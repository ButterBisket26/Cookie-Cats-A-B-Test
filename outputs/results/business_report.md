# Product Decision Report: Gate Placement A/B Test

**Prepared for:** Game Product & Growth Teams
**Experiment:** Cookie Cats Gate-30 vs. Gate-40 (90,189 players, 14-day window)
**Recommendation:** Do not ship gate_40

---

## Executive Summary

The Cookie Cats team tested whether moving the first monetization gate from level 30 to level 40 would improve player retention by giving players a longer uninterrupted initial experience. **The answer is no — the later gate hurts retention.**

| Metric | gate_30 (Control) | gate_40 (Treatment) | Change |
|---|---|---|---|
| Day-1 Retention | 44.82% | 44.23% | −0.59pp (not significant) |
| Day-7 Retention | **19.02%** | **18.20%** | **−0.82pp (p = 0.0015)** |
| Median Game Rounds | 17 | 16 | No meaningful difference |

The Day-7 retention loss is **statistically robust across three independent methods** — a frequentist significance test (p = 0.0015), a Bayesian analysis (99.9% probability gate_30 is better), and a bootstrap resampling check (99.96% of resamples favor gate_30).

---

## Key Finding: The Damage Is Concentrated Where It Matters Most

We segmented players by their engagement level **before** either gate (at 20 rounds — well below both gate placements), creating a clean pre-treatment split:

| Segment | gate_30 | gate_40 | Difference | Significance |
|---|---|---|---|---|
| **Engaged** (≥20 rounds) | 37.25% | 36.28% | **−0.97pp** | **p = 0.041** |
| Casual (<20 rounds) | 3.02% | 2.90% | −0.12pp | p = 0.454 |

**This is the most important finding in the analysis.** The average effect looks like a modest −0.82pp, but that average masks a business-critical split:

- **Casual players** — who barely experience either gate — show no difference. They dilute the signal in any average analysis.
- **Engaged players** — the ones most likely to become long-term, high-value, paying users — bear the **entire retention cost** of the later gate, and the effect is statistically significant within this segment.

If the team had only looked at the overall average, they might have concluded "the effect is small, maybe worth trying." The segment decomposition reveals the effect is not small for the players who matter most — it's almost 1 percentage point, and those players are disproportionately the ones who drive lifetime value.

---

## The Later Gate Does Not Improve Engagement

If moving the gate later were genuinely giving players a better, longer uninterrupted experience, we would expect them to play more total rounds. They didn't.

- **Median rounds:** 17 (gate_30) vs. 16 (gate_40)
- **Mann-Whitney U test:** p = 0.050 (borderline, no meaningful difference)

The later gate isn't trading engagement for retention. It's just costing retention without any offsetting engagement gain.

---

## Power Analysis: The Test Was Adequate

| Question | Answer |
|---|---|
| At our current sample size (~45K/group), what effect can we detect? | **≥ 0.735pp** at 80% power |
| To detect a 1pp difference reliably, how many players would we need? | **24,179 per group** (we had 44,700+) |
| Could a smaller-but-important effect have been missed? | Effects < 0.7pp would require larger samples — but the observed effect (0.82pp) **exceeds the detection threshold** |

This is not an underpowered "we didn't find anything" result. The test was large enough to detect the effect that was actually there, and it found it.

---

## Methodology Note: The Peeking Risk

Most A/B tests in practice are checked daily, and shipped the moment p < 0.05. We simulated this scenario:

| Checking strategy | False-positive rate |
|---|---|
| Single planned analysis at end of test | 5.0% (nominal) |
| Checking the dashboard every day for 14 days | **22.1%** (simulated, 2,000 replays) |

**That's a 4.42x inflation in the chance of shipping a change that doesn't actually work.** This isn't a theoretical concern — it's the most common methodological error in applied A/B testing. Our recommendation is based on the full-window dataset, not an early peek.

---

## What We'd Do Next

### Priority 1: Do Not Ship gate_40
The evidence against it is consistent across three independent methods, statistically significant, and concentrated in the highest-value player segment. There is no upside — engagement didn't improve.

### Priority 2: Investigate Post-Gate-30 Drop-Off
**18.6% of players who reach gate 30 churn within the next 10 rounds.** This is a larger addressable opportunity than gate timing. A better reward, hint, or pacing change at that exact moment — reducing the friction of the gate experience itself — could improve retention more than moving the gate ever would.

### Priority 3: Build Daily Event-Level Instrumentation
To prevent future peeking risk, instrument daily-level event logging so future tests can be properly sequentially monitored (with alpha-spending corrections) instead of relying on a single end-of-test analysis.

### Priority 4: Run an Engaged-Segment-Specific Follow-Up
If the team wants to explore gate timing further, run a dedicated test focused on the engaged segment. The current sample within that segment is smaller, so a targeted test would give a more precise read on whether there's a gate placement that works better for high-engagement players specifically.

---

## Appendix: Methods Used

| Method | Purpose | Key Result |
|---|---|---|
| Two-proportion z-test | Primary retention comparison | p = 0.0015 for Day-7 |
| Bayesian beta-binomial | Direct P(control better) | 99.9% for Day-7 |
| Bootstrap (5,000 resamples) | Assumption-free cross-check | 99.96% favor control |
| Mann-Whitney U | Guardrail (skewed engagement metric) | p = 0.050 |
| Power analysis | Detectable effect size at current N | MDE = 0.735pp |
| Permutation-null simulation | Peeking-risk quantification | 4.42x false-positive inflation |

---

*Report generated by the Cookie Cats A/B Test analytics pipeline. All code and data are available in the repository.*
