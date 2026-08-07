# Strategy Architecture — group MaRs-777 (POLICE)

**Status: STAGE 2A ARCHITECTURE FREEZE — boundary design only. No strategy implemented.**
This document defines **where strategy plugs in**, not what it decides.

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

Contains **only** role-legal data (`ROLE_RESPONSIBILITIES.md` §2):

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
