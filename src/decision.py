"""
decision.py
------------
Two things a product analyst delivers that a pure statistics writeup
doesn't: (1) a minimum detectable effect / required sample size
calculation -- so the team knows what future tests can and can't detect
at this traffic level -- and (2) a RICE-scored recommendation converting
the statistical findings into a ranked set of product actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil

import numpy as np
from scipy import stats


@dataclass
class PowerAnalysisResult:
    baseline_rate: float
    n_per_group_observed: int
    mde_detectable_at_observed_n_pct_pts: float
    n_required_for_1pp_mde_per_group: int


def minimum_detectable_effect(baseline_rate: float, n_per_group: int, power: float = 0.8, alpha: float = 0.05) -> float:
    """Smallest absolute rate difference (in percentage points) detectable
    with the given sample size at the given power and significance level."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    p = baseline_rate
    se_component = np.sqrt(2 * p * (1 - p))
    mde = (z_alpha + z_beta) * se_component / np.sqrt(n_per_group)
    return round(mde * 100, 3)


def required_sample_size(baseline_rate: float, mde_pct_pts: float, power: float = 0.8, alpha: float = 0.05) -> int:
    """Required N per group to detect a given absolute effect size."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    p = baseline_rate
    mde = mde_pct_pts / 100
    n = ((z_alpha + z_beta) ** 2) * 2 * p * (1 - p) / (mde ** 2)
    return ceil(n)


def run_power_analysis(baseline_rate: float, n_per_group_observed: int) -> PowerAnalysisResult:
    mde_at_n = minimum_detectable_effect(baseline_rate, n_per_group_observed)
    n_for_1pp = required_sample_size(baseline_rate, 1.0)
    return PowerAnalysisResult(
        baseline_rate=round(baseline_rate * 100, 2),
        n_per_group_observed=n_per_group_observed,
        mde_detectable_at_observed_n_pct_pts=mde_at_n,
        n_required_for_1pp_mde_per_group=n_for_1pp,
    )


@dataclass
class RiceItem:
    action: str
    reach: int      # 1-10, share of user base affected
    impact: int      # 1-10
    confidence: int  # 1-10, statistical confidence in the underlying finding
    effort: int      # 1-10, engineering/design effort (lower = less effort)

    @property
    def score(self) -> float:
        return round((self.reach * self.impact * self.confidence) / self.effort, 1)


def build_rice_roadmap() -> list[RiceItem]:
    """
    RICE-scored product actions derived directly from the statistical
    findings -- reach and confidence are grounded in the actual test
    results (e.g., confidence is high for the primary retention finding,
    which crossed both frequentist and Bayesian thresholds; lower for the
    engaged-segment finding, which had a smaller sample and wider CI).

    Scoring methodology: RICE = (Reach x Impact x Confidence) / Effort.
    Each factor is rated 1-10.  Reach captures the fraction of users
    affected; Impact estimates the business effect magnitude; Confidence
    reflects certainty in the underlying statistical finding; Effort is
    the estimated engineering/design cost (higher = more work).  Items
    are ranked by descending score to prioritise high-impact, high-
    confidence, low-effort actions.
    """
    return [
        RiceItem("Keep the gate at level 30 (do not ship gate_40)", reach=10, impact=8, confidence=9, effort=1),
        RiceItem("Investigate post-gate-30 drop-off with an in-game reward/nudge", reach=8, impact=7, confidence=5, effort=5),
        RiceItem("Run a follow-up test on engaged-segment-specific gate placement", reach=4, impact=6, confidence=4, effort=4),
        RiceItem("Instrument daily-level event logging to prevent future peeking risk", reach=10, impact=5, confidence=8, effort=3),
    ]
