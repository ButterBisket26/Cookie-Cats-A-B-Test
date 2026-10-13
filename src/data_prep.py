"""
data_prep.py
------------
Loads the Cookie Cats mobile game A/B test dataset (90,189 real players,
Tactile Entertainment). The experiment: the first progression "gate" that
forces players to wait or pay to continue was moved from level 30 to level
40. Every player was randomly assigned to gate_30 (control) or gate_40
(treatment) at install time.

This module also engineers FUNNEL MILESTONES from sum_gamerounds -- rather
than treating engagement as a single number, we treat it as a progression
funnel (played >=1 round -> reached the old gate at 30 -> reached the new
gate at 40 -> reached round 100) so drop-off can be analyzed stage by
stage, the way a product analyst would look at an onboarding funnel.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "cookie_cats.csv"

FUNNEL_MILESTONES = [1, 10, 30, 40, 50, 100]


def load_and_clean(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the raw CSV, flag extreme outliers, cast retention columns to
    bool, and engineer boolean milestone columns for the engagement funnel.

    Outlier handling: a single known extreme value (one user logged 49,854
    game rounds -- more than 3,500 rounds/day sustained, almost certainly a
    bot/QA account) is documented in the original analysis.  Rather than
    silently dropping it, the row is flagged via ``is_extreme_outlier`` so
    the effect of excluding it is auditable.
    """
    df = pd.read_csv(path)

    # Flag extreme outlier (auditable, not silently dropped)
    df["is_extreme_outlier"] = df["sum_gamerounds"] > df["sum_gamerounds"].quantile(0.9999)

    df["retention_1"] = df["retention_1"].astype(bool)
    df["retention_7"] = df["retention_7"].astype(bool)

    for m in FUNNEL_MILESTONES:
        df[f"reached_{m}"] = df["sum_gamerounds"] >= m

    return df


def dataset_summary(df: pd.DataFrame) -> dict[str, object]:
    """Return a high-level summary dictionary of the dataset suitable for
    logging or serialization."""
    return {
        "n_players": len(df),
        "n_control_gate30": int((df["version"] == "gate_30").sum()),
        "n_treatment_gate40": int((df["version"] == "gate_40").sum()),
        "overall_day1_retention_pct": round(100 * df["retention_1"].mean(), 2),
        "overall_day7_retention_pct": round(100 * df["retention_7"].mean(), 2),
        "median_gamerounds": float(df["sum_gamerounds"].median()),
        "n_zero_rounds_players": int((df["sum_gamerounds"] == 0).sum()),
        "n_extreme_outliers_flagged": int(df["is_extreme_outlier"].sum()),
    }


if __name__ == "__main__":
    df = load_and_clean()
    for k, v in dataset_summary(df).items():
        print(f"{k}: {v}")
