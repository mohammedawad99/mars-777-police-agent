# Competitive research laboratory — group MaRs-777

**Status: CURRENT.** Established at Stage 9B-0. **No production strategy was
changed by this stage, and none may be until this document's gates are met.**

This is the court, built before the race. It exists so that a future claim
"candidate X is better than what we ship" is a measurement rather than an
opinion.

## 1. What the source asks for, and what it does not

| Requirement | Class | Where |
|---|---|---|
| the movement policy is the group's own choice, from three equal tracks (Bayesian belief + Manhattan, own heuristic, optionally RL) | `SOURCE_BINDING` (freedom, not obligation) | Ch 6 §6.3.1 |
| the spatial decision stays **algorithmic**; an LLM may never decide a move | `SOURCE_BINDING` | Ch 6 §6.1, §6.6; App E rule 25 |
| a strategy may read only lawful local observation | `SOURCE_BINDING` | Ch 6 §6.4 (*"neither of them sees the opponent's real position"*) |
| strategy choice is private and not negotiated | `SOURCE_BINDING` | Ch 6 §6.3.1; App F Table 22 (reference-only) |
| systematic parameter study / sensitivity analysis | `GUIDELINE_EXCELLENCE` §9.1 | guideline v3.00 |
| results-analysis notebook or equivalent | `GUIDELINE_EXCELLENCE` §9.2 | guideline v3.00 |
| result visualisation (bar/line/scatter/heatmap/box) | `GUIDELINE_EXCELLENCE` §9.3 | guideline v3.00 |
| reproducibility of the experiment | `GUIDELINE_EXCELLENCE` §8.4, §6.4 | guideline v3.00 |
| cost/resource awareness | `GUIDELINE_EXCELLENCE` §11 | guideline v3.00 |
| a "learning curve" as literal ML training evidence | `JUSTIFIED_NA` | see §11 below |

**No machine learning is implemented, so none is claimed.** Nothing in this
project trains a model to move; the movement policy is a deterministic
heuristic. There is therefore no training loss, no epoch, no reward curve, and
this laboratory produces none.

## 2. Frozen baselines

| | Police repository | Thief repository |
|---|---|---|
| production strategy | `CompetitiveStrategy` | `BaselineStrategy` |
| resolved from | `composition.py` / `compose_backend.py` | `composition.py` / `compose_backend.py` |
| sources | `app/competitive_strategy.py`, `app/baseline_strategy.py` | `app/baseline_strategy.py` |

Identity is recorded as the SHA-256 of those sources plus the commit, by
`research/identity.py`, and travels in every result row and in the manifest. A
benchmark whose identity does not match the shipped files is a benchmark of
something else.

## 3. What a strategy may see

Every policy — production or benchmark opponent — receives exactly one
`Observation`, whose four members are the board, its own cell, its own quota and
its own lawfully folded scent belief.

| Field | Police | Thief | Class |
|---|---|---|---|
| own position | yes | yes | own truth |
| barriers on the board | yes | yes | public, declared truthfully (App E #15/#16) |
| board dimensions | yes | yes | locked configuration |
| own barrier quota | yes | yes | locked configuration |
| scent belief folded from the **opponent's** disclosed emissions | yes | yes | lawful partial evidence |
| received hint text | no | no | not on the decision seam at all |
| opponent's exact position | **no** | **no** | prohibited (Ch 6 §6.4) |
| unrevealed intent, nonce, commitment | **no** | **no** | prohibited |
| opponent's internal strategy or parameters | **no** | **no** | prohibited |
| any future move or future draw | **no** | **no** | prohibited |

The guarantee is structural rather than procedural: `Observation` has **no
field** those prohibited items could arrive in, and the research harness passes
a policy nothing else — no game handle, no clock, no random stream.

## 4. Opponent corpus

Seven deterministic legal families, all with the identical observation budget:

| Family | Idea |
|---|---|
| `random_legal` | seeded arbitrary choice among legal moves — robustness floor |
| `center_mobility` | prefers cells with the most onward moves |
| `evasive` | maximises reachable region, avoids its own strongest evidence |
| `pursuit` | walks toward the strongest lawful evidence |
| `barrier_aware` | prefers mobility, then reachable region |
| `scent_aware` | uses only scent, minimising its own exposure |
| `adversarial_corner` | deliberately enters tight regions — the case a pursuer should punish |

A **police-side** opponent may also place a barrier when the lawful evidence on
a placeable neighbour beats the evidence where it would otherwise move. Only the
police may place at all; the rule is written in `research/opponents.py` and is an
independent research policy, never a copy of another repository's production
strategy. **`research` imports nothing from a sibling repository**, and a test
asserts it.

## 5. Configuration corpus, and the Appendix F classes

| Parameter | App F | Class | Benchmark values | Why |
|---|---|---|---|---|
| grid size | T13 #1, example 7×7 | **MINIMUM** | 7, 9, 11 | may be raised, never eased; **5×5 is not source-permitted** and is excluded |
| barrier quota | T15 #2, example 14 | **MINIMUM** | 14, 22 | example is the default; 22 is a legal raise |
| max moves / survival threshold | T15 #3/#4, example 35 | **MINIMUM** | 35, 45 | as above |
| opening cells | T13 #5/#6 | **NEGOTIABLE** | seed-selected, plus the example geometry | free by agreement |
| movement set | T15 #1 | **FIXED** | never varied | deviation disqualifies |
| scent source 0.9, decay 0.10, field 5×5 | T16 #1–#3 | **FIXED** | never varied | deviation disqualifies |
| scoring 20/5/5/10/2 | T17 | **FIXED** | used as the outcome authority | — |
| six sub-games | T18 #1 | **FIXED** | not a benchmark axis | — |

## 6. Seeds, and the flaw the first run exposed

Seeds are derived from `SHA-256("mars777-research/v1/" + set + "/" + index)`,
first 8 bytes big-endian. Never `hash()`, which is not stable across processes.
Three disjoint banks: **development** (64), **holdout** (64), **stress** (16).

**The first benchmark run was discarded, and the reason is recorded rather than
buried.** It reported win rates of exactly `0` and exactly `1/3` with tight
confidence intervals. Measured directly, the seed changed the outcome in **0 of
42** (family, configuration) cells: every policy is a deterministic function of
position, so sixty-four seeds replayed one game and the intervals treated
sixty-four copies of one observation as sixty-four observations.

The corpus now lets the seed select the one thing Appendix F leaves free — the
two opening cells (Table 13 #5/#6, `NEGOTIABLE`). After the correction the seed
changes the outcome in **26 of 42** cells, and the intervals mean something.
`tests/research/test_research_units.py` pins the property so it cannot silently
return.

**One row's interval must not be read as its `n` suggests.** The
`appendixF-example` configuration fixes both opening cells on purpose, so every
seed replays the same game: it contributes **7 distinct scenarios** (one per
opponent family), not 1008. Its `n` is honest about how many games were played
and dishonest about how much independent information they carry, so its interval
is reported but must not be compared with the other rows'. Measured, not
assumed: 1 of its 7 family cells varies with the seed, against 7 of 7 for every
other configuration. Reweighting or dropping the replication is a corpus
improvement for Stage 9B-1.

**Holdout policy.** The holdout bank exists to confirm a promotion, never to tune
a candidate. This is a *process* commitment, and the honest limitation is that
nothing mechanically prevents a person from looking; what the code guarantees is
deterministic separation and a separately reported number.

## 7. Metrics, frozen before any candidate exists

**Primary, both roles: `win_rate`** — `own_score > opponent_score` under the
Appendix F Table 17 table the tournament itself uses. No research score is
invented, because a research score could disagree with the league.

| Role | Secondary (diagnostic only) |
|---|---|
| Police | capture rate, mean steps to end, barriers spent, decision latency |
| Thief | survival rate, mean steps survived, barriers faced, decision latency |

## 8. Statistics

Proportions and means are reported with `n`, median, and a **deterministic
percentile bootstrap** 95% interval (1000 resamples drawn from a SHA-256
counter, never a random module), so a published figure is reproducible and an
argument about it is checkable. Fewer than 8 observations report **no** interval
rather than a meaningless one. Baseline-versus-candidate comparisons must be
**paired** — same seeds, same configurations, same opponents — and reported as
the per-game difference.

## 9. Promotion gates — frozen now, before any candidate exists

A candidate may replace the shipped strategy only if **all** hold:

| # | Gate |
|---|---|
| A | zero legality regression: every action still accepted by `Replay.check` |
| B | zero protocol/audit regression: the full production suite stays green |
| C | primary `win_rate` improves on the **promotion** set, and the paired 95% interval for the difference excludes zero |
| D | **no material regression** on any opponent family or configuration family |
| E | the **holdout** set confirms the direction of the improvement |
| F | decision latency p95 stays within the ceiling in §10 |
| G | memory and runtime remain within the same order as the baseline |
| H | no prohibited information: the input matrix in §3 is unchanged |
| I | the improvement is not solely against a pinned-KIT-shaped opponent |

**Material regression is defined numerically now**, before any candidate result
is known: a drop of **more than 5 percentage points** in `win_rate` on any
family or configuration cell whose paired 95% interval also excludes zero. A
drop inside the interval is noise; a drop outside it is a regression.

**Thief:** the same structure with `win_rate` (survival-driven) as primary.

## 10. Performance budget

Measured at the production call surface, `choose_action`, separately from
harness throughput. **Ceiling for any future candidate: p95 ≤ 25 ms per
decision**, an order of magnitude inside the locked 30 s per-request watchdog and
far inside any turn deadline. Baseline numbers are in `results/baseline/latency.json`.

## 11. "Learning curve" — the source-faithful reading

The guideline asks for research evidence of progress. This project trains
nothing, so a literal training curve would be a fabricated result. The truthful
equivalents, and what this stage produces:

* **performance by opponent family** — where the baseline is strong and weak;
* **performance by configuration family** — how board size and quota change it;
* **performance versus candidate revision** — the axis a later stage extends,
  starting from the baseline point frozen here.

Every figure is labelled for what it actually is. Nothing here is called a
training loss, an epoch, or a reward.

## 12. Reproduction

```bash
uv run python -m research.bench_main all --out results
```

That runs every seed bank against the whole corpus, writes the result rows,
regenerates every table and figure, measures decision latency and rewrites the
manifest. No network, no credential, no live game, no editing between stages.

## 13. Baseline results (Stage 9B-0, frozen)

6,048 games per role: 7 opponent families × 6 configuration families × (64 + 64
+ 16) seeds. Runtime ≈ 12 minutes per role on one developer core.

### Police — `CompetitiveStrategy`

**Overall win rate 5.26% [4.66%, 5.82%]**, mean score 5.79 of a possible 20,
mean 3.40 barriers spent of a 14 quota.

| Opponent family | win rate | 95% CI |
|---|---|---|
| `adversarial_corner` | 0.111 | [0.091, 0.133] |
| `center_mobility` | 0.076 | [0.059, 0.095] |
| `random_legal` | 0.060 | [0.045, 0.076] |
| `pursuit` | 0.044 | [0.031, 0.057] |
| `barrier_aware` | 0.032 | [0.021, 0.045] |
| `scent_aware` | 0.029 | [0.017, 0.041] |
| `evasive` | **0.015** | [0.007, 0.023] |

| Configuration | win rate | 95% CI |
|---|---|---|
| `grid7` / `grid7-quota22` | 0.073 | [0.058, 0.090] |
| `grid9` / `grid9-horizon45` | 0.063 | [0.048, 0.079] |
| `grid11` | 0.042 | [0.030, 0.055] |
| `appendixF-example` | **0.000** | [0.000, 0.000] — 7 distinct scenarios, see §6 |

Development 0.047, holdout 0.060, stress 0.048 — the three banks agree.

### Thief — `BaselineStrategy`

**Overall win rate 99.06% [98.79%, 99.27%]**, mean score 9.95 of a possible 10.
Only two families ever beat it, and only with barriers: `adversarial_corner`
0.958 and `barrier_aware` 0.976. Every other family: 1.000.

### Decision latency

| Role | median | p95 | max | samples |
|---|---|---|---|---|
| Police | 0.03 ms | 2.09 ms | 3.06 ms | 210 |
| Thief | 1.20 ms | 1.31 ms | 2.55 ms | 210 |

Both are two orders of magnitude inside the 25 ms candidate ceiling.

## 14. What the baseline evidence supports — police

**Observed (measurement).**

1. The police wins **5.3%** of games. The tournament pays 20 for a capture and 5
   for a survival, so this is close to the floor.
2. It is weakest against **region-maximising evaders** (`evasive`, 1.5%) and
   strongest against an opponent that walks into tight regions (11.1%).
3. **Raising the barrier quota changes nothing**: `grid7` and `grid7-quota22`
   are identical in win rate and in barriers spent (4.06). The quota is not the
   binding constraint — the policy spends ~3.4 of 14.
4. **A longer horizon changes nothing**: `grid9` and `grid9-horizon45` have the
   same win rate; only the step count differs.
5. Win rate **falls as the board grows**: 0.073 → 0.063 → 0.042 for 7, 9, 11.
6. On Appendix F's own example geometry it captured **0 times** — with the
   caveat in §6 that this row is 7 scenarios replicated, not 1008.

**Hypotheses (not facts).** These follow from reading the policy beside the
numbers, and none is established by this stage:

* `BaselineStrategy` maximises **its own** reachability, which is a target-free
  objective — there is no term that closes distance on believed evidence, which
  would explain both the flat performance and the failure against evaders.
* `CompetitiveStrategy` admits a placement only when its support strictly
  exceeds the evidence at the cell the baseline would move to, which is a rare
  condition — consistent with spending 3.4 of 14 barriers.
* Larger boards dilute a fixed-radius scent field, so the evidence that funds a
  placement is weaker where there is more room to search.

## 15. What the baseline evidence supports — thief

The thief wins 99.1% of games and loses only to barrier pressure. There is **no
statistically supported weakness** to fix, and the historical record already
contains one rejected thief candidate. **Recommendation: `NO_CHANGE`.** Changing
it for symmetry with the police would risk a 99% baseline for no measured reason.

## 16. Candidate hypotheses for Stage 9B-1 — police only

Ranked by expected benefit against evidence support, implementation risk,
latency risk and overfitting risk. **None is implemented, and none may be until
this stage has supervisory PASS.**

| # | Hypothesis | Evidence | Benefit | Risk |
|---|---|---|---|---|
| 1 | **Belief-directed pursuit**: add a term that reduces distance to the strongest lawful evidence, instead of only maximising own reachability | findings 1, 2, 5 — the policy has no target term at all | high | low latency (BFS already computed); moderate design risk |
| 2 | **Mobility denial**: prefer placements that cut the evader's reachable region rather than only those the evidence directly supports | findings 2, 3 — the quota is unspent and evaders thrive on region | high | must not weaken the existing strict admission gate |
| 3 | **Spend the quota**: relax the placement admission when a large quota remains late in the horizon | finding 3 — 3.4 of 14 spent | medium | irreversible placements; needs a regression guard |
| 4 | **Board-size-aware weighting**: scale the evidence threshold with board area | finding 5 | medium | overfitting risk: only three grid sizes measured |
| 5 | **End-game trap completion**: prefer placements that complete a `GAME-005` enclosure | capture is only ever `BAR-003` or `GAME-005` | medium | narrow applicability |

Candidate 4 carries the highest overfitting risk and should be attempted last,
if at all. Candidates 1 and 2 are the ones the evidence actually points at.
