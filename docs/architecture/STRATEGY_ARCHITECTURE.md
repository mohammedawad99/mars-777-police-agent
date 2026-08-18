# Strategy Architecture — group MaRs-777 (POLICE)

**Status: BOUNDARY FROZEN AT STAGE 2A; BASELINE IMPLEMENTED AT STAGE 6B;
COMPETITIVE POLICY PROMOTED AT STAGE 7D-B.** This document still defines
**where strategy plugs in**, not what it decides — the boundary below is
unchanged, and `StrategyPort` has never changed shape.

Two policies now exist behind that one seam. `BaselineStrategy` is the **frozen
reference**: it is still shipped in the tree, is the regression oracle for every
no-evidence corpus, and is what the competitive policy is measured against.
`CompetitiveStrategy` is what production composes (`composition.py`, one
construction site), and it is **PROJECT-DERIVED / OPTIONAL COMPETITIVE
STRATEGY** — the source mandates no algorithm, this is not Bayes, not learning,
and not a claim of optimality.

**What it adds.** BAR-004 lets the police forgo its move to place a barrier, an
action the baseline never used. `CompetitiveStrategy` keeps the baseline's move
as the decision and lets a placement displace it only when the lawful scent
evidence supporting the placement is *strictly stronger* than the evidence at
the cell the baseline would have moved to. Support is the stronger of the
evidence on the target itself (BAR-003 captures a thief standing there) and the
evidence on any cell the placement would newly corner (GAME-005). Empty,
uniform or equal evidence reproduces the baseline exactly.

**What it never does.** It creates no `CaptureClaim`: a wrong same-cell
declaration is a `FALSE_CAPTURE_CLAIM` technical loss for the claimant, while a
legal barrier that simply misses produces no finding at all — belief may fund a
barrier, never a declaration. It enumerates candidates only through
`is_placeable` and `legal_moves`, and `LocalTurnService` still revalidates.

The **thief** side deliberately ships the baseline: its candidate competitive
policy was implemented, benchmarked and **rejected** at Stage 7D-B for failing
its promotion gate.

## 1. The boundary

```
   domain.observation ──► Observation ──► [ StrategyPort ] ──► ProposedAction
                                              (plug-in)              │
                                                                     ▼
                                                    domain.rules  (deterministic validator)
                                                                     │ accept / reject
                                                                     ▼
                                                    app.turn_service (commits the action)
```

**One seam, one contract.** A strategy is any component satisfying `StrategyPort`.
Replacing it must require **no change** to networking, cryptography, persistence, GUI,
Gmail, or protocol parsing (design principle 10).

## 2. Legal inputs — `Observation`

**Implemented at Stage 6B** in `domain/observation.py`, with exactly **three**
members — `board`, `own_position`, `quota` — frozen and slotted, built by the
pure `observation_of(truth, quota)`. That is a strict subset of the list below,
and deliberately so: Ch 10 §10.3.3 places a **blind** strategy at this stage,
*"blind in the sense that there is not yet scent, natural language or
deception"*, so scent readings, hints and belief arrive with PRD-04 rather than
sitting on the type unread. Adding a member is an additive change to a frozen
dataclass and changes neither `choose_action`'s signature nor the future game
owner's call site — the seam does not need the fields in advance.

The privacy guarantee is unchanged and is now structural rather than editorial:
there is **no field** an opponent cell, a peer nonce, a reveal or a final-audit
trajectory could arrive in, and a contract test asserts the field set exactly, so
a new member fails the build rather than passing review (`PRD03-AC-001`).

The full list below remains the long-term target:

- own true position, own step/turn, own remaining budget (barriers/moves);
- locked config values (board size, scoring, limits, scent parameters);
- public barrier set;
- own scent readings;
- **belief** over opponent position (explicitly typed as belief, with uncertainty);
- validated opponent-supplied public data (revealed moves, hints, `intent` after reveal);
- score state and clock budget remaining.

**Never contains** opponent true position, opponent nonce, opponent pre-reveal move,
key material, or any transport handle. The type has no field for them.

## 3. Legal output — `ProposedAction`

- a **proposed** legal action (move or, for police, barrier placement / forgo move);
- optional hint text (within `hint_max_words`) and its `intent` truth/lie classification;
- optional confidence/diagnostics for metrics.

It is a **proposal**: authority to change state belongs to `app.turn_service` **after**
`domain.rules` validates it. A rejected proposal triggers a deterministic fallback.

**Stage-6B form.** `choose_action` returns the domain's existing `PhysicalAction`
union **bare**. Hint text and `intent` are PRD-04's, and Ch 6 Figure 7 runs the
dependency that way round — *"the language model receives the movement decision
as a given fact"* — so the future owner **composes** a physical strategy with a
language policy rather than hiding one inside the other. `ProposedAction` keeps
its name for that composition. No fallback ladder exists yet: the baseline is
total over `legal_moves`, so its only failure mode is an empty candidate set,
which is a terminal the caller settles before asking (App E #47).

## 4. Strategy MUST NOT

| Forbidden | Enforced by |
|---|---|
| Send network messages | no transport import (DEPENDENCY_RULES §3) |
| Write result JSON / touch artifacts | no `infra` import |
| Manipulate nonce or hashes | `CommitmentPort` not reachable from strategy |
| Mutate authoritative state | receives values; returns a proposal |
| Bypass legality validation | validator sits between proposal and effect |
| Read forbidden opponent truth | `Observation` has no such field |
| Depend on wall-clock beyond its budget | `ClockPort` injected, bounded |

## 5. Determinism and seeding

- Strategies are **deterministic given a seed**: same seed + same `Observation` sequence
  ⇒ same decisions. The seed is recorded as evidence for replay.
- Randomized/mixed strategies draw from a **seeded** RNG owned by the strategy, never
  from global randomness.
- A **time-boxed** decision: exceeding the step budget yields a deterministic default
  (a legal, safe action), never a protocol violation.

## 6. Optional LLM augmentation

Strategy may consult `LlmAdvisorPort` for *language* (hints/bluffs) and, only under the
locked documented mutual-agreement exception, for tactical suggestion. Any suggestion is
**advisory**: it enters as a `ProposedAction` and passes the same deterministic
validator. **Zero-token operation must remain fully viable** (`LLM_BOUNDARY.md`).

## 7. Role-specific capability space (future strategies must be expressible)

### POLICE strategy capabilities
- belief tracking over thief position from scent/hints;
- scent-gradient inference and source localization;
- trajectory prediction and interception planning;
- barrier/choke-point planning within quota, exploiting irreversibility;
- capture-by-barrier opportunities (BAR-003);
- opponent adaptation across the 6-sub-game series.

### THIEF strategy capabilities
- escape-risk evaluation and survival-horizon planning;
- police and barrier prediction (including choke-point avoidance);
- exit preservation — keeping escape routes open as barriers accumulate;
- trap avoidance under irreversible barrier growth;
- scent-aware movement and deception (legal lying via `intent`);
- opponent adaptation across the series.

**Both roles** share the same plug-in contract; only the action space and objective
differ. This repository implements the **POLICE** strategy; the THIEF
capability list is documented so this agent can *anticipate* and *validate*, never
simulate as authoritative.

## 8. Replaceability guarantees

- Multiple strategies coexist and are selected by local settings (kind 2 config).
- A baseline **deterministic, zero-token** strategy always exists as the fallback.
- Strategy changes require no protocol renegotiation and no artifact-format change.
- Strategy quality is measured via `OBSERVABILITY.md` metrics, not by touching game state.
