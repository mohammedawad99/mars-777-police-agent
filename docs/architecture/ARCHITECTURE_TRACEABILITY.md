# Architecture Traceability — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — mapping only.**
**No requirement is marked IMPLEMENTED or VERIFIED. Implementation has not begun.**

Every one of the **91** locked requirements maps to at least one architecture
component, a PRD owner, and a status. Status vocabulary:

- **ARCHITECTURE-DEFINED** — a component and boundary now own it; detailed behaviour
  goes into the PRD, implementation later.
- **PRD-PENDING** — ownership assigned; the requirement needs PRD elaboration before it
  can be designed further.
- **IMPLEMENTATION-PENDING** — architecture is settled; only code remains.
- **EXTERNAL-EVIDENCE-PENDING** — satisfied by an external act (submission, delivery,
  repository access), not by code.

## Coverage summary

| Metric | Value |
|---|---|
| Requirements mapped | **91 / 91** |
| **MUST** mapped | **76 / 76** |
| **MUST NOT** mapped | **9 / 9** |
| SHOULD mapped | 4 / 4 |
| MAY mapped | 2 / 2 |
| **Unmapped MUST / MUST NOT** | **0** |
| Marked IMPLEMENTED | **0** |

## Domain → primary owner

| Domain | Count | Primary architecture owner | PRD |
|---|---|---|---|
| ARCH | 5 | System topology / dependency layering | PRD-02 |
| BAR | 5 | Barrier subsystem + legality validator | PRD-01 |
| CRYPTO | 11 | Commit-Reveal, keyed auth, canonical bytes | PRD-06 |
| DOC | 3 | Documentation + submission evidence | PRD-07 |
| GAME | 9 | Rules, scoring, board, config model | PRD-01 |
| GIT | 5 | Version identity / exact played commit | PRD-07 |
| GUI | 3 | GUI projection (events only) | PRD-07 |
| JSON | 4 | Artifact lifecycle + canonicalization | PRD-07 |
| LEAGUE | 7 | Series scoring + result agreement | PRD-07 |
| LLM | 5 | LLM boundary + hint subsystem | PRD-04 |
| NET | 4 | FastMCP transport + Gatekeeper | PRD-05 |
| PERF | 3 | Token/cost accounting | PRD-04 |
| REPLAY | 2 | Replay verifier (artifacts only) | PRD-07 |
| REPORT | 3 | Reporting / Gmail egress | PRD-07 |
| SCENT | 3 | Scent subsystem | PRD-04 |
| SEC | 6 | Security architecture / secret boundary | PRD-06 |
| STATE | 5 | State machine, deadlines, watchdog | PRD-02 |
| STRAT | 3 | Strategy plug-in boundary | PRD-03 |
| SUB | 5 | Submission delivery | PRD-07 |

## Multi-PRD requirements

Some requirements are owned by one PRD but **constrain** others; these are the
deliberate cross-cutting cases:

| Requirement | Primary | Also constrains | Reason |
|---|---|---|---|
| CRYPTO-001/002/008/009 (commit-reveal) | PRD-06 | PRD-01, PRD-02, PRD-07 | turn pipeline, state machine, replay evidence |
| CRYPTO-006 (signed Step-0) | PRD-06 | PRD-05, PRD-07 | handshake transport + result `hardware_auth` |
| GAME-001/002 (config equality, Appendix F enforcement) | PRD-01 | PRD-02, PRD-06 | lock sequencing + keyed config auth |
| LLM-001 (never delegate legality) | PRD-04 | PRD-01, PRD-03 | validator ownership and strategy boundary |
| NET-002/003 (rate limit, retry/429) | PRD-05 | PRD-07 | also governs Gmail reporting egress |
| PERF-001/002 (token reporting) | PRD-04 | PRD-07 | tokens surface in the result artifact |
| REPLAY-001/002 | PRD-07 | PRD-06 | replay verifies commitments |
| GUI-001/002 (no objective board) | PRD-07 | PRD-03 | privacy wall also constrains strategy inputs |
| JSON-003/004 (artifact identity/canonical) | PRD-07 | PRD-01, PRD-06 | config identity + hashing |
| SUB-004 (four links / two repos) | PRD-07 | — | external submission evidence |

## Full mapping (91 rows)

| Requirement | Modality | Scope | Architecture component | PRD | Status |
|---|---|---|---|---|---|
| ARCH-001 | MUST | BOTH | System topology, process isolation, module/dependency layering | PRD-02 | ARCHITECTURE-DEFINED |
| ARCH-002 | MUST NOT | BOTH | System topology, process isolation, module/dependency layering | PRD-02 | ARCHITECTURE-DEFINED |
| ARCH-003 | MUST | BOTH | System topology, process isolation, module/dependency layering | PRD-02 | ARCHITECTURE-DEFINED |
| ARCH-004 | MUST | BOTH | System topology, process isolation, module/dependency layering | PRD-02 | ARCHITECTURE-DEFINED |
| ARCH-005 | MUST | BOTH | System topology, process isolation, module/dependency layering | PRD-02 | ARCHITECTURE-DEFINED |
| NET-001 | MUST | BOTH | FastMCP transport + Gatekeeper (infra.mcp_*, infra.gatekeeper) | PRD-05 | ARCHITECTURE-DEFINED |
| NET-002 | MUST | BOTH | FastMCP transport + Gatekeeper (infra.mcp_*, infra.gatekeeper) | PRD-05 | ARCHITECTURE-DEFINED |
| NET-003 | MUST | BOTH | FastMCP transport + Gatekeeper (infra.mcp_*, infra.gatekeeper) | PRD-05 | ARCHITECTURE-DEFINED |
| NET-004 | MUST | BOTH | FastMCP transport + Gatekeeper (infra.mcp_*, infra.gatekeeper) | PRD-05 | ARCHITECTURE-DEFINED |
| GAME-001 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-002 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-003 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-004 | MUST NOT | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-005 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-006 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-007 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-008 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| GAME-009 | MUST | BOTH | Rules, scoring, board, config model (domain.*) | PRD-01 | ARCHITECTURE-DEFINED |
| BAR-001 | MUST | POLICE | Barrier subsystem + legality validator (domain.barriers, domain.rules) | PRD-01 | ARCHITECTURE-DEFINED |
| BAR-002 | MUST NOT | POLICE | Barrier subsystem + legality validator (domain.barriers, domain.rules) | PRD-01 | ARCHITECTURE-DEFINED |
| BAR-003 | MUST | POLICE | Barrier subsystem + legality validator (domain.barriers, domain.rules) | PRD-01 | ARCHITECTURE-DEFINED |
| BAR-004 | MUST | POLICE | Barrier subsystem + legality validator (domain.barriers, domain.rules) | PRD-01 | ARCHITECTURE-DEFINED |
| BAR-005 | MUST | POLICE | Barrier subsystem + legality validator (domain.barriers, domain.rules) | PRD-01 | ARCHITECTURE-DEFINED |
| SCENT-001 | MUST | BOTH | Scent/pheromone subsystem (domain.scent) | PRD-04 | ARCHITECTURE-DEFINED |
| SCENT-002 | MUST | BOTH | Scent/pheromone subsystem (domain.scent) | PRD-04 | ARCHITECTURE-DEFINED |
| SCENT-003 | MUST | BOTH | Scent/pheromone subsystem (domain.scent) | PRD-04 | ARCHITECTURE-DEFINED |
| CRYPTO-001 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-002 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-003 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-004 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-005 | MUST NOT | POLICE | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-006 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-007 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-008 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-009 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-010 | SHOULD | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| CRYPTO-011 | MUST | BOTH | Commit-Reveal, keyed auth, canonical bytes (protocol.*) | PRD-06 | ARCHITECTURE-DEFINED |
| STATE-001 | MUST | BOTH | State machine, deadlines, watchdog (app.state_machine, infra.clock) | PRD-02 | ARCHITECTURE-DEFINED |
| STATE-002 | MUST | BOTH | State machine, deadlines, watchdog (app.state_machine, infra.clock) | PRD-02 | ARCHITECTURE-DEFINED |
| STATE-003 | MUST | BOTH | State machine, deadlines, watchdog (app.state_machine, infra.clock) | PRD-02 | ARCHITECTURE-DEFINED |
| STATE-004 | MUST | BOTH | State machine, deadlines, watchdog (app.state_machine, infra.clock) | PRD-02 | ARCHITECTURE-DEFINED |
| STATE-005 | MUST | BOTH | State machine, deadlines, watchdog (app.state_machine, infra.clock) | PRD-02 | ARCHITECTURE-DEFINED |
| STRAT-001 | MUST | BOTH | Strategy plug-in boundary (app.strategy_api) | PRD-03 | ARCHITECTURE-DEFINED |
| STRAT-002 | MUST | BOTH | Strategy plug-in boundary (app.strategy_api) | PRD-03 | ARCHITECTURE-DEFINED |
| STRAT-003 | MAY | BOTH | Strategy plug-in boundary (app.strategy_api) | PRD-03 | ARCHITECTURE-DEFINED |
| LLM-001 | SHOULD | BOTH | LLM boundary + hint subsystem (infra.llm, protocol.hints) | PRD-04 | ARCHITECTURE-DEFINED |
| LLM-002 | MUST | BOTH | LLM boundary + hint subsystem (infra.llm, protocol.hints) | PRD-04 | ARCHITECTURE-DEFINED |
| LLM-003 | MUST NOT | BOTH | LLM boundary + hint subsystem (infra.llm, protocol.hints) | PRD-04 | ARCHITECTURE-DEFINED |
| LLM-004 | MUST | BOTH | LLM boundary + hint subsystem (infra.llm, protocol.hints) | PRD-04 | ARCHITECTURE-DEFINED |
| LLM-005 | MAY | BOTH | LLM boundary + hint subsystem (infra.llm, protocol.hints) | PRD-04 | ARCHITECTURE-DEFINED |
| GUI-001 | MUST | BOTH | GUI projection (infra.gui, projection events only) | PRD-07 | ARCHITECTURE-DEFINED |
| GUI-002 | MUST NOT | BOTH | GUI projection (infra.gui, projection events only) | PRD-07 | ARCHITECTURE-DEFINED |
| GUI-003 | MUST | BOTH | GUI projection (infra.gui, projection events only) | PRD-07 | ARCHITECTURE-DEFINED |
| REPLAY-001 | MUST | BOTH | Replay verifier over artifacts only (infra.replay) | PRD-07 | ARCHITECTURE-DEFINED |
| REPLAY-002 | MUST | BOTH | Replay verifier over artifacts only (infra.replay) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-001 | MUST | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-002 | MUST | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-003 | MUST | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-004 | MUST NOT | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-005 | MUST | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-006 | MUST | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| LEAGUE-007 | MUST | LEAGUE | Series/league scoring + result agreement (app.orchestrator, infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| JSON-001 | MUST | BOTH | Artifact lifecycle + canonicalization (infra.artifacts, protocol.canonical) | PRD-07 | ARCHITECTURE-DEFINED |
| JSON-002 | MUST NOT | BOTH | Artifact lifecycle + canonicalization (infra.artifacts, protocol.canonical) | PRD-07 | ARCHITECTURE-DEFINED |
| JSON-003 | MUST | BOTH | Artifact lifecycle + canonicalization (infra.artifacts, protocol.canonical) | PRD-07 | ARCHITECTURE-DEFINED |
| JSON-004 | MUST | BOTH | Artifact lifecycle + canonicalization (infra.artifacts, protocol.canonical) | PRD-07 | ARCHITECTURE-DEFINED |
| REPORT-001 | MUST | BOTH | Reporting/Gmail egress (infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| REPORT-002 | MUST | BOTH | Reporting/Gmail egress (infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| REPORT-003 | MUST | BOTH | Reporting/Gmail egress (infra.reporter) | PRD-07 | ARCHITECTURE-DEFINED |
| GIT-001 | MUST | SUBMISSION | Version identity, exact played commit (infra.artifacts, submission) | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| GIT-002 | MUST | SUBMISSION | Version identity, exact played commit (infra.artifacts, submission) | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| GIT-003 | MUST | BOTH | Version identity, exact played commit (infra.artifacts, submission) | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| GIT-004 | MUST | SUBMISSION | Version identity, exact played commit (infra.artifacts, submission) | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| GIT-005 | MUST | SUBMISSION | Version identity, exact played commit (infra.artifacts, submission) | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| SEC-001 | MUST | BOTH | Security architecture, secret boundary (TB-6), scans | PRD-06 | ARCHITECTURE-DEFINED |
| SEC-002 | MUST | BOTH | Security architecture, secret boundary (TB-6), scans | PRD-06 | ARCHITECTURE-DEFINED |
| SEC-003 | MUST NOT | BOTH | Security architecture, secret boundary (TB-6), scans | PRD-06 | ARCHITECTURE-DEFINED |
| SEC-004 | MUST | BOTH | Security architecture, secret boundary (TB-6), scans | PRD-06 | ARCHITECTURE-DEFINED |
| SEC-005 | MUST | BOTH | Security architecture, secret boundary (TB-6), scans | PRD-06 | ARCHITECTURE-DEFINED |
| SEC-006 | MUST | BOTH | Security architecture, secret boundary (TB-6), scans | PRD-06 | ARCHITECTURE-DEFINED |
| PERF-001 | MUST | BOTH | Token/cost accounting (infra.metrics) + result reporting | PRD-04 | ARCHITECTURE-DEFINED |
| PERF-002 | MUST | BOTH | Token/cost accounting (infra.metrics) + result reporting | PRD-04 | ARCHITECTURE-DEFINED |
| PERF-003 | SHOULD | BOTH | Token/cost accounting (infra.metrics) + result reporting | PRD-04 | ARCHITECTURE-DEFINED |
| DOC-001 | MUST | SUBMISSION | Documentation set + submission evidence | PRD-07 | PRD-PENDING |
| DOC-002 | MUST | SUBMISSION | Documentation set + submission evidence | PRD-07 | PRD-PENDING |
| DOC-003 | SHOULD | BOTH | Documentation set + submission evidence | PRD-07 | PRD-PENDING |
| SUB-001 | MUST | SUBMISSION | Submission delivery obligations | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| SUB-002 | MUST | SUBMISSION | Submission delivery obligations | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| SUB-003 | MUST | SUBMISSION | Submission delivery obligations | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| SUB-004 | MUST | SUBMISSION | Submission delivery obligations | PRD-07 | EXTERNAL-EVIDENCE-PENDING |
| SUB-005 | MUST | SUBMISSION | Submission delivery obligations | PRD-07 | EXTERNAL-EVIDENCE-PENDING |

## Notes

- **Scope column** is the *game role* a requirement binds (BOTH / POLICE / LEAGUE /
  SUBMISSION), copied unchanged from the locked catalog. POLICE-scoped rows are retained
  in both repositories: the thief agent must still validate the opponent's obligations
  and the shared protocol it is audited against.
- **No status above is IMPLEMENTED or VERIFIED.** Stage 2A produced architecture and
  ownership only.
- **Stage 2A-R2:** the requirement set is **unchanged at 91** (76/9/4/2). The only
  Stage-1 edit was a *project-contract representation* correction (result static-metadata
  placement, JDEC-014) — it added **no** requirement and removed **none**. Role
  alternation, Ed25519 and config `_note` keys were classified as example/reference
  conventions and deliberately did **not** become requirements.
- Conflict-bearing requirements keep their locked resolutions: **C-07** (technical_loss
  provenance), **C-08** (verdict = intent), **C-09** (reporting sanction, strictest rule).
