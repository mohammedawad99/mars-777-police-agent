# Sensitivity analysis — group MaRs-777, Police

**Post-hoc and descriptive. Nothing here tuned anything.** Every number below is
read from evidence that was already committed before this analysis existed: the
Stage-9B-0F corrected baseline tables, the Stage-9B-1A candidate screening, and
the one-shot final-holdout result. **No experiment was run to produce this
document**, the final holdout was not reopened, and no parameter of the promoted
strategy was touched — the strategy was frozen before the holdout and has not
changed since.

This matters more than the numbers: a sensitivity study run *after* a promotion,
which then fed back into the strategy, would silently convert a sealed evaluation
into another development set.

## 1. Sensitivity to board size — the strongest structural effect

| grid | baseline win rate | N | promoted delta (holdout) | 95% CI |
|---|---|---|---|---|
| 7×7 | 0.0749 | 988 | +0.0726 | [+0.0431, +0.1043] |
| 9×9 | 0.0639 | 1002 | +0.0714 | [+0.0446, +0.1004] |
| 11×11 | 0.0417 | 1008 | +0.0658 | [+0.0385, +0.0930] |

**Baseline difficulty rises with area**: 0.075 → 0.064 → 0.042. The 7 and 9
intervals overlap, so only the 11×11 drop is clearly separated — a limit that was
already recorded when this finding was reclassified from CONFIRMED to **WEAKENED**
at Stage 9B-0F, and it is repeated here rather than quietly upgraded.

**The improvement is remarkably flat across board size** (+0.073 / +0.071 /
+0.066), and all three intervals exclude zero. That is the useful result: the
promoted barrier rule is not a small-board trick, and it needed no board-specific
weighting. A per-grid weight was in fact the one candidate hypothesis
**deliberately never implemented**, precisely because three grid sizes and one
clear separation is the highest overfitting risk in the study.

## 2. Sensitivity to barrier quota — none detectable

| configuration | quota | baseline win rate | promoted delta |
|---|---|---|---|
| `grid7` | 14 | 0.074899 | +0.0726 |
| `grid7-quota22` | 22 | 0.074899 | +0.0726 |

Raising the quota from the Appendix F Table 15 minimum of **14** to **22**
changes the baseline win rate by **nothing at all** — the two rows are identical
to six decimal places — and the promoted delta by nothing either.

The mechanism explains it: the policy spends about **3.2 of 14** barriers per
game, so the quota was never the binding constraint. Instrumenting the belief
showed what actually binds — the admission gate — and fixing that raised the win
rate while *reducing* mean barrier use to 3.17. **Spending more was never the
answer**, which is also what the rejected C3 candidate demonstrated by lowering
the threshold and doing worse.

## 3. Sensitivity to horizon — none detectable

| configuration | horizon | baseline win rate | promoted delta |
|---|---|---|---|
| `grid9` | 35 | 0.063872 | +0.0714 |
| `grid9-horizon45` | 45 | 0.063872 | +0.0714 |

Ten extra steps change nothing measurable. Games that end, end early; games that
survive to 35 survive to 45. This is why the horizon was not treated as a
competitive axis.

## 4. Sensitivity to opponent family — the largest spread by far

| family | baseline win rate | promoted delta (holdout) |
|---|---|---|
| `adversarial_corner` | 0.1346 | **+0.1415** |
| `center_mobility` | 0.0926 | +0.1164 |
| `random_legal` | 0.0723 | +0.0409 |
| `pursuit` | 0.0533 | +0.0881 |
| `barrier_aware` | 0.0393 | +0.0314 |
| `scent_aware` | 0.0351 | +0.0157 |
| `evasive` | 0.0182 | +0.0660 |

Opponent behaviour dominates every configuration axis: baseline win rate spans
**7.4×** across families (0.018 → 0.135) while spanning only **1.8×** across
board sizes. Any single headline number is therefore a statement about *this
opponent corpus*, not about the game.

The gain is **largest where the mechanism predicted it** — `adversarial_corner`,
the family whose positions blocked the old admission gate in 89% of
belief-carrying decisions — and the two weakest baseline families (`evasive`
0.018, `scent_aware` 0.035) both improve rather than being traded away.

## 5. Sensitivity to the candidate threshold — the variants already tried

Recorded from Stage 9B-1A screening, N=471. **No new variant was run.**

| threshold | candidate | paired delta | 95% CI | status |
|---|---|---|---|---|
| 0.9 (source strength) | C4 | **+0.0722** | [+0.0446, +0.1019] | ADVANCED |
| 0.9, with new mover | C2 | +0.0510 | [+0.0234, +0.0786] | NOT_ADVANCED |
| 0.3 (aggressive) | C3 | +0.0234 | [−0.0021, +0.0510] | REJECTED_GATE |
| n/a (mover only) | C1 | **−0.0488** | [−0.0679, −0.0318] | REJECTED_GATE |

The response to the threshold is **monotone in the wrong direction for
aggression**: lowering the floor from 0.9 to 0.3 made the result *worse* and its
interval crossed zero. Only two values were ever tried, both anchored to the
Appendix F Table 16 FIXED source strength rather than searched, which is why this
row is a sensitivity observation and not a tuning curve.

## 6. Sensitivity of decision latency to board size

| board | p50 | p95 | max | N |
|---|---|---|---|---|
| `grid9` | 2.17 ms | 2.28 ms | 2.90 ms | 213 |
| `grid11` | 3.20 ms | 3.34 ms | 4.17 ms | 210 |

Latency grows with board area, as a per-cell belief scan must, and stays roughly
**7×** inside the frozen 25 ms ceiling on the largest legal board. Board size is
the only axis that moves latency measurably.

## 7. What this analysis cannot tell you

- Every number describes **our own opponent corpus**. The seven families are
  models we wrote; the real opponent is unknown and is not represented here.
- `appendixF-example` has **N = 9** in the baseline corpus and **N = 7** in the
  holdout. Its apparent +0.2857 is an observation, not a finding, and it is
  excluded from every headline.
- Configuration axes were swept **jointly**, not one factor at a time from a
  single centre point. The quota and horizon rows are clean pairwise
  comparisons because those corpora differ in exactly one value; the grid rows
  are not, so read them as a trend rather than as a controlled experiment.
