# Product Analytics: A/B Test Deep-Dive on a Real Mobile Game

### Funnel Analysis · Frequentist & Bayesian Testing · Heterogeneous Effects · RICE-Scored Decision

> **Bottom line:** Moving Cookie Cats' first progression gate from level 30 to level 40 **hurts Day-7 retention by 0.82 percentage points** (19.02% → 18.20%). This effect is confirmed by three independent statistical methods (p = 0.0015, Bayesian P(control better) = 99.9%, bootstrap 99.96%), is concentrated among engaged players — the highest-value segment — and is not offset by any increase in engagement. **Recommendation: do not ship gate_40.**

---

## Why this project exists

Most A/B test portfolio pieces stop at "here's the p-value, ship or don't." Real product analytics requires turning a raw experiment result into a **defensible product decision** — including the parts most tutorials skip:

- Does the effect hold up across **multiple statistical methods**, not just one?
- Is the average effect **hiding a harmful subgroup effect** the average masks?
- Was the test **adequately powered** to trust a "no effect" reading?
- Was the result obtained **without the most common methodological error** in applied testing — checking the dashboard daily and shipping on the first p < 0.05?

This project answers all four.

---

## The Experiment

| | Control | Treatment |
|---|---|---|
| **Group** | gate_30 | gate_40 |
| **Gate placement** | Level 30 | Level 40 |
| **Players** | 44,700 | 45,489 |
| **Day-1 retention** | 44.82% | 44.23% |
| **Day-7 retention** | **19.02%** | **18.20%** |
| **Median game rounds** | 17 | 16 |

Cookie Cats is a mobile puzzle game by Tactile Entertainment. Players were randomly assigned at install time to one of two versions: the first progression "gate" (forcing a wait or in-app purchase) at level 30 or level 40. This is **genuinely randomized experimental data from a real product decision** — 90,189 real players — not a simulation.

---

## Headline Results

### 1. Day-7 Retention: gate_30 is Better — Confirmed by Three Independent Methods

| Method | Finding | Confidence |
|---|---|---|
| Frequentist z-test | 0.82pp difference | p = 0.0015 |
| Bayesian beta-binomial | Posterior diff = 0.82pp | P(gate_30 better) = 99.9% |
| Bootstrap (5,000 resamples) | Mean diff = 0.83pp | 99.96% of resamples favor gate_30 |

> **The 95% confidence interval on the Day-7 retention difference is [0.31pp, 1.33pp].** Even at the lower bound, the effect is practically meaningful at scale.

### 2. The Damage Is Concentrated Among Engaged Players

| Segment | gate_30 | gate_40 | Difference | p-value |
|---|---|---|---|---|
| **Engaged** (≥20 rounds pre-gate) | 37.25% | 36.28% | **−0.97pp** | **0.041** |
| Casual (<20 rounds) | 3.02% | 2.90% | −0.12pp | 0.454 |

> Engaged players — those most likely to become long-term, high-value, paying users — bear the entire retention cost. Casual players show no measurable effect. **A pure average analysis would have missed this.**

### 3. Engagement Did Not Improve

The Mann-Whitney U test on `sum_gamerounds` (guardrail metric) shows **no meaningful difference** in total engagement between groups (p = 0.05, median rounds 17 vs 16). The later gate isn't trading engagement for retention — it's just costing retention.

### 4. The Test Was Adequately Powered

| Metric | Value |
|---|---|
| Minimum detectable effect at current N | 0.735pp |
| N required to detect a 1pp difference | 24,179 per group |

At 44,700+ players per group, the test could reliably detect effects ≥ 0.735pp. The observed 0.82pp effect **exceeds this threshold** — this is not a borderline finding.

### 5. Peeking at Results Daily Would Have Inflated False Positives 4.4x

| Scenario | False-positive rate |
|---|---|
| Single planned look | 5.0% (nominal) |
| Checking daily for 14 days | **22.1%** (simulated) |

> Simulated via 2,000 permutation-null replays. If the team had checked the dashboard daily and shipped the moment p < 0.05, the chance of a false "it's working" signal would have been **4.42x higher** than the intended 5%.

---

## How This Project Goes Beyond Standard A/B Test Analyses

| Standard tutorial approach | This project |
|---|---|
| One chi-square test on Day-1 retention | Frequentist z-tests + Bayesian beta-binomial + bootstrap cross-check on both Day-1 and Day-7, plus Mann-Whitney guardrail |
| Reports the average treatment effect | Decomposes by **engagement segment** — reveals the effect is concentrated among engaged players and hidden by casual players |
| Treats `sum_gamerounds` as one number | Reframes it as a **funnel** — drop-off at each milestone, and churn rate in the 10 rounds immediately after each group's gate |
| Stops at "p < 0.05" | Runs **power analysis** (what effect size is detectable at this N) and **peeking-risk simulation** (quantifying false-positive inflation from daily checking) |
| Ends with a one-line conclusion | Ends with a **RICE-scored roadmap** — the actual product-decision artifact a team would act on |

---

## Repository Structure

```
product-analytics-project/
├── README.md                              <- you are here
├── PROBLEM_STATEMENT.md                   <- business context, analytical questions, methodology
├── requirements.txt                       <- pinned dependencies
├── LICENSE                                <- MIT
├── main.py                                <- single-command end-to-end pipeline
├── data/
│   └── cookie_cats.csv                    <- 90,189 real players
├── src/
│   ├── __init__.py
│   ├── data_prep.py                       <- cleaning, funnel milestone engineering
│   ├── funnel.py                          <- engagement funnel, gate-specific churn
│   ├── ab_test.py                         <- z-test, Mann-Whitney, Bayesian, bootstrap
│   ├── segments.py                        <- heterogeneous treatment effect analysis
│   ├── peeking_risk.py                    <- sequential-testing false-positive simulation
│   ├── decision.py                        <- power analysis + RICE roadmap
│   └── visualize.py                       <- 5 chart exhibits
└── outputs/
    ├── figures/
    │   ├── 01_funnel.png
    │   ├── 02_retention_comparison.png
    │   ├── 03_bayesian_posterior.png
    │   ├── 04_segment_effects.png
    │   └── 05_peeking_risk.png
    └── results/
        ├── funnel_by_version.csv
        ├── gate_specific_dropoff.csv
        ├── segment_treatment_effects.csv
        ├── summary_metrics.json           <- all statistics, machine-readable
        └── business_report.md             <- plain-language findings for stakeholders
```

---

## How to Run

```bash
# Clone the repository
git clone https://github.com/saivignesh21/Cookie-Cats-A-B-Test-.git
cd Cookie-Cats-A-B-Test-

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python main.py
```

**Runtime:** ~30 seconds (the peeking-risk simulation is the slowest step — 2,000 permutation-null replays).

---

## Key Outputs

### Figures

| # | Exhibit | What it shows |
|---|---|---|
| 1 | **Engagement Funnel** | Stage-by-stage drop-off for both groups across milestones |
| 2 | **Retention Comparison** | Day-1 and Day-7 retention with p-values and confidence intervals |
| 3 | **Bayesian Posterior** | Full posterior distributions — almost complete separation on Day-7 |
| 4 | **Segment Effects** | Heterogeneous treatment effect by engagement level |
| 5 | **Peeking Risk** | False-positive inflation from daily sequential checking |

### Machine-Readable Results

`outputs/results/summary_metrics.json` contains every statistic from every method — z-statistics, p-values, Bayesian posteriors, bootstrap CIs, power analysis metrics, and the RICE roadmap — in a single JSON file ready for downstream consumption.

---

## Skills Demonstrated

| Category | Specifics |
|---|---|
| **Statistical Testing** | Two-proportion z-tests, Mann-Whitney U (skewed guardrail), Bayesian beta-binomial inference, bootstrap resampling |
| **Experiment Design** | Power analysis, minimum detectable effect, sequential-testing risk quantification |
| **Product Analytics** | Funnel decomposition, heterogeneous treatment effects, guardrail metrics |
| **Decision Framework** | RICE-scored product roadmap converting statistical findings to actionable priorities |
| **Communication** | Plain-language business report for non-technical stakeholders |
| **Code Quality** | Modular pipeline, typed dataclasses, reusable across any binary-outcome A/B test |

---

## Methodology Notes

- **Outlier handling:** One extreme outlier (49,854 game rounds, ~3,500/day — almost certainly a bot/QA account) is flagged but **not removed**, so its effect is auditable rather than hidden.
- **Segment definition:** Players are split at 20 rounds (a pre-gate milestone) to avoid **post-treatment conditioning bias** — both gates are at 30+, so no player's segment assignment is affected by treatment.
- **Gate-specific churn:** Approximated as "reached gate level but not gate+10" since only cumulative `sum_gamerounds` is available (not day-by-day timestamps).
- **Peeking simulation:** Uses permutation null with cumulative sums for efficiency. Daily slices are approximated as equal-size batches — a standard approach when daily timestamps are unavailable.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
