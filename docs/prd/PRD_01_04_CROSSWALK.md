# PRD-01…04 Crosswalk — group MaRs-777 (POLICE)

**Status: STAGE 2B — ownership and coverage audit. Documentation only.**

Purpose: guarantee that **every concern has exactly one primary PRD**, that
cross-references are explicit, and that **no locked requirement disappears**.

## 1. Concern ownership

| Concern | Primary PRD | Secondary PRD | Source IDs | Architecture owner |
|---|---|---|---|---|
| Game state / turn semantics | **PRD-01** | PRD-02 (sequencing) | GAME-003/005/008 | `domain.truth`, `domain.rules` |
| Movement legality | **PRD-01** | PRD-03 (pre-check only) | GAME-003, GAME-004, GAME-009 | `domain.rules` |
| Barriers (legality, quota, irreversibility) | **PRD-01** | PRD-03 (proposes) | BAR-001…005 | `domain.barriers` |
| Capture / survival / terminals | **PRD-01** | PRD-07 (evidence) | GAME-005/006/008 | `domain.rules` |
| Scoring | **PRD-01** | PRD-07 (report) | GAME-006, C-07 | `domain.scoring` |
| Series aggregation (6 sub-games) | **PRD-01** | PRD-02 (orchestration) | LEAGUE-005, C-05 | `domain.scoring`, `app.orchestrator` |
| **Scent physics** | **PRD-01** | PRD-04 (consumes) | SCENT-002 | `domain.scent` |
| **Scent interpretation** | **PRD-04** | PRD-03 (consumes) | SCENT-001/003 | `protocol.hints`, app boundary |
| Belief input | **PRD-01** (type/owner) | PRD-03 (uses), PRD-04 (feeds) | GUI-001/002 | `domain.belief` |
| Strategy decision | **PRD-03** | PRD-01 (validates) | STRAT-001…003 | strategy plug-in |
| Language / hints / `intent` | **PRD-04** | PRD-06 (seals) | LLM-002/003/004, C-08 | `protocol.hints` |
| LLM tiers T0/T1/T2 | **PRD-04** | PRD-03 (consumes) | LLM-001/005 | `infra.llm` |
| State machine | **PRD-02** | PRD-01 (verdicts) | STATE-001…003 | `app.state_machine` |
| FastMCP server/client | **PRD-02** | PRD-05 (public exposure) | ARCH-004, NET-004 | `infra.mcp_*` |
| SeriesLauncher | **PRD-02** | PRD-05 (tunnel lifetime) | ARCH-001/002 | `infra.series_launcher` |
| Timeouts / watchdog | **PRD-02** | — | STATE-004/005 | `infra.clock` |
| Rate limiting / retries / 429 | **PRD-02** | PRD-05 (egress), PRD-07 (Gmail) | NET-002/003 | `infra.gatekeeper` |
| Compatibility profiles | **PRD-02** (selection/freeze) | PRD-04, PRD-06 | JDEC-013/014 | `protocol.profiles` |
| Privacy (opponent truth) | **PRD-01** (structural) | PRD-03, PRD-04, PRD-07 | GUI-001/002 | `domain.observation` |
| Determinism | **PRD-01** (domain) | PRD-02, PRD-03, PRD-04 | JDEC-002 | all layers |
| Evidence / logging | **PRD-02** (emits) | PRD-07 (owns artifacts) | REPLAY-001/002 | `infra.logger` |
| Token accounting | **PRD-04** | PRD-07 (reports) | PERF-001/002/003 | `infra.metrics` |
| Public tunnel / egress | *PRD-05* | PRD-02 | NET-001/002/003 | `infra.mcp_client` |
| Crypto / commit-reveal / auth | *PRD-06* | PRD-01, PRD-02, PRD-04 | CRYPTO-*, SEC-* | `protocol.*` |
| Artifacts / replay / GUI / report | *PRD-07* | PRD-01, PRD-02 | JSON-*, REPORT-*, GUI-*, REPLAY-*, LEAGUE-* | `infra.artifacts/replay/gui/reporter` |

**No concern has two primary owners.** Cross-PRD *references* are permitted; conflicting
requirements are not.

## 2. Requirement coverage (all 91 accounted for)

| Owner | Count | Requirement IDs |
|---|---|---|
| **PRD-01** | **15** | GAME-001…009 (9), BAR-001…005 (5), SCENT-002 |
| **PRD-02** | **11** | ARCH-001…005 (5), STATE-001…005 (5), NET-004 |
| **PRD-03** | **3** | STRAT-001, STRAT-002, STRAT-003 |
| **PRD-04** | **10** | LLM-001…005 (5), SCENT-001, SCENT-003, PERF-001, PERF-002, PERF-003 |
| **Subtotal PRD-01…04** | **39** | — |
| *PRD-05 (deferred)* | **3** | NET-001, NET-002, NET-003 |
| *PRD-06 (deferred)* | **17** | CRYPTO-001…011 (11), SEC-001…006 (6) |
| *PRD-07 (deferred)* | **19** | GUI-001…003 (3), REPLAY-001/002 (2), REPORT-001…003 (3), JSON-001…004 (4), LEAGUE-001…007 (7) |
| *EXTERNAL / SUBMISSION (deferred)* | **13** | GIT-001…005 (5), DOC-001…003 (3), SUB-001…005 (5) |
| **TOTAL** | **91** | — |
| **Unmapped** | **0** | — |

### Cross-cutting (owned once, constraining several PRDs)

| Requirement | Owner | Also constrains |
|---|---|---|
| GAME-009 (legality never LLM) | PRD-01 | PRD-03, PRD-04 |
| LLM-001 (no LLM move decision) | PRD-04 | PRD-03 |
| LLM-005 (T2 by mutual agreement) | PRD-04 | PRD-03 |
| GUI-001/002 (no objective board) | *PRD-07* | PRD-01 (structural), PRD-03, PRD-04 |
| STATE-004/005 (deadline/watchdog) | PRD-02 | PRD-03, PRD-04 (decision budgets) |
| PERF-001/002 (token report/lock) | PRD-04 | PRD-06 (Step-0 lock), PRD-07 (result) |
| SCENT-001/003 (model lock/exchange) | PRD-04 | PRD-01 (physics), PRD-06 (locking) |
| NET-002 (rate limiter) | *PRD-05* | PRD-02 (gatekeeper), PRD-07 (Gmail egress) |
| CRYPTO-008/009 (sequence, canonical record) | *PRD-06* | PRD-01 (`state`), PRD-02 (sequencing), PRD-04 (`intent`) |
| LEAGUE-005 (`num_games`) | *PRD-07* | PRD-01 (series semantics), PRD-02 (orchestration) |

## 3. Role-symmetry classification

| PRD | Classification | Police-specific | Thief-specific |
|---|---|---|---|
| **PRD-01** | **COMMON-WITH-ROLE-SECTIONS** | §5.3 + barrier action space (BAR-001…005 are police actions); scoring perspective | §5.3 + no barrier action; survival perspective; GAME-005 trap risk emphasised |
| **PRD-02** | **COMMON-WITH-ROLE-SECTIONS** | title/§7 role identity only | title/§7 role identity only — protocol behaviour identical |
| **PRD-03** | **ROLE-SPECIFIC** | pursuit policy: barrier-aware distance minimisation, information-gain on ambiguity, barrier placement rule, anti-passivity | escape policy: mobility guard (GAME-005 defence), escape-room preservation, threat region, corner penalty, survival awareness, **never proposes a barrier** |
| **PRD-04** | **COMMON-WITH-ROLE-SECTIONS** | §13.6: hints for behavioural profiling/pressure | §13.6: hints as primary deception instrument |
| **This crosswalk** | **COMMON-WITH-ROLE-SECTIONS** | header role | header role |
| **PRD_01_04_REVIEW** | **COMMON-EXACT** | none | none |

**The game rulebook is not duplicated:** PRD-01 is semantically identical across both
repositories except for the role's action space and scoring perspective.

## 4. Deliberate non-duplication checks

| Risk | Resolution |
|---|---|
| Scent specified twice | PRD-01 owns **physics**; PRD-04 owns **interpretation**. PRD-04 explicitly forbids recomputing or re-parameterising the field. |
| Legality specified twice | PRD-01 owns legality; PRD-03 may only *pre-check* using the same rules and the validator stays authoritative. |
| Timeouts specified twice | PRD-02 owns deadline enforcement; PRD-03/04 only consume a budget strictly inside it. |
| Belief specified twice | PRD-01 owns the type/authority; PRD-03 keeps a derived working copy that is never promoted to truth. |
| Token accounting twice | PRD-04 owns metering; PRD-07 only reports the totals. |
| Series orchestration vs game rules | PRD-01 owns per-sub-game semantics + aggregation; PRD-02 owns which process plays when. Role alternation is orchestration, **not a game rule**. |
