# Problem Statement

## Does Moving the Game's First Monetization Gate Later Help or Hurt Player Retention?

---

### Business Context

Cookie Cats is a mobile puzzle game by Tactile Entertainment. Like most free-to-play games, it uses **progression gates** — points in the game where players must either wait or pay to continue. These gates serve a dual purpose:

1. **Monetization** — impatient players pay to skip the wait
2. **Pacing** — a forced break can prevent fatigue and improve long-term retention

The product team hypothesized that moving the first gate **later** (from level 30 to level 40) — giving players a longer uninterrupted initial experience — might improve how many players stick around.

### The Experiment

A **randomized A/B test** was run on **90,189 real players**, assigned at install time:

| Group | Gate Placement | Players |
|---|---|---|
| Control | Gate at level 30 | 44,700 |
| Treatment | Gate at level 40 | 45,489 |

**Metrics recorded per player:**
- `retention_1` — Did the player return on Day 1? (boolean)
- `retention_7` — Did the player return on Day 7? (boolean)
- `sum_gamerounds` — Total game rounds played over 14 days (integer, right-skewed)

This is **genuinely randomized experimental data** from a real product decision — not a simulation — which is what allows a causal read on the gate-placement effect.

### The Analytical Problem

Given this data, produce a **ship / don't-ship recommendation** that is defensible on four fronts:

| # | Question | Why It Matters |
|---|---|---|
| 1 | **Is the primary effect statistically real, by more than one method?** | A single p-value is fragile. Three independent methods converging on the same answer is not. |
| 2 | **Does the average effect hide a harmful effect on a subgroup?** | An overall "no effect" can mask a large positive for one segment and a large negative for another. The players who matter most to revenue might be the ones being harmed. |
| 3 | **Was the test adequately powered?** | If we can't detect a meaningful effect at this sample size, "no significant difference" means "we don't know," not "there is no difference." |
| 4 | **Was the result obtained without methodological bias?** | The most common error in applied A/B testing — checking the dashboard every day and shipping the moment p < 0.05 — inflates false-positive rates by 4x or more. Did this analysis avoid that trap? |

### Why a Single Chi-Square Test Is Not Enough

Most public analyses of this exact dataset stop at a single chi-square test on Day-1 retention. This is insufficient for a real product recommendation:

| What a single test tells you | What a product team actually needs |
|---|---|
| "Is there a difference on average?" | "Is there a difference **for the players who matter most**?" |
| "Is p < 0.05?" | "How confident are we, in terms an executive can act on?" |
| "Did the test find significance?" | "Could this test size have detected a smaller-but-still-important effect?" |
| "The dashboard showed p<0.05 on day 4, so we shipped" | "How often would that happen purely by chance if we checked every day?" |

### Methodology

Each of the four questions above maps to a specific analytical module:

1. **Funnel Construction** (`funnel.py`) — Reframe the single `sum_gamerounds` number as a progression funnel across milestones (1, 10, 30, 40, 50, 100 rounds), and measure churn in the 10-round window immediately after each group's gate.

2. **Primary + Guardrail Testing** (`ab_test.py`) — Two-proportion z-tests with confidence intervals on the risk difference for Day-1 and Day-7 retention. Mann-Whitney U test on the heavily right-skewed engagement metric as a guardrail. Bayesian beta-binomial model giving P(control is actually better) directly. Non-parametric bootstrap as an assumption-free cross-check.

3. **Heterogeneous Treatment Effects** (`segments.py`) — Split players by pre-gate engagement level (a variable not affected by treatment, avoiding post-treatment conditioning bias) and re-run the primary test within each segment.

4. **Power Analysis + Decision Framework** (`decision.py`) — Compute the minimum detectable effect at the observed sample size, and the sample size required to detect smaller effects. Convert all findings into a RICE-scored product roadmap.

5. **Peeking-Risk Simulation** (`peeking_risk.py`) — Simulate 2,000 null-hypothesis replays of the 14-day experiment window, checking cumulative significance daily, to quantify false-positive rate inflation from sequential peeking.

### Data Source

**Cookie Cats gate-placement A/B test** (Tactile Entertainment, released for analysis via the applied A/B testing community). 90,189 players, randomly assigned to gate_30 or gate_40, with `sum_gamerounds`, `retention_1`, and `retention_7` recorded per player.

### Deliverables

- A **modular, reusable pipeline** (`src/`) — swap the CSV and metric names to retarget at any binary-outcome randomized experiment
- **5 decision-ready exhibits** — funnel comparison, retention comparison with CIs, Bayesian posterior distributions, segment-level heterogeneous effects, and peeking-risk inflation chart
- `outputs/results/summary_metrics.json` — every statistic from every method, machine-readable
- A **plain-language business findings report** and RICE-scored recommendation (`outputs/results/business_report.md`)
