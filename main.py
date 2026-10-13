"""
main.py
--------
End-to-end product analytics pipeline on the Cookie Cats A/B test:

  1. Load and clean data, engineer funnel milestones
  2. Funnel drop-off analysis by version
  3. Primary metric tests: frequentist (z-test + Mann-Whitney guardrail),
     Bayesian (beta-binomial), and bootstrap cross-check
  4. Heterogeneous treatment effect by engagement segment
  5. Power analysis (MDE at current sample size, required N for smaller effects)
  6. Sequential-peeking risk simulation
  7. RICE-scored product decision roadmap
  8. Save all figures and result tables

Run with: python main.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from src.data_prep import load_and_clean, dataset_summary
from src.funnel import funnel_by_version, gate_specific_dropoff
from src.ab_test import two_proportion_z_test, mann_whitney_guardrail_test, bayesian_beta_binomial, bootstrap_retention_diff
from src.segments import segment_treatment_effects
from src.peeking_risk import simulate_peeking_inflation
from src.decision import run_power_analysis, build_rice_roadmap
from src.visualize import (
    funnel_plot, retention_comparison_plot, bayesian_posterior_plot,
    segment_effect_plot, peeking_risk_plot,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 70)
    print("PRODUCT ANALYTICS: COOKIE CATS GATE PLACEMENT A/B TEST")
    print("=" * 70)

    # 1. Load data --------------------------------------------------------
    df = load_and_clean()
    summary = dataset_summary(df)
    print("\n[1/8] Data loaded.")
    for k, v in summary.items():
        print(f"      {k}: {v}")

    # 2. Funnel -------------------------------------------------------------
    print("\n[2/8] Building engagement funnel...")
    funnel_df = funnel_by_version(df)
    gate_dropoff_df = gate_specific_dropoff(df)
    print(gate_dropoff_df.to_string(index=False))

    # 3. Primary + guardrail tests ------------------------------------------
    print("\n[3/8] Running frequentist tests (Day-1, Day-7 retention)...")
    test_d1 = two_proportion_z_test(df, "retention_1")
    test_d7 = two_proportion_z_test(df, "retention_7")
    for t in (test_d1, test_d7):
        print(f"      {t.metric}: control={t.rate_control}% treatment={t.rate_treatment}% "
              f"diff={t.absolute_diff}pp (95% CI [{t.ci_95_diff_low}, {t.ci_95_diff_high}]) p={t.p_value}")

    guardrail = mann_whitney_guardrail_test(df)
    print(f"      guardrail (sum_gamerounds): median control={guardrail.median_control}, "
          f"median treatment={guardrail.median_treatment}, p={guardrail.p_value:.4f}")

    print("\n      Bayesian analysis:")
    bayes_d1 = bayesian_beta_binomial(df, "retention_1")
    bayes_d7 = bayesian_beta_binomial(df, "retention_7")
    for b in (bayes_d1, bayes_d7):
        print(f"      {b.metric}: P(gate_30 > gate_40) = {b.prob_control_better:.1%}, "
              f"posterior mean diff = {b.posterior_diff_mean}pp, 95% CI {b.posterior_diff_ci_95}")

    print("\n      Bootstrap cross-check (Day-7 retention):")
    boot = bootstrap_retention_diff(df, "retention_7", n_boot=5000)
    print(f"      {boot}")

    # 4. Segment analysis -----------------------------------------------
    print("\n[4/8] Heterogeneous treatment effect by engagement segment...")
    segment_df = segment_treatment_effects(df, "retention_7")
    print(segment_df.to_string(index=False))

    # 5. Power analysis ---------------------------------------------------
    print("\n[5/8] Power analysis...")
    power = run_power_analysis(baseline_rate=test_d7.rate_control / 100, n_per_group_observed=test_d7.n_control)
    print(f"      At n={power.n_per_group_observed}/group, minimum detectable effect = "
          f"{power.mde_detectable_at_observed_n_pct_pts}pp")
    print(f"      To detect a 1pp difference reliably would require "
          f"{power.n_required_for_1pp_mde_per_group:,} users/group")

    # 6. Peeking risk simulation ---------------------------------------
    print("\n[6/8] Simulating sequential-peeking false-positive inflation...")
    peeking = simulate_peeking_inflation(df, metric="retention_1", n_simulations=2000)
    print(f"      {peeking}")

    # 7. RICE roadmap -----------------------------------------------------
    print("\n[7/8] Building RICE-scored product roadmap...")
    rice_items = build_rice_roadmap()
    rice_items_sorted = sorted(rice_items, key=lambda x: -x.score)
    for item in rice_items_sorted:
        print(f"      [{item.score:>6.1f}] {item.action}")

    # 8. Save outputs -------------------------------------------------------
    print("\n[8/8] Saving figures and result tables...")
    funnel_plot(funnel_df)
    retention_comparison_plot([test_d1, test_d7])
    bayesian_posterior_plot(df, "retention_7")
    segment_effect_plot(segment_df)
    peeking_risk_plot(peeking)

    funnel_df.to_csv(OUTPUT_DIR / "funnel_by_version.csv", index=False)
    gate_dropoff_df.to_csv(OUTPUT_DIR / "gate_specific_dropoff.csv", index=False)
    segment_df.to_csv(OUTPUT_DIR / "segment_treatment_effects.csv", index=False)

    result_summary = {
        "dataset": summary,
        "primary_tests": {
            "retention_1": vars(test_d1),
            "retention_7": vars(test_d7),
        },
        "guardrail_test_sum_gamerounds": vars(guardrail),
        "bayesian": {
            "retention_1": vars(bayes_d1),
            "retention_7": vars(bayes_d7),
        },
        "bootstrap_retention_7": boot,
        "power_analysis": vars(power),
        "peeking_risk_simulation": peeking,
        "rice_roadmap": [
            {"action": i.action, "reach": i.reach, "impact": i.impact,
             "confidence": i.confidence, "effort": i.effort, "rice_score": i.score}
            for i in rice_items_sorted
        ],
    }
    with open(OUTPUT_DIR / "summary_metrics.json", "w") as f:
        json.dump(result_summary, f, indent=2, default=str)

    print("      Done. See outputs/figures/ and outputs/results/.")
    print("=" * 70)
    return result_summary


if __name__ == "__main__":
    start_time = time.perf_counter()
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: Pipeline failed -- {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        elapsed = time.perf_counter() - start_time
        print(f"Total pipeline time: {elapsed:.2f}s")
