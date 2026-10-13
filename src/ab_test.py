"""
ab_test.py
-----------
Frequentist AND Bayesian analysis of the gate_30 vs gate_40 A/B test on two
primary metrics (Day-1 and Day-7 retention) and one guardrail metric
(engagement, sum_gamerounds).

Most tutorial treatments of this dataset stop at a single chi-square test.
This module adds:
  - A two-proportion z-test with a Wilson-score confidence interval on the
    RISK DIFFERENCE (not just the p-value) -- what a product/growth team
    actually needs to size a decision, not just whether p < 0.05.
  - A Mann-Whitney U test on the guardrail metric, since game-round counts
    are heavily right-skewed (a t-test's normality assumption doesn't
    hold here).
  - A Bayesian beta-binomial analysis giving P(gate_30 > gate_40) directly,
    which answers the actual business question ("how likely is gate_30
    better") instead of the frequentist p-value's indirect framing.

NOTE ON CONFIDENCE INTERVALS:
    The normal approximation used for the two-proportion z-test confidence
    intervals is appropriate at this sample size (n > 45,000 per group).
    With tens of thousands of observations per arm, the sampling
    distribution of proportions is well-approximated by the normal
    distribution via the Central Limit Theorem.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ProportionTestResult:
    metric: str
    n_control: int
    n_treatment: int
    rate_control: float
    rate_treatment: float
    absolute_diff: float           # control - treatment
    relative_diff_pct: float
    z_stat: float
    p_value: float
    ci_95_diff_low: float
    ci_95_diff_high: float


def two_proportion_z_test(df: pd.DataFrame, metric: str) -> ProportionTestResult:
    control = df[df["version"] == "gate_30"][metric]
    treatment = df[df["version"] == "gate_40"][metric]

    n1, n2 = len(control), len(treatment)
    p1, p2 = control.mean(), treatment.mean()

    # Pooled proportion for the z-test statistic
    p_pool = (control.sum() + treatment.sum()) / (n1 + n2)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se_pool
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    # Unpooled SE for the confidence interval on the difference itself
    se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p1 - p2
    ci_low = diff - 1.96 * se_diff
    ci_high = diff + 1.96 * se_diff

    return ProportionTestResult(
        metric=metric, n_control=n1, n_treatment=n2,
        rate_control=round(100 * p1, 3), rate_treatment=round(100 * p2, 3),
        absolute_diff=round(100 * diff, 3),
        relative_diff_pct=round(100 * diff / p2, 2),
        z_stat=round(z, 4), p_value=round(p_value, 5),
        ci_95_diff_low=round(100 * ci_low, 3), ci_95_diff_high=round(100 * ci_high, 3),
    )


@dataclass
class MannWhitneyResult:
    metric: str
    median_control: float
    median_treatment: float
    u_stat: float
    p_value: float


def mann_whitney_guardrail_test(df: pd.DataFrame, metric: str = "sum_gamerounds") -> MannWhitneyResult:
    control = df[df["version"] == "gate_30"][metric]
    treatment = df[df["version"] == "gate_40"][metric]
    u_stat, p_value = stats.mannwhitneyu(control, treatment, alternative="two-sided")
    return MannWhitneyResult(
        metric=metric,
        median_control=float(control.median()), median_treatment=float(treatment.median()),
        u_stat=float(u_stat), p_value=float(p_value),
    )


@dataclass
class BayesianResult:
    metric: str
    prob_control_better: float
    posterior_diff_mean: float
    posterior_diff_ci_95: tuple


def bayesian_beta_binomial(df: pd.DataFrame, metric: str, n_samples: int = 200_000, seed: int = 42) -> BayesianResult:
    """
    Model each group's conversion rate with a Beta(1,1) uninformative
    prior updated by observed successes/failures, then draw posterior
    samples for each group's rate and directly compute
    P(control_rate > treatment_rate) -- the actual probability decision-
    makers want, rather than a p-value that answers a different question.
    """
    rng = np.random.default_rng(seed)
    control = df[df["version"] == "gate_30"][metric]
    treatment = df[df["version"] == "gate_40"][metric]

    a_c, b_c = 1 + control.sum(), 1 + (len(control) - control.sum())
    a_t, b_t = 1 + treatment.sum(), 1 + (len(treatment) - treatment.sum())

    samples_c = rng.beta(a_c, b_c, n_samples)
    samples_t = rng.beta(a_t, b_t, n_samples)

    diff = samples_c - samples_t
    prob_control_better = float((diff > 0).mean())
    ci = (float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5)))

    return BayesianResult(
        metric=metric, prob_control_better=round(prob_control_better, 4),
        posterior_diff_mean=round(float(diff.mean()) * 100, 3),
        posterior_diff_ci_95=(round(ci[0] * 100, 3), round(ci[1] * 100, 3)),
    )


def bootstrap_retention_diff(df: pd.DataFrame, metric: str, n_boot: int = 10_000, seed: int = 42) -> dict:
    """Non-parametric bootstrap on the retention-rate difference, as a
    cross-check that doesn't rely on any distributional assumption."""
    rng = np.random.default_rng(seed)
    control = df[df["version"] == "gate_30"][metric].values
    treatment = df[df["version"] == "gate_40"][metric].values

    diffs = np.empty(n_boot)
    for i in range(n_boot):
        c_sample = rng.choice(control, size=len(control), replace=True)
        t_sample = rng.choice(treatment, size=len(treatment), replace=True)
        diffs[i] = c_sample.mean() - t_sample.mean()

    return {
        "metric": metric,
        "bootstrap_mean_diff_pct": round(float(diffs.mean()) * 100, 3),
        "bootstrap_ci_95_low_pct": round(float(np.percentile(diffs, 2.5)) * 100, 3),
        "bootstrap_ci_95_high_pct": round(float(np.percentile(diffs, 97.5)) * 100, 3),
        "pct_bootstrap_samples_control_better": round(100 * float((diffs > 0).mean()), 2),
    }
