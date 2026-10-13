"""
funnel.py
----------
Product funnel analysis: for each engagement milestone (played >=1 round,
reached round 10, reached the old gate at 30, reached the new gate at 40,
reached round 50, reached round 100), compute the share of players in each
A/B group who got that far, and the stage-to-stage drop-off rate.

This reframes "sum_gamerounds" -- a single aggregate number -- as a funnel,
which is the standard lens a product analyst uses to find exactly where
users disengage, rather than just reporting an average.
"""
from __future__ import annotations

import pandas as pd

from src.data_prep import FUNNEL_MILESTONES


def funnel_by_version(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the engagement funnel (cumulative reach % at each milestone)
    for each A/B test version, along with stage-to-stage drop-off."""
    rows = []
    for version, group in df.groupby("version"):
        n_total = len(group)
        prev_pct = 100.0
        for m in FUNNEL_MILESTONES:
            n_reached = int(group[f"reached_{m}"].sum())
            pct_reached = 100 * n_reached / n_total
            rows.append({
                "version": version,
                "milestone": f"Round {m}",
                "n_reached": n_reached,
                "pct_of_group_reached": round(pct_reached, 2),
                "drop_off_from_prev_stage_pct": round(prev_pct - pct_reached, 2),
            })
            prev_pct = pct_reached
    return pd.DataFrame(rows)


def gate_specific_dropoff(df: pd.DataFrame) -> pd.DataFrame:
    """
    The business-critical comparison: among players who actually reached
    their assigned gate (30 for control, 40 for treatment), what fraction
    dropped off in the 10 rounds immediately after the gate -- i.e. does a
    later gate cause MORE frustration-driven churn right after it, even
    among engaged players who got that far?

    IMPORTANT APPROXIMATION NOTE:
        Since we only have cumulative sum_gamerounds (not day-by-day
        timestamps), "churned within 10 rounds after the gate" is
        approximated as "reached gate level but did not reach gate+10."
        This is a conservative estimate -- it captures all players who
        never made it 10 rounds past the gate, but cannot distinguish
        players who churned immediately from those who played 9 more
        rounds and then stopped.
    """
    results = []
    # Control: gate at 30, "just after" = reached 30 but not 40 => churned
    # in the 10-round window right after hitting the gate.
    control = df[df["version"] == "gate_30"]
    reached_30 = control[control["reached_30"]]
    churned_soon_after = reached_30[~reached_30["reached_40"]]
    results.append({
        "version": "gate_30", "gate_level": 30,
        "n_reached_gate": len(reached_30),
        "n_churned_within_10_rounds_after_gate": len(churned_soon_after),
        "pct_churned_within_10_rounds_after_gate": round(100 * len(churned_soon_after) / len(reached_30), 2),
    })

    # Treatment: gate at 40, "just after" = reached 40 but not 50.
    treatment = df[df["version"] == "gate_40"]
    reached_40 = treatment[treatment["reached_40"]]
    churned_soon_after_t = reached_40[~reached_40["reached_50"]]
    results.append({
        "version": "gate_40", "gate_level": 40,
        "n_reached_gate": len(reached_40),
        "n_churned_within_10_rounds_after_gate": len(churned_soon_after_t),
        "pct_churned_within_10_rounds_after_gate": round(100 * len(churned_soon_after_t) / len(reached_40), 2),
    })
    return pd.DataFrame(results)
