# State Ownership — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

**Prime rule: exactly one authoritative owner per mutable state.** Every other
component holds a *read-only projection* or a *derived copy clearly marked derived*.
Duplicate mutable truth is an architecture defect.

Lifetimes: **SERIES** = whole 6-sub-game series · **SUBGAME** = one sub-game ·
**TURN** = one turn · **PROCESS** = process lifetime.

| State | Authoritative owner | Readers | Writers | Persistence | Reset boundary | Lifetime | Class |
|---|---|---|---|---|---|---|---|
| Immutable signed config | `protocol.config_lock` | all layers (read-only value) | **none after lock** | `config_<game_id>_g<NN>.json` | new sub-game negotiation | SUBGAME (locked) | PUBLIC |
| `config_sha256` / config auth tag | `protocol.config_lock` | orchestrator, logger, declaration | config_lock (once) | declaration / sidecar | per sub-game | SUBGAME | PUBLIC (tag), **key SECRET** |
| Current sub-game index | `app.orchestrator` | state machine, logger, reporter | orchestrator | log + result | series start | SERIES | PUBLIC |
| Turn number / step | `domain.truth` | rules, strategy (via Observation), logger | `app.turn_service` | log entry | sub-game start | SUBGAME | PUBLIC |
| **Own position** | `domain.truth` | rules, observation builder, GUI projection | `app.turn_service` (after validation) | log entry | sub-game start | SUBGAME | **LOCAL-TRUTH** |
| Barrier set | `domain.barriers` | rules, observation, GUI, scoring | `app.turn_service` (police placement) | log entry | sub-game start | SUBGAME | PUBLIC |
| Scent observation/field | `domain.scent` | strategy (via Observation), GUI | `app.turn_service` per step | log entry | sub-game start | SUBGAME | PUBLIC |
| **Belief state** | `domain.belief` | strategy (via Observation), GUI (labelled) | `app.turn_service` after each permitted observation | optional (derived) | sub-game start | SUBGAME | **BELIEF** |
| Hint / `intent` (pre-reveal) | `app.turn_service` (pending record) | commitment only | turn_service | sealed in commitment | per turn | TURN | LOCAL-TRUTH until reveal |
| Pending commitment (`H_commit`) | `protocol.commitment` | orchestrator, logger, peer | commitment | log entry | per turn | TURN | PUBLIC |
| **Nonce** | `protocol.commitment` | commitment only | commitment | **withheld until final audit** | per turn (revealed at audit) | TURN→AUDIT | **SECRET until audit** |
| Acknowledgement | `app.turn_service` | orchestrator, logger | turn_service on peer ack | log entry | per turn | TURN | PUBLIC |
| Revealed move | `app.turn_service` | rules, logger, GUI | turn_service on reveal | log entry | per turn | TURN | PUBLIC after reveal |
| Deadlines / watchdog timers | `infra.clock` | orchestrator, state machine | clock | timing metrics only | per turn / per call | TURN | LOCAL |
| Score (per sub-game + cumulative) | `domain.scoring` (computed) → `app.orchestrator` (recorded) | reporter, GUI, logger | orchestrator at sub-game end | result artifact | series start | SERIES | PUBLIC |
| Token usage / cost | `infra.metrics` | reporter, GUI | metrics on each LLM call | result (`tokens`, `total_tokens`) | series start | SERIES | PUBLIC (aggregate) |
| Logs / evidence | `infra.logger` | replay, auditors | logger (**append-only**) | `log_<game_id>_g<NN>.json` | sub-game start (new file) | SUBGAME | PUBLIC |
| Final result | `infra.reporter` (assembles) | grader, opponent | reporter once | `result_<game_id>.json` | series end | SERIES | PUBLIC |
| **Key material** | `infra.settings` (env only) | `protocol.keyed_auth` at use time | — | **never persisted** | process end | PROCESS | **SECRET** |
| Local runtime settings | `infra.settings` | infra only | settings load | local file/env (git-ignored) | process start | PROCESS | LOCAL |
| State-machine current state | `app.state_machine` | orchestrator | state_machine only | log transitions | sub-game start | SUBGAME | LOCAL |

## Stage 5-R8 additions

| State | Sole owner | Readers | Written by | Persisted as | Lifetime | Scope | Classification |
|---|---|---|---|---|---|---|---|
| Capture transcript, inbound | `app.turn_protocol_runtime` (`TurnTranscript.inbound`) | this sub-game's `AuditRuntime`, logger | the turn runtime, when it answers a reveal | log `reveal` events + `capture[]` of the peer's disclosure | per turn → sub-game audit | TURN→SUBGAME | PUBLIC after reveal |
| Capture transcript, outbound | `app.turn_protocol_runtime` (`TurnTranscript.outbound`) → `app.outbound_evidence_runtime` | our own disclosure writer, logger | `PeerRunner`, only once the peer's answer returned | our own `capture[]` | per turn → sub-game | TURN→SUBGAME | PUBLIC after reveal |
| Semantic finding | `app.audit_runtime` (`semantic`) | `SeriesAuditGate`, logger | `app.sub_game_closure`, once per sub-game, after the disclosure | log `audit.semantic` | sub-game end | SUBGAME | **LOCAL-DERIVED-AUDIT** |

8. **A capture row has two independent custodians on purpose.** The answerer
   keeps what it answered and the asker keeps what it was told; the final audit
   compares them. This is the one place where duplication is the mechanism
   rather than a defect, and it is why the two directions are never merged.
9. **The semantic finding is derived, never received.** Like `audit.result`, a
   peer's claim about it has no standing: each side replays the disclosed game
   itself.

## Anti-duplication rules

1. **Own position** exists once (`domain.truth`). GUI/logger receive copies in events; they never write back.
2. **Barriers** exist once (`domain.barriers`); the log stores an *append-only record* of placements, not a second live set.
3. **Score** is *computed* by `domain.scoring` and *recorded* by the orchestrator; the reporter never recomputes it differently — it reads the recorded value.
4. **Belief is never promoted to truth.** No code path may copy `domain.belief` into `domain.truth`.
5. **Nonce has exactly one custodian** (`protocol.commitment`) and one release point (final audit).
6. **Config is immutable after lock** — any post-lock write attempt is a programming defect (ERROR_MODEL `E-LOCAL`).
7. **No opponent-truth state exists in this table** — because it is never received (`ROLE_RESPONSIBILITIES.md` §2).
