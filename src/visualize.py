"""
visualize.py
-------------
Produces the exhibits: funnel drop-off by version, retention comparison
with CIs, Bayesian posterior distributions, heterogeneous treatment effect
by segment, and the peeking-risk inflation chart.
"""
from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (9, 5.5), "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "font.size": 11,
})
COLORS = {"gate_30": "#2c3e50", "gate_40": "#c0392b"}


def funnel_plot(funnel_df: pd.DataFrame):
    fig, ax = plt.subplots()
    for version, sub in funnel_df.groupby("version"):
        ax.plot(sub["milestone"], sub["pct_of_group_reached"], marker="o",
                label=version, color=COLORS.get(version), linewidth=2.2)
    ax.set_ylabel("% of group reaching milestone")
    ax.set_xlabel("Engagement milestone")
    ax.set_title("Engagement Funnel: Gate 30 vs. Gate 40")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_funnel.png", dpi=200)
    plt.close(fig)


def retention_comparison_plot(retention_tests: list):
    fig, axes = plt.subplots(1, len(retention_tests), figsize=(5 * len(retention_tests), 5))
    if len(retention_tests) == 1:
        axes = [axes]
    for ax, test in zip(axes, retention_tests):
        vals = [test.rate_control, test.rate_treatment]
        colors = [COLORS["gate_30"], COLORS["gate_40"]]
        bars = ax.bar(["gate_30 (control)", "gate_40 (treatment)"], vals, color=colors)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.3, f"{v:.2f}%", ha="center", fontsize=10)
        ax.set_title(f"{test.metric}  (p = {test.p_value:.4f})")
        ax.set_ylabel("Retention rate (%)")
        ax.set_ylim(0, max(vals) * 1.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_retention_comparison.png", dpi=200)
    plt.close(fig)


def bayesian_posterior_plot(df, metric: str, n_samples: int = 200_000, seed: int = 42):
    rng = np.random.default_rng(seed)
    control = df[df["version"] == "gate_30"][metric]
    treatment = df[df["version"] == "gate_40"][metric]
    a_c, b_c = 1 + control.sum(), 1 + (len(control) - control.sum())
    a_t, b_t = 1 + treatment.sum(), 1 + (len(treatment) - treatment.sum())
    samples_c = rng.beta(a_c, b_c, n_samples)
    samples_t = rng.beta(a_t, b_t, n_samples)

    fig, ax = plt.subplots()
    ax.hist(samples_c * 100, bins=200, alpha=0.6, color=COLORS["gate_30"], label="gate_30 (control)", density=True)
    ax.hist(samples_t * 100, bins=200, alpha=0.6, color=COLORS["gate_40"], label="gate_40 (treatment)", density=True)
    ax.set_xlim(np.percentile(np.concatenate([samples_c, samples_t]) * 100, [0.1, 99.9]))
    ax.set_xlabel(f"Posterior {metric} rate (%)")
    ax.set_ylabel("Density")
    ax.set_title(f"Bayesian Posterior Distributions: {metric}")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_bayesian_posterior.png", dpi=200)
    plt.close(fig)


def segment_effect_plot(segment_df: pd.DataFrame):
    fig, ax = plt.subplots()
    x = np.arange(len(segment_df))
    width = 0.35
    ax.bar(x - width/2, segment_df["rate_control_pct"], width, label="gate_30 (control)", color=COLORS["gate_30"])
    ax.bar(x + width/2, segment_df["rate_treatment_pct"], width, label="gate_40 (treatment)", color=COLORS["gate_40"])
    ax.set_xticks(x)
    ax.set_xticklabels(segment_df["segment"], rotation=10)
    ax.set_ylabel("Day-7 retention rate (%)")
    ax.set_title("Heterogeneous Treatment Effect by Engagement Segment")
    ax.legend(frameon=False)
    for i, row in segment_df.iterrows():
        ax.text(i, max(row["rate_control_pct"], row["rate_treatment_pct"]) + 0.5,
                f"p={row['p_value']:.3f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_segment_effects.png", dpi=200)
    plt.close(fig)


def peeking_risk_plot(peeking_result: dict):
    fig, ax = plt.subplots(figsize=(7, 5))
    vals = [peeking_result["nominal_single_look_alpha"] * 100,
            peeking_result["simulated_false_positive_rate_with_peeking"] * 100]
    labels = ["Nominal false-positive\nrate (single look)", f"Simulated false-positive rate\n({peeking_result['n_looks_simulated']} daily peeks)"]
    colors = ["#1d9e75", "#c0392b"]
    bars = ax.bar(labels, vals, color=colors)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.3, f"{v:.1f}%", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("False positive rate (%)")
    ax.set_title(f"Cost of 'Peeking' Daily: {peeking_result['inflation_factor']}x Inflation")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_peeking_risk.png", dpi=200)
    plt.close(fig)
