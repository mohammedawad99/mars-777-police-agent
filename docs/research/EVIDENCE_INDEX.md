# Research evidence index — Police

Every artifact behind the strategy claim, in the order the work happened. A
reader should never have to search the repository to check a number.

## Read these three first

| | what it answers |
|---|---|
| `docs/research/COMPETITIVE_RESEARCH.md` | the whole method and every result, §1–§18 |
| `notebooks/competitive_research.ipynb` | the same story as a narrated read-through |
| `results/figures/candidates/strategy_research_progression.png` | the entire search in one picture, rejections included |

## 1. Baseline and the correction that came before any candidate

| artifact | contents |
|---|---|
| `results/baseline/games_development.csv` | frozen-policy rows, development bank |
| `results/baseline/games_holdout.csv` | the bank reclassified as **validation** (its label stays `holdout` so committed rows still load) |
| `results/baseline/games_stress.csv` | stress bank rows |
| `results/tables/by_*.csv`, `overall.json` | grouped baseline tables |
| `results/figures/*.png` | eight baseline figures |
| `COMPETITIVE_RESEARCH.md` §6, §13 | the invalid first benchmark, and both the old and corrected headline (0.0526 → **0.0638**) |

## 2. The sealed holdout, fixed before candidates existed

| artifact | contents |
|---|---|
| `results/final_holdout.json` | seal only: commitment `99bd72e1…`, count 2,226, **370 bytes, no scenario list** |
| `COMPETITIVE_RESEARCH.md` §9 | promotion gates, frozen before any candidate |

## 3. Candidate exploration — including what failed

| artifact | contents |
|---|---|
| `results/candidates/belief.json` | the belief/gate diagnostic that redirected the study |
| `results/candidates/screen_C1…C4.csv` | every candidate's rows on the frozen screening subset |
| `results/candidates/screening.json` | screening summary, all four candidates |
| `results/tables/candidates/screening.csv` | the same as a table, with `ADVANCED` / `NOT_ADVANCED` / `REJECTED_GATE` |
| `results/figures/candidates/candidate_delta.png` | signed deltas on a real zero line |
| `results/figures/candidates/exploration_progression.png` | the search, rejections kept |

**The negative results are the point.** C1 lost every game the shipped policy
had won; C3's interval crossed zero; C2 won but lost the selection. None was
deleted.

## 4. Full development, validation, stress

| artifact | contents |
|---|---|
| `results/candidates/full_C4.csv` / `.json` | N=2,247, +0.0601 |
| `results/candidates/validation_C4.csv` / `.json` | N=2,219, +0.0640 |
| `results/candidates/stress_C4.csv` / `.json` | N=567, +0.0935 |
| `results/candidates/freeze_C4.json` | the freeze: source hash, three manifest digests, three result digests, seal metadata |
| `results/figures/candidates/c4_by_bank.png` | the same candidate across banks |
| `results/figures/candidates/c4_validation_family.png`, `c4_stress_family.png` | per-family detail |

## 5. The one-shot final holdout

| artifact | contents |
|---|---|
| `results/candidates/final_holdout_result.json` | **the single official result**: N=2,226, 153 → 312 wins, +0.0714 [+0.0593, +0.0863] |
| `results/figures/candidates/c4_final_holdout_family.png` | all seven families, all positive |
| `COMPETITIVE_RESEARCH.md` §18 | the ceremony, the refusals, the result, the promotion |

Evaluated **once**. The tooling refuses a second run for the same commitment and
candidate, and that refusal is demonstrated against the real directory.

## 6. Latency and sensitivity

| artifact | contents |
|---|---|
| `results/baseline/latency.json` | pre-promotion baseline timing |
| `results/candidates/latency.json` | all four candidates, two boards |
| `results/candidates/promoted_latency.json` | the promoted production strategy |
| `docs/research/SENSITIVITY.md` | board size, quota, horizon, opponent family, threshold, latency |

## 7. Promotion

| artifact | contents |
|---|---|
| `src/mars777_police/app/competitive_strategy.py` | the promoted rule |
| `tests/app/test_promoted_barrier_rule.py` | RED-first behavioural pins |
| `tests/research/test_promotion_equivalence.py` | 3,125-state matrix + whole games on three banks |
| `tests/composition_root/test_promoted_strategy_composed.py` | the really-composed agent decides identically |
| `docs/DECISIONS.md` D66–D68 | why C4, why the holdout is never rerun, what is and is not claimed |

## Regenerating all of it

```bash
uv run python -m research.bench_main all --out results          # baseline
uv run python -m research.candidate_main screen   --out results
uv run python -m research.candidate_main full     --candidate C4 --out results
uv run python -m research.candidate_main validation --out results
uv run python -m research.candidate_main stress   --out results
uv run python -m research.candidate_main freeze   --out results
uv run python -m research.candidate_main figures  --out results
uv run python -m research.candidate_main evidence --out results
```

There is deliberately **no command here that re-runs the final holdout.** It
lives behind its own module and an explicit confirmation flag, and it refuses to
run twice.
