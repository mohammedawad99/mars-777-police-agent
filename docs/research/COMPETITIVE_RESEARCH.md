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

**The experimental unit is the scenario, fixed at Stage 9B-0F.** Stage 9B-0
counted rows: 6,048 of them, over 4,991 distinct conditions, with 7 conditions
replayed 144 times each. Policies here are deterministic, so a replayed scenario
produces the identical game and adds no information — counting it again inflates
`N` and narrows an interval that should not narrow.

`scenario_id` is now the canonical identity (`scenario-1`), a SHA-256 over: role
under evaluation, opponent family, configuration name, grid, quota, horizon,
both opening cells, **and the opponent seed only where that family's behaviour
actually depends on it**. Measured, not assumed: only `random_legal` reads its
seed, and the 7 outcome disagreements in the Stage-9B-0 rows were all that
family. Nothing that cannot change a game — path, timestamp, row number — is in
the identity.

Three consequences, all enforced in code and pinned by tests:

* **Openings are drawn without replacement.** Sixty-four seeds that collide onto
  twenty openings are twenty observations; a colliding seed is now skipped, and
  `size_of` reports what a sweep will actually play rather than
  `families × configs × seeds`.
* **A finite space yields its real size.** `appendixF-example` has exactly **one**
  legal opening, so it contributes **7 scenarios** in total — one per family —
  and is reported as `N = 7`, never as `N = 1008`.
* **The reference geometry is excluded from the headline** and reported on its
  own, so seven observations cannot borrow the confidence of two thousand.

**Holdout policy, corrected at Stage 9B-0F.** Stage 9B-0 ran a bank called
`holdout` and then read its baseline results while ranking candidate hypotheses.
A set whose outcomes have been seen is not blind, whatever it is called, so it
was **reclassified as `validation`** — what it actually is. Its results are kept,
not deleted, and this paragraph is the record rather than a rewrite.

A genuinely sealed **`final_holdout`** was created afterwards, under its own
namespace `mars777-research/final-holdout-v1/`, disjoint from every working
bank, and **no game has been played on it**. Its scenario list is enumerated,
hashed and committed in `results/final_holdout.json` so that "fixed before the
candidate existed" is checkable rather than asserted. `bench_main` iterates
`working_banks()`, which does not contain it, and asking for it by name is
refused; there is deliberately no `--final-holdout` flag yet, because a flag
that existed today is a flag somebody could pass today.

| Bank | Purpose | May be inspected |
|---|---|---|
| `development` | candidate design and tuning | freely |
| `validation` (was `holdout`) | comparison once a coherent revision exists | occasionally |
| `stress` | rare and adversarial cases | freely |
| **`final_holdout`** | **exactly one** promotion evaluation, after the candidate is frozen | **not until then** |

If a final-holdout evaluation fails, the candidate is rejected. A new cycle needs
a **new sealed version** — a failed holdout does not become blind again.

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
rather than a meaningless one.

**The resampling unit is one unique scenario.** Every aggregate collapses rows by
`scenario_id` before it measures anything, and a test asserts that duplicating a
series does not narrow its interval — which is exactly the error the Stage-9B-0
numbers contained.

**Weighting, frozen now.** The headline is **scenario-weighted over the varied
configurations**, which carry equal target `N` by construction (64 openings
each), so scenario weighting and equal-cell weighting coincide there and no
config can dominate by having a larger legal opening space. The fixed reference
geometry is excluded from that headline and reported separately with its own
`N`. This is the tournament-relevant reading: a real match is played on one
agreed configuration, and no configuration is more likely than another.

**Paired comparison, frozen now.** A baseline-versus-candidate comparison is
keyed by `scenario_id`, not by position: `paired_by_scenario` refuses unless
both sides played exactly the same scenario set, so a baseline measured on one
bank and a candidate on another can never be presented as pairs.

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

## 13. Baseline results — corrected at Stage 9B-0F

The Stage-9B-0 numbers counted rows; these count **unique scenarios** and
exclude the fixed reference geometry from the headline. Both are shown, because
the correction changed the headline and hiding that would be the same error in a
different place.

| Role | Stage 9B-0 (rows) | **Corrected (scenarios)** |
|---|---|---|
| Police | 0.0526 [0.0466, 0.0582], "n = 6048" | **0.0638 [0.0567, 0.0706], n = 4988** |
| Thief | 0.9906 [0.9879, 0.9927], "n = 6048" | **0.9886 [0.9856, 0.9914], n = 4988** |

**Why the police number rose.** The old figure folded in 1,008 rows of the fixed
reference geometry — 9 distinct scenarios replayed — every one of them a loss,
each weighted as an independent observation. Removing that inflation raises the
headline by about 1.1 points. The old interval was also too narrow, because
1,057 duplicate rows were resampled as if they were independent.

**Reference geometry, reported separately.** Police 0.000 and thief 1.000, at
**N = 9** — six non-seeded families contribute one scenario each, and
`random_legal` contributes three because its behaviour genuinely varies with its
seed. Nine, not seven, and not 1,008.

**Run shape after the correction.** 5,033 raw rows per role, 4,997 unique
scenarios, multiplicity `{1: 4967, 2: 24, 3: 6}` — the remaining duplicates are
cross-bank collisions on the same opening, correctly collapsed. Runtime ≈ 10
minutes per role.

### Police — `CompetitiveStrategy`, corrected

| Opponent family | win rate | 95% CI | N |
|---|---|---|---|
| `adversarial_corner` | 0.135 | [0.109, 0.160] | 713 |
| `center_mobility` | 0.093 | [0.072, 0.115] | 713 |
| `random_legal` | 0.072 | [0.056, 0.092] | 719 |
| `pursuit` | 0.053 | [0.038, 0.070] | 713 |
| `barrier_aware` | 0.039 | [0.025, 0.055] | 713 |
| `scent_aware` | 0.035 | [0.022, 0.049] | 713 |
| `evasive` | **0.018** | [0.010, 0.028] | 713 |

| Configuration | win rate | 95% CI | N |
|---|---|---|---|
| `grid7` / `grid7-quota22` | 0.075 | [0.059, 0.091] | 988 |
| `grid9` / `grid9-horizon45` | 0.064 | [0.050, 0.081] | 1002 |
| `grid11` | 0.042 | [0.030, 0.055] | 1008 |
| `appendixF-example` | 0.000 | [0.000, 0.000] | **9 — reference only** |

### Thief — `BaselineStrategy`, corrected

**0.9886 [0.9856, 0.9914]**, N = 4988. Beaten only by `adversarial_corner`
(0.950, N=713) and `barrier_aware` (0.971, N=713); every other family 1.000.

### Decision latency

Unchanged by the correction — it measures `choose_action`, not aggregation.
Police p95 ≈ 2.1 ms, thief p95 ≈ 1.3 ms, both far inside the 25 ms ceiling.

## 14. Police weakness findings, reclassified against the corrected numbers

| Stage-9B-0 finding | Status | Corrected evidence |
|---|---|---|
| Weakest against region-maximising evaders | **CONFIRMED** | `evasive` 0.018 [0.010, 0.028], N=713 — still the worst family by a clear margin |
| Strongest against an opponent entering tight regions | **CONFIRMED** | `adversarial_corner` 0.135 [0.109, 0.160], N=713 |
| Raising the barrier quota changes nothing | **CONFIRMED** | `grid7` and `grid7-quota22` remain identical; the quota is not the binding constraint |
| A longer horizon changes nothing | **CONFIRMED** | `grid9` and `grid9-horizon45` remain identical in win rate |
| Win rate falls as the board grows | **WEAKENED** | 0.075 → 0.064 → 0.042; the 7 and 9 intervals overlap, so only the 11 drop is clearly separated |
| Zero captures on the Appendix F example geometry | **INSUFFICIENT_N** | still 0.000, but **N = 9**, not 1008 — this is a reference observation, not a statistical finding |
| Overall win rate near the floor | **CONFIRMED, revised upward** | 0.064 rather than 0.053; still weak, and still the side worth improving |

**Thief `NO_CHANGE` reassessment.** The corrected figure is 0.9886 over 4,988
independent scenarios, with the two barrier-using families at 0.950 and 0.971 on
N=713 each. The coverage is ample and the conclusion is unchanged:
**`NO_CHANGE` stands.**

## 15. Candidate hypotheses for Stage 9B-1 — police only

Ranked by expected benefit against evidence support, implementation risk,
latency risk and overfitting risk. **None is implemented, and none may be until
this stage has supervisory PASS.**

**Evidence policy (Stage 9B-0F).** Every hypothesis below rests only on
`development`, `validation` and source/domain reasoning. **None uses
`final_holdout`, because no final-holdout outcome exists** — the sealed set has
been enumerated and committed but never played. All five survive the corrected
numbers; only their supporting rows changed.

| # | Hypothesis | Evidence | Benefit | Risk |
|---|---|---|---|---|
| 1 | **Belief-directed pursuit**: add a term that reduces distance to the strongest lawful evidence, instead of only maximising own reachability | findings 1, 2, 5 — the policy has no target term at all | high | low latency (BFS already computed); moderate design risk |
| 2 | **Mobility denial**: prefer placements that cut the evader's reachable region rather than only those the evidence directly supports | findings 2, 3 — the quota is unspent and evaders thrive on region | high | must not weaken the existing strict admission gate |
| 3 | **Spend the quota**: relax the placement admission when a large quota remains late in the horizon | finding 3 — 3.4 of 14 spent | medium | irreversible placements; needs a regression guard |
| 4 | **Board-size-aware weighting**: scale the evidence threshold with board area | finding 5, now **WEAKENED** — the 7 and 9 intervals overlap | low-medium | highest overfitting risk: three grid sizes, one clear separation |
| 5 | **End-game trap completion**: prefer placements that complete a `GAME-005` enclosure | capture is only ever `BAR-003` or `GAME-005` | medium | narrow applicability |

Candidate 4 carries the highest overfitting risk and should be attempted last,
if at all. Candidates 1 and 2 are the ones the evidence actually points at.
