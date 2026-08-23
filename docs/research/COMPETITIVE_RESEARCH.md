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

## 16. Stage 9B-1A — police candidate exploration on DEVELOPMENT only

**Scope, stated before the numbers.** Everything in this section is measured on
`development` scenarios. No candidate has been run on `validation`, none on
`stress`, and the sealed `final_holdout` has not been opened, parsed or played.
No candidate has been promoted: `composition.py` still builds
`CompetitiveStrategy(baseline=BaselineStrategy())`, unchanged from the entry
commit. Promotion gates C and E in §9 are therefore **not satisfied and not
claimed** — they require the promotion and holdout sets, which belong to a later
stage.

### 16.1 The mechanism first, not a parameter search

The §15 hypotheses name *what* to try; they do not say *why* the shipped policy
underperforms. So the belief state was instrumented before any candidate was
written (`research/diagnostics.py`, committed output
`results/candidates/belief.json`).

The shipped barrier gate admits a placement only when its support **strictly
exceeds** the evidence at the cell the mover was already stepping onto. Measured
over `grid9`, twelve games per family:

| family | belief steps | gate blocked | blocked share | mean landing evidence |
|---|---|---|---|---|
| `adversarial_corner` | 375 | 334 | **0.891** | **0.822** |
| `center_mobility` | 345 | 27 | 0.078 | 0.206 |
| `random_legal` | 343 | 28 | 0.082 | 0.098 |
| `pursuit` | 408 | 24 | 0.059 | 0.077 |
| `evasive` | 408 | 22 | 0.054 | 0.074 |
| `scent_aware` | 377 | 4 | 0.011 | 0.072 |
| `barrier_aware` | 375 | 0 | 0.000 | 0.011 |

> **Corrected at Stage E-0. The table above is what the instrument reported, and
> it stopped being true at Stage 9B-2.** `research/diagnostics.py` kept its own
> copy of the gate - "no target's support strictly exceeds the landing cell" -
> and its docstring called that "the shipped gate's own test". Stage 9B-2
> replaced that rule with an absolute floor and the diagnostic was never
> updated, so from that commit onward it measured a gate this repository does
> not ship. The numbers above remain correct **for Stage 9B-1A**, which is why
> they are kept: they are what the candidates were actually built from.
>
> The instrument now asks the policy what it decided instead of restating the
> rule beside it, and separates a *gate refusal* from a decision where the board
> offered no lawful target at all - "did not place" has three causes and only
> one of them is the gate. Re-measured against the **shipped** absolute floor,
> same configuration, same sampling:
>
> | family | belief steps | starved | gate refused | share |
> |---|---|---|---|---|
> | `evasive` | 408 | 0 | 394 | 0.966 |
> | `pursuit` | 408 | 0 | 394 | 0.966 |
> | `barrier_aware` | 375 | 0 | 356 | 0.949 |
> | `scent_aware` | 408 | 0 | 378 | 0.926 |
> | `random_legal` | 343 | 0 | 302 | 0.880 |
> | `center_mobility` | 317 | 0 | 277 | 0.874 |
> | `adversarial_corner` | 285 | 1 | 232 | 0.817 |
>
> The shape of the finding **inverts**. Under the old rule one family was
> blocked and six were not; under the shipped floor the gate refuses 82-97% of
> belief-carrying decisions in *every* family, and `adversarial_corner` is now
> the *least* blocked rather than the most. `starved` is ~0 throughout, so this
> is the gate refusing and not the board running out of targets.
>
> This does not retract any Stage 9B-1A or 9B-2 result. Those measured game
> outcomes, not this counter, and the promotion rested on paired deltas across
> development, validation, stress and a sealed holdout. What it retracts is the
> *explanation* that survived into the shipped code's own documentation.

This **partly refuted the assumption behind hypothesis 3**. The quota is not
unspent because the policy is timid in general; against six of seven families the
gate almost never blocks. It is blocked almost always in exactly the one family
where the police is *already next to a well-located evader* — because the same
policy has just walked onto the hottest cell, and the gate then compares the
candidate placement against that cell. A hot landing square is **evidence to
act**, not a reason to abstain. That is a defect in the comparison, not in the
threshold, and it is what the candidates were built to test.

### 16.2 Candidates — all four, including the two that lost

Each is one conceptual change, frozen with its revision and the SHA-256 of its
source before it was run (`research/candidates/registry.py`).

| # | name | change | why it was askable |
|---|---|---|---|
| C1 | `C1-pursuit` | belief-directed mover, shipped barrier gate | hypothesis 1, alone |
| C2 | `C2-denial` | C1's mover **+** belief-valued barrier rule at 0.9 | hypotheses 1+2 together |
| C3 | `C3-pressure` | same rule at 0.3 | tests whether more aggression helps |
| C4 | `C4-ablation` | **shipped** mover + the same rule at 0.9 | C1–C3 cannot say which half of C2 works |

**Three numeric variants at most, and only two were used**: 0.9 and 0.3. Both are
anchored to the Appendix F Table 16 FIXED source strength (0.9) rather than
fished for, and both were frozen before any candidate was run. No threshold was
adjusted after seeing a result, and no per-grid weighting was implemented —
hypothesis 4 remains untried, deliberately, as the highest overfitting risk.

### 16.3 Screening — membership frozen before any candidate ran

`screen-v1`, 220/1000 of scenario ids by digest, giving **N = 471** unique
scenarios (21.0% of development), digest `6a22fc7d…`, all 7 families and all 6
configurations present. Membership is a function of the scenario id alone, so no
outcome can influence it. Baseline wins on that subset: 23.

| # | delta | 95% paired CI | wins | gains / losses | barriers | verdict |
|---|---|---|---|---|---|---|
| C1 | **−0.0488** | [−0.0679, −0.0318] | 23 → 0 | 0 / 23 | 3.40 → 0.40 | **rejected — collapse** |
| C2 | +0.0510 | [+0.0234, +0.0786] | 23 → 47 | 33 / 9 | 3.40 → 3.23 | not advanced |
| C3 | +0.0234 | [−0.0021, +0.0510] | 23 → 34 | 27 / 16 | 3.40 → 3.20 | **rejected — interval includes zero** |
| C4 | **+0.0722** | [+0.0446, +0.1019] | 23 → 57 | 42 / 8 | 3.40 → 3.17 | **advanced** |

**What the negative results actually establish**, and why they are kept:

* **C1 refutes hypothesis 1 as an isolated change.** A belief-directed mover
  *alone* does not merely fail to help, it destroys the policy: every one of the
  23 baseline wins is lost. Chasing the evidence walks the police onto the hot
  cell, which — via the gate measured in §16.1 — suppresses the barrier placements
  the wins were actually made of. Barrier use falls 3.40 → 0.40.
* **C3 refutes "spend more of the quota" (hypothesis 3).** Lowering the floor to
  0.3 is *worse* than 0.9, and its interval includes zero. Both C2 and C3 place
  **fewer** barriers than the baseline, not more. The gain does not come from
  spending more quota; it comes from spending it on better-valued targets.
* **C4 reverses the ranking C2 suggested.** Running the same barrier rule behind
  the **shipped** mover beats running it behind the new one. So the mover change
  is not merely unnecessary, it costs about 2 percentage points. Without this
  ablation the stage would have advanced C2 and attributed the gain to the wrong
  half of the change.

### 16.4 Full development set — the advancing candidate only

C4 over the whole development set, paired on identical `scenario_id`s,
**N = 2,247** unique scenarios:

| metric | baseline | C4 |
|---|---|---|
| wins | 126 | **261** |
| mean barriers placed | 3.28 | 2.99 |
| paired delta | — | **+0.0601, 95% CI [+0.0467, +0.0748]** |
| gains / losses | — | 187 / 52 |

**The full-set estimate is lower than the screening estimate** (+0.0601 against
+0.0722), which is the expected direction: the subset that selected the candidate
flatters it. The full-set number is the one that carries forward.

| family | delta | | configuration | delta |
|---|---|---|---|---|
| `adversarial_corner` | **+0.1776** | | `grid7` | +0.0759 |
| `barrier_aware` | +0.0623 | | `grid7-quota22` | +0.0759 |
| `pursuit` | +0.0623 | | `grid11` | +0.0647 |
| `center_mobility` | +0.0561 | | `grid9` | +0.0402 |
| `evasive` | +0.0498 | | `grid9-horizon45` | +0.0402 |
| `scent_aware` | +0.0280 | | `appendixF-example` | +0.2857 (N=7) |
| `random_legal` | **−0.0156** | | | |

The largest family gain is exactly where §16.1 predicted it: `adversarial_corner`,
the family the gate was blocking 89% of the time.

**One family regresses.** `random_legal` falls 1.6 percentage points. Against the
§9 material-regression definition — more than **5** points *and* an interval
excluding zero — this is **not a material regression**. It is reported rather
than dropped, and it is the specific thing the validation stage must re-check,
because a regression against a random opponent is the signature of a policy that
has learned the shape of the *modelled* opponents.

### 16.5 Latency

Measured at `choose_action` on `grid9` (the board the committed baseline number
was measured on) and on `grid11` (the largest legal board, the worst case).
Committed output: `results/candidates/latency.json`. Wall-clock timings move a
few percent between runs; the ceiling is an order of magnitude away, so the
conclusion does not depend on which run is quoted.

| candidate | grid9 p95 | grid11 p95 | ceiling |
|---|---|---|---|
| baseline (9B-0) | 3.61 ms | — | 25 ms |
| C1 | 2.32 ms | 3.38 ms | 25 ms |
| C2 | 2.18 ms | 3.36 ms | 25 ms |
| C3 | 2.25 ms | 3.32 ms | 25 ms |
| **C4** | **2.32 ms** | **3.40 ms** | 25 ms |

Every candidate, including the rejected ones, is inside the ceiling; gate F in
§9 is satisfied for C4 on development evidence.

### 16.6 What leaves this stage

**One candidate: C4.** It dominates C2 on delta, on interval, on gains-to-losses
and on implementation surface — it needs no change to the mover at all. C2 is not
kept as a hedge, because C2 and C4 share the barrier rule and are therefore
highly correlated: they would fail together.

**C4 is not promoted.** It is a development-only research result. Gates C, D
(re-check on the promotion set), E and I are unevaluated by construction.

### 16.6a One correction made before publishing

`compare.replay` stamped each replayed row with the **baseline's** strategy name
and hash, so every candidate CSV filed its own games under `CompetitiveStrategy`.
The identity is now a required argument rather than an inherited field, and all
candidate result files were regenerated. The correction is labelling only: every
delta, interval, win count and barrier mean above is identical before and after.

### 16.7 Reproduction

```bash
uv run python -m research.candidate_main screen   --out results
uv run python -m research.candidate_main full     --candidate C4 --out results
uv run python -m research.candidate_main latency  --out results
uv run python -m research.candidate_main belief   --out results
uv run python -m research.candidate_main figures  --out results
```

Figures: `results/figures/candidates/candidate_delta.png` and
`exploration_progression.png`, both labelled **DEVELOPMENT RESEARCH / NOT FINAL
HOLDOUT / NOT PRODUCTION PROMOTION**. The progression figure plots one point per
candidate in the order tried, with the rejected points kept and marked. It is
**not a learning curve**: nothing is trained, the x axis is exploration order,
and the y axis is a paired win-rate difference against a frozen baseline.

## 17. Stage 9B-1B — C4 on VALIDATION and STRESS, then frozen

**Scope.** The candidate that left 9B-1A is evaluated here on two banks it was
never tuned on. Its source was frozen **before the first validation game**, and
the freeze is checked in code: `research.validation.evaluate` refuses to run
unless C4's source hash still equals `1cc0a20d…`, the hash its development
evidence was produced with. The sealed final holdout was not opened, parsed or
played; nothing was promoted to production.

### 17.1 The frozen candidate

| | |
|---|---|
| candidate | `C4-ablation`, revision `r1` |
| source | `research/candidates/denial.py`, SHA-256 `1cc0a20d40680874a337dd3f7f2e552924763e42f291066990cb0dc8385c2884` |
| parameters | `threshold = 0.9` (the Appendix F Table 16 FIXED source strength), `TRAP_BONUS = 10` |
| formula | `value(t) = belief[t] + Σ belief[c]·TRAP_BONUS if placing traps c + Σ belief[c] if t adjoins c`; place the best `t` when `value ≥ threshold`, else the **shipped** mover |

### 17.2 Bank identities, pinned before C4 ran

| bank | file | unique scenarios | manifest digest |
|---|---|---|---|
| DEVELOPMENT | `games_development.csv` | 2,247 | `56717b3e…` |
| VALIDATION | `games_holdout.csv` | **2,219** | `b90267e5…` |
| STRESS | `games_stress.csv` | **567** | `304de01e…` |

Both working banks carry all 7 opponent families and all 6 configurations
(validation 317 per family; stress 81 per family).

### 17.3 Validation result — N = 2,219

| metric | baseline | C4 |
|---|---|---|
| wins | 160 | **302** |
| mean barriers | 3.378 | 3.186 |
| paired delta | — | **+0.0640, 95% CI [+0.0500, +0.0771]** |
| gains / losses | — | 191 / 49 |

**Every opponent family improved.** No family and no configuration shows a
negative point estimate at all, so the material-regression question does not
even arise on this bank.

| family | delta | 95% CI | | configuration | delta |
|---|---|---|---|---|---|
| `adversarial_corner` | **+0.1514** | [+0.0978, +0.2082] | | `grid9` | +0.0670 |
| `evasive` | +0.0726 | [+0.0473, +0.1009] | | `grid9-horizon45` | +0.0670 |
| `barrier_aware` | +0.0694 | [+0.0410, +0.1009] | | `grid11` | +0.0625 |
| `pursuit` | +0.0694 | [+0.0347, +0.1041] | | `grid7` | +0.0599 |
| `center_mobility` | +0.0631 | [+0.0252, +0.1009] | | `grid7-quota22` | +0.0599 |
| `scent_aware` | +0.0158 | [−0.0063, +0.0379] | | `appendixF-example` | +0.2857 (N=7) |
| `random_legal` | +0.0063 | [−0.0189, +0.0347] | | | |

`appendixF-example` has **N = 7**, below the bootstrap minimum, so it carries no
interval and is reported as an observation rather than a finding.

### 17.4 The predeclared `random_legal` risk

Development measured **−0.0156** against `random_legal` and this stage recorded
that number *before* running validation. On validation the same family measures
**+0.0063**, 95% CI [−0.0189, +0.0347], on N=317 with 12 gains against 10
losses; on stress it measures **−0.0123**, CI [−0.0741, +0.0494], on N=81.

Applying the **same** frozen rule (a drop of more than 5 points *and* an
interval excluding zero) to all three banks: **NO_CONFIRMED_REGRESSION.** The
development sign did not reproduce, both later intervals contain zero, and every
point estimate is an order of magnitude inside the material threshold. No
special `random_legal` rule was written, and the threshold was not redefined.

### 17.5 Development versus validation

| bank | N | delta | 95% CI |
|---|---|---|---|
| DEVELOPMENT | 2,247 | +0.0601 | [+0.0467, +0.0748] |
| VALIDATION | 2,219 | **+0.0640** | [+0.0500, +0.0771] |
| STRESS | 567 | **+0.0935** | [+0.0670, +0.1235] |

Classification: **REPLICATED.** The intervals overlap heavily and validation did
not shrink the estimate — which is worth stating plainly rather than
celebrating, because the expected direction was a *smaller* number and the
honest reading is that development was not optimistic here, not that C4 got
better.

### 17.6 Stress result — N = 567

Wins 32 → **85**, gains/losses 64 / 11, delta **+0.0935**, CI [+0.0670,
+0.1235]. Six of seven families improve; `random_legal` is the only negative
point estimate (−0.0123) and its interval contains zero. Barrier use is
essentially unchanged (3.402 → 3.407). No deterministic failure mode appeared:
zero illegal actions, and every game reached a natural terminal.

### 17.7 Gate audit

Applied by `research/gates.py`, which is the only place these rules exist as
code. On **both** banks: A zero legality failures · C positive delta · D lower
bound above zero · E no material family regression · F no material config
regression · G latency inside the ceiling · I candidate hash unchanged — **all
pass**, with an empty material-regression list.

**Gate H (not concentrated in one sparse cell)** is assessed by reading rather
than by a threshold: on validation, five of seven families improve with intervals
excluding zero, and all six configurations improve, five of them with intervals
excluding zero. The gain is broad, not one lucky cell. **Gate B** (source and
privacy) holds by construction — a candidate sees only `Observation`, and the
structural tests that forbid a candidate naming a hidden field are unchanged.

Legality is not merely asserted: every research game is adjudicated by the same
`Replay` engine the live audit uses, and an illegal action raises rather than
scoring, so a completed run *is* the zero-failure evidence.

### 17.8 Latency

The frozen source hash is unchanged from the measurement committed at 9B-1A, so
that measurement stands for this revision: p50/p95/max **2.19 / 2.32 / 3.64 ms**
on `grid9` (N=213) and **3.28 / 3.40 / 4.51 ms** on `grid11` (N=210), against
the frozen **25 ms** ceiling. Re-measuring an unchanged source would produce a
new number for the same thing.

### 17.9 Decision

**C4 = VALIDATED.** It is frozen in `results/candidates/freeze_C4.json`, which
pins the source hash, the three manifest digests, the three result digests, the
latency digest and the seal metadata, and records
`final_holdout_evaluated: false` and `production_promotion: false`. That is the
exact candidate Stage 9B-2 may evaluate **once**.

**C2 was not evaluated.** It is the only permitted fallback and it stays
archived and untouched, because the fallback is defined to trigger only on a C4
gate failure.

### 17.10 Evidence vocabulary corrected

Stage 9B-1A wrote a binary verdict, so C2 — which beat the baseline by +0.0510
with an interval excluding zero, and lost the *selection* to a stronger
candidate — was recorded with the same word as C1, which lost every game it had
won. Those are different research outcomes. The vocabulary is now three-valued
in `research/gates.py`: **ADVANCED**, **NOT_ADVANCED**, **REJECTED_GATE**, and
`verdict_for` refuses the impossible combination (selected while failing a gate).
Every historical number is unchanged; only the label is.

### 17.11 Reproduction

```bash
uv run python -m research.candidate_main validation --out results
uv run python -m research.candidate_main stress     --out results
uv run python -m research.candidate_main freeze     --out results
uv run python -m research.candidate_main figures    --out results
uv run python -m research.candidate_main evidence   --out results
```

Figures: `c4_by_bank.png`, `c4_validation_family.png`, `c4_stress_family.png`
and `strategy_research_progression.png`, all labelled **VALIDATION / STRESS
RESEARCH EVIDENCE — NOT FINAL HOLDOUT — NOT YET PRODUCTION**. The progression
keeps every rejected candidate visible and is **not** a learning curve: nothing
is trained, and the x axis is the order things were evaluated.

## 18. Stage 9B-2 — the one-shot final holdout, and promotion

### 18.1 What was sealed, and that it had not moved

Before a single sealed scenario was played, the current state was checked
against the Stage-9B-1B freeze record: seal file SHA `206ee57b…`, commitment
`99bd72e1…`, count **2,226**, `results_present: false`, candidate source
`1cc0a20d…`, freeze record digest `6b82388e…`. All matched. Production still
built the pre-promotion strategy and no final-holdout result existed.

### 18.2 One shot, enforced rather than promised

The evaluation lives behind its own module and its own explicit confirmation
(`python -m research.final_main --i-am-consuming-the-final-holdout`) so no
`all`, default or habit can reach it. Before anything is played the runner
refuses if a result already exists, if the seal reports results, if the
commitment differs, if the candidate hash has moved, or if re-enumerating the
sealed scenarios fails to reproduce the committed commitment. Publication is
atomic and refuses to overwrite. Every one of those refusals is tested **on fake
seals only** — a security test that opened the holdout to prove it was closed
would consume the thing it protects.

There was no preview, no sample and no dry run. The first performance evaluation
against the sealed set is the one reported here, and the second-run refusal was
then demonstrated against the real directory.

### 18.3 The result — N = 2,226, one shot

| metric | baseline | C4-ablation r1 |
|---|---|---|
| wins | 153 | **312** |
| win rate | 0.068733 | **0.140162** |
| mean barriers | 3.247 | 3.168 |
| paired gains / losses / unchanged | — | **196 / 37 / 1,993** |
| paired delta | — | **+0.071429** |
| 95% CI | — | **[+0.059299, +0.086253]** |
| legality failures | 0 | 0 |

Result digest `0d23b0c708306717460289c3a4561f04be9747d4d48e5d80c53230daf2ce599d`.

**Every opponent family improved**, each with an interval excluding zero:

| family | N | baseline | C4 | delta | 95% CI |
|---|---|---|---|---|---|
| `adversarial_corner` | 318 | 46 | 91 | **+0.1415** | [+0.0912, +0.1981] |
| `center_mobility` | 318 | 32 | 69 | +0.1164 | [+0.0723, +0.1572] |
| `pursuit` | 318 | 16 | 44 | +0.0881 | [+0.0472, +0.1226] |
| `evasive` | 318 | 4 | 25 | +0.0660 | [+0.0409, +0.0943] |
| `random_legal` | 318 | 28 | 41 | **+0.0409** | [+0.0094, +0.0723] |
| `barrier_aware` | 318 | 20 | 30 | +0.0314 | [+0.0157, +0.0535] |
| `scent_aware` | 318 | 7 | 12 | +0.0157 | [+0.0000, +0.0314] |

Every configuration improved: `grid7` and `grid7-quota22` +0.0726, `grid9` and
`grid9-horizon45` +0.0714, `grid11` +0.0658, each with an interval excluding
zero. `appendixF-example` is **N = 7** — a sparse reference cell reported
separately and given no statistical weight.

**`random_legal`, the risk predeclared at 9B-1A, is resolved.** It measured
−0.0156 on development, +0.0063 on validation, −0.0123 on stress and **+0.0409
with an interval excluding zero** on the sealed set. Under the unchanged frozen
rule it was never a material regression, and the final evidence is positive.

**Gate I** — the gain is not one opponent's doing: 7 of 7 families improve, and
the two weakest baseline families (`evasive` at 4 wins, `scent_aware` at 7)
both improve rather than being traded away.

**Decision: FINAL_HOLDOUT_PASS.** Every frozen gate in §9 holds.

### 18.4 Promotion — the same behaviour, not a new interpretation

`CompetitiveStrategy` keeps its name, its mover and its legality sources; only
the scoring and the gate changed, which is the smallest change that makes
production semantically equal to C4. Production imports nothing from `research/`.

| | SHA-256 |
|---|---|
| old production strategy | `655ca8576130bbd3fcaa3f1b8de9a0f7e47a2f055dde0d2fb1bef90e7b169331` |
| new production strategy | `c7f5584ff8ade44fd3f1ef7c8e3d3c2ee796f24b3671252b7a555485a74ff598` |
| frozen research C4 | `1cc0a20d40680874a337dd3f7f2e552924763e42f291066990cb0dc8385c2884` |

The hashes differ because the code lives in different modules with different
prose. **Behavioural equivalence is the requirement, and it is proved**, not
asserted: identical actions across an exhaustive 5×5 matrix of every actor cell
× every single-source belief cell × five intensities (**3,125 states**), across
four wall/trap layouts, and identical outcome, step count, barrier count and
score on committed development, validation and stress scenarios. **The sealed
set was not replayed** — it is consumed, and the result above belongs to the
frozen candidate that production is proved equal to.

Two shipped tests changed behaviour rather than being deleted, and both are
recorded as intended consequences: a synthetic **uniform** belief field now
funds a placement (an expectation over many believed cells is genuinely large,
and a uniform field is unreachable under the Table 16 radial kernel), and the
**landing cell no longer enters admission at all** — which was the defect.

### 18.5 Latency after promotion

Measured at the `StrategyPort` surface: `grid9` p50/p95/max **2.17 / 2.28 /
2.90 ms** (N=213); `grid11` **3.20 / 3.34 / 4.17 ms** (N=210). Ceiling 25 ms.
Within noise of the frozen research C4 measurement, as equivalence implies.

### 18.6 One defect the promotion exposed, found by CI

The first push failed all three gating jobs with a semantic verdict of
**`ILLEGAL_ACTION`** in the two-process and in-process series proofs. The fault
was recorded against the **thief**, not the police, and the cause was a harness
flaw the promotion made visible rather than created.

Both integration harnesses gave *this* repository's composed policy to the
**thief-role** side. This is the police agent, so that policy may place a
barrier - and `BAR-004` gives placement to the police alone, so the semantic
review correctly refused it. The rule this replaced almost never admitted a
placement in those positions, so the flaw had never surfaced.

**The promoted rule itself is not implicated**: 264 research games with it
produced zero illegal actions, and the recorded fault is the thief's.

A first attempt fixed this in `compose_agent` by selecting the strategy from the
role. That was **wrong and was reverted**: `test_the_composition_carries_no_role_branch`
freezes composition as role-symmetric, because each repository ships the policy
for its own role and the two repositories' production code stays identical. The
correct fix is in the harnesses, which now let the thief stand-in play
`BaselineStrategy` - the sibling repository's frozen, never-placing thief policy,
which is what a real counterparty runs. No assertion was relaxed: both proofs
still require six `CONSISTENT` audits and the exact fourteen artifacts.

**A process failure of mine is recorded with it.** The local gate run before
that push was reported green on the strength of a grep for pytest's summary
line rather than its exit status, and two failures went unseen. The gate command
now checks `PYTEST_EXIT` explicitly.

### 18.7 What this does and does not claim

C4 is a **validated improvement across this project's frozen legal benchmark
corpus**, confirmed by a single pre-committed holdout evaluation. It is not a
guarantee of winning any particular match. The external opponent is unknown, the
corpus is our own construction, and the seven opponent families are models
rather than the field.

## 19. Stage E — a second cycle, and what the corrected instrument changed

**Written before any v2 candidate was run.** Everything in this section that is a
*number* is either from Stage 9B or from the corrected diagnostic; no v2 outcome
exists at the time of writing, the v2 holdout is sealed and unopened, and
`composition.py` still builds the promoted Stage 9B-2 policy.

### 19.1 Why a second cycle exists at all

The Stage 9B-2 holdout is **spent**. A frozen candidate was evaluated against it
exactly once and the one-shot result is committed, so it can decide nothing
further — §9 already froze the rule that a consumed holdout does not become blind
again by being reused. A second cycle therefore gets a second sealed set:

| | |
|---|---|
| namespace | `mars777-research/final-holdout-v2/` |
| bank | `final_holdout_v2` |
| seeds | `34bddb9b9c24e387d73e40439ca0ba7a946957654860384f630f5d0a2a826ae1` |
| commitment | `5bf90845113384c6364d24f9216a0e74f01986ab74b9b4c7f5dd2b0ffe72a787` |
| scenarios | 2181 |
| sealed at | stage-E-0, before any v2 candidate existed |

A fresh namespace does **not** by itself produce a blind set, and this nearly
went unnoticed. `scenario_id` covers the family, the configuration and both
opening cells, so a configuration whose legal opening space is finite yields the
same scenarios however the seeds are drawn — `appendixF-example` has exactly one
opening. Enumerating v2 reproduced **66** scenarios the spent v1 evaluation had
already played. They are excluded before any candidate exists and the count is
recorded in the manifest, because a holdout is not "mostly blind".

### 19.2 The evidence this cycle rests on is *new*, not a re-reading

§16.1's mechanism table described the pre-9B-2 gate. That gate no longer exists,
and the instrument that measured it was never updated — see the correction boxed
in §16.1. Against the **shipped** absolute floor the finding inverts: the gate
refuses **82–97%** of belief-carrying decisions in *every* family, and
`adversarial_corner` — the family the entire 9B-1 search was built around — is
now the **least** blocked rather than the most, with `starved` ≈ 0 throughout.

That is the new fact. `CONSERVATIVE = 0.9` was chosen when it was a *comparison*
baseline — "act when the expected evidence is worth a full emission at its
source". Stage 9B-2 changed the gate's **structure** to an absolute floor and
carried the same number across. **The level has never been measured under the
structure it now serves.** That is a specific, evidence-driven question, not a
parameter search.

### 19.3 Candidates — frozen here, before any of them ran

Three, and no more. Two are threshold levels behind the **shipped** mover; one is
the §15 hypothesis that was never implemented.

| # | Candidate | Change | Why this value, and not a fitted one |
|---|---|---|---|
| V1 | `V1-floor-decay` | shipped rule, floor **0.81** | `0.9 × (1 − 0.10)` — one decay step from a source emission. The book's own recurrence, and exactly the value `DECAY_EXAMPLE` carries. |
| V2 | `V2-floor-adjacent` | shipped rule, floor **0.62** | The Figure-4 kernel weight at an orthogonally adjacent cell — the evidence a cell one step from an emission actually carries. |
| V3 | `V3-mobility` | §15 hypothesis 2 | Prefer placements that cut the evader's reachable region, not only those the evidence directly supports. Never implemented; the only structural candidate here. |

Both thresholds are **anchored to numbers the source already fixes**, in the same
way §16 anchored 0.9 and 0.3, and both are declared here before any of them ran.
`0.3` is deliberately not retried behind the shipped mover: C3 measured it and
its interval included zero, and re-rolling an inconclusive number until it
separates is the failure this methodology exists to prevent.

**What is deliberately not attempted.** §15 hypothesis 4 (board-size-aware
weighting) remains untried, for the reason it was ranked last: three grid sizes
and one clear separation is the highest overfitting risk on the list, and the
9B-0F correction already **weakened** the trend it rested on.

### 19.4 The rules, unchanged

Every gate is §9's, applied from `research/gates.py` as before: the material
regression rule (>5 points **and** an interval excluding zero), the three-valued
verdict vocabulary, scenario-level units, paired comparison keyed by
`scenario_id`, screening membership frozen by digest. Nothing in this section
redefines a threshold, and no gate is relaxed for a v2 candidate.

**The predeclared risk, written down before the numbers.** Lowering an admission
floor spends more of the quota, and §16 already measured that spending *more* is
not by itself a gain. If a lower floor helps, the mechanism must be visible as
better-valued placements rather than merely more of them, so barrier counts are
reported for every arm. A candidate that wins only by placing more is the
signature of a policy fitted to modelled opponents, and it is named here in
advance as the thing validation must re-check.

