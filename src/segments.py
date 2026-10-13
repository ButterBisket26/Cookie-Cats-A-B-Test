"""
segments.py
------------
Heterogeneous treatment effect analysis: does moving the gate from 30 to 40
affect casual players and engaged players differently?

The average effect can hide a business-critical split: a change might be
neutral-to-positive for casual players but actively harmful for the
engaged players who matter most to long-term revenue. This is the standard
follow-up question after any average-effect A/B test result, and it's
what separates "the test was flat, ship it" from a defensible product
recommendation.

Segment definition: players are split by whether they reached round 20
(a milestone BEFORE either gate, so it is not itself affected by the
treatment) into "Casual" (<20 rounds) and "Engaged" (>=20 rounds) --
this avoids conditioning on a post-treatment-affected variable like the
gate milestones themselves, which would bias the comparison.

NOTE ON POST-TREATMENT BIAS AVOIDANCE:
    Selecting a segmentation threshold that falls after the treatment
    would introduce post-treatment bias: the gate placement itself affects
    how many rounds a player completes, so conditioning on a post-gate
    milestone would confound the treatment effect. Round 20 is chosen
    precisely because it is BEFORE both gates (30 and 40), making it a
    clean pre-treatment proxy for player engagement.
"""
from __future__ import annotations

import pandas as pd

from src.ab_test import two_proportion_z_test, bayesian_beta_binomial


def add_engagement_segment(df: pd.DataFrame, threshold: int = 20) -> pd.DataFrame:
    """Classify each player as 'Casual' or 'Engaged' based on whether they
    reached the pre-treatment milestone *threshold* (default 20 rounds).

    If a pre-computed ``reached_<threshold>`` column exists, it is used;
    otherwise the segment is derived directly from ``sum_gamerounds``.

    The returned DataFrame gets an ``engagement_segment`` column with two
    levels: ``'Engaged (>=20 rounds pre-gate)'`` and
    ``'Casual (<20 rounds)'``.
    """
    df = df.copy()
    reached_col = f"reached_{threshold}"
    if reached_col in df.columns:
        df["engagement_segment"] = df[reached_col]
    else:
        df["engagement_segment"] = df["sum_gamerounds"] >= threshold
    df["engagement_segment"] = df["engagement_segment"].map(
        {True: "Engaged (>=20 rounds pre-gate)", False: "Casual (<20 rounds)"}
    )
    return df


def segment_treatment_effects(df: pd.DataFrame, metric: str = "retention_7") -> pd.DataFrame:
    """Compute frequentist and Bayesian treatment effects separately for
    each engagement segment.

    Returns a DataFrame with one row per segment containing sample sizes,
    retention rates for control and treatment, absolute difference, p-value,
    and the Bayesian posterior probability that control is better.
    """
    df = add_engagement_segment(df)
    rows: list[dict[str, object]] = []
    for segment, sub in df.groupby("engagement_segment"):
        test = two_proportion_z_test(sub, metric)
        bayes = bayesian_beta_binomial(sub, metric)
        rows.append({
            "segment": segment,
            "n_control": test.n_control,
            "n_treatment": test.n_treatment,
            "rate_control_pct": test.rate_control,
            "rate_treatment_pct": test.rate_treatment,
            "absolute_diff_pct_pts": test.absolute_diff,
            "p_value": test.p_value,
            "bayesian_prob_control_better": bayes.prob_control_better,
        })
    return pd.DataFrame(rows)
