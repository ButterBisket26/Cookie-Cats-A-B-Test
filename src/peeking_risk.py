"""
peeking_risk.py
-----------------
Simulates a common real-world mistake: checking an A/B test's p-value
every day and stopping as soon as it crosses 0.05 ("peeking"). This
inflates the false-positive rate far above the nominal 5% -- a well-known
but frequently ignored problem in applied A/B testing.

This module replays the ACTUAL experiment data in daily-cumulative slices
(approximated by revealing the dataset in random daily batches, since we
only have the 14-day endpoint, not literal day-by-day timestamps) and
checks how many of the 14 "look points" would have crossed p < 0.05 by
chance if the two groups had no real difference -- estimated via a
permutation null. This is the kind of check that signals real statistical
maturity in an interview: understanding why "the test hit significance on
day 3, so we shipped it" is a methodological error even when the final
p-value looks fine.

LIMITATION:
    Since the dataset only provides a 14-day cumulative sum rather than
    daily timestamps, daily slices are approximated by dividing the
    dataset into equal-size batches in random order. This is a standard
    approach when daily data is unavailable, but should be noted as an
    approximation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def simulate_peeking_inflation(
    df: pd.DataFrame,
    metric: str = "retention_1",
    n_looks: int = 14,
    n_simulations: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """
    Under the NULL (no true difference -- simulated by randomly reshuffling
    the version label so any observed difference is pure chance), estimate
    the probability that at least one of `n_looks` sequential peeks at the
    cumulative data would show p < alpha, versus the nominal single-look
    false positive rate of exactly `alpha`.

    Vectorized via cumulative sums (O(n) per simulation) rather than
    re-slicing the full array at every look, so this runs in seconds
    instead of hours at n=90,189.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    values = df[metric].values.astype(float)
    version = df["version"].values

    false_positive_any_look = 0
    look_cutoffs = np.array([int(n * look / n_looks) for look in range(1, n_looks + 1)])

    for _ in range(n_simulations):
        shuffled_version = rng.permutation(version)
        order = rng.permutation(n)

        vals_ordered = values[order]
        is_control_ordered = (shuffled_version[order] == "gate_30")

        control_val_cum = np.cumsum(np.where(is_control_ordered, vals_ordered, 0.0))
        control_n_cum = np.cumsum(is_control_ordered)
        total_val_cum = np.cumsum(vals_ordered)
        total_n_cum = np.arange(1, n + 1)

        treat_val_cum = total_val_cum - control_val_cum
        treat_n_cum = total_n_cum - control_n_cum

        found_significant = False
        for cutoff in look_cutoffs:
            idx = cutoff - 1
            n1, n2 = control_n_cum[idx], treat_n_cum[idx]
            if n1 < 30 or n2 < 30:
                continue
            p1 = control_val_cum[idx] / n1
            p2 = treat_val_cum[idx] / n2
            p_pool = total_val_cum[idx] / total_n_cum[idx]
            se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
            if se == 0:
                continue
            z = (p1 - p2) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))
            if p_value < alpha:
                found_significant = True
                break
        if found_significant:
            false_positive_any_look += 1

    inflated_fp_rate = false_positive_any_look / n_simulations

    return {
        "metric": metric,
        "n_looks_simulated": n_looks,
        "nominal_single_look_alpha": alpha,
        "simulated_false_positive_rate_with_peeking": round(inflated_fp_rate, 4),
        "inflation_factor": round(inflated_fp_rate / alpha, 2),
        "n_simulations": n_simulations,
    }
