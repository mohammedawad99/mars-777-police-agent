# Prompt Register - group MaRs-777

> **Status: DRAFT.**
> **Purpose:** Reference (not necessarily verbatim) the supervising-reviewer
> prompts that drove each stage, for traceability and academic honesty.
> **Note:** Never store secrets, tokens, or credentials here.

| Stage | Summary | Recorded |
|-------|---------|----------|
| 0A | Read-only environment / tooling / Git / GitHub preflight audit | Referenced |
| 0B | Local repository foundation for both agents (no remote, no commit) | Referenced |
| 0B.1 | Final evidence audit and narrow foundation correction | Referenced |
| 0C | Create private remotes; one reviewed initial commit and push each | Referenced |
| 0C.1–0C.4 | Workflow-scope auth attempts; SSH transport recovery + push; CI rerun & targeted Windows verification | Referenced |
| 0D | Repository protection assessment (branch protection unavailable on plan) | Referenced |
| 1A | Authoritative book extraction & requirement catalog (specification only) | Referenced |
| 1B | Independent specification cross-audit & correction (App F counts, technical_loss, num_games) | Referenced |
| 1B-CLOSE | Reviewed specification baseline commit + push | Referenced |
| 1C | Four JSON artifact **contracts** (specification only; provenance-classified) | Referenced |
| 1D | Final JSON contract audit & interoperability lock (verdict/intent, game_uid, NDEC) | Referenced |
| 1D.1 | Cryptographic & reporting contract corrections (Step-0/config **keyed authentication** K1/K2, result self-containment K3, reporting-sanction conflict C-09/K4) | Referenced |
| 2A | Architecture freeze and PRD blueprint (21 architecture docs, 7 blueprints) | Referenced |
| 2A-R | Lecturer reference repository audit + chatbot question pack (read-only) | Referenced |
| 2A-R2 | Final chatbot/attachment reconciliation; JDEC-014; matrix 77 → 75 | Referenced |
| 2A-CLOSE | Consistency sweep, commit, push, CI | Referenced |
| 2B | Full PRD-01…04 | Referenced |
| 2C | Full PRD-05…07 | Referenced |
| 2-CLOSE | Final PRD consistency audit, approval, commit, push, CI | Referenced |
| 3A | Deterministic domain foundation - tests first (grid config, position, board, moves, legality, apply) | Referenced |
| 3A-CLOSE | Stage-3A final audits, narrow tracking update, commit, push, CI | Referenced |
| 3B | Deterministic game semantics - tests first (barriers, capture, terminal, scoring, scent) | Referenced |
| 3B-FIX1 | Supervising correction: terminal threshold admissibility (JDEC-015) + scent radial contract hardening | Referenced |
| 3B-FIX2 | Supervising ruling: scent state bound vs additive update resolved as C-10 (saturating recurrence) | Referenced |
| 3B-CLOSE | Stage-3B final audit, tracking finalization, commit, push, CI | Referenced |
| 3C | Local application / turn orchestration foundation - tests first | Referenced |
| 3C-FIX1 | Supervising correction: remove duplicated local barrier-count state | Referenced |
| 3C-CLOSE | Stage-3C final audits, PRD-02 status alignment, commit, push, CI | Referenced |
| 4A | Local protocol state machine foundation - tests first (18 phases, frozen graph) | Referenced |
| 4A-FIX1 | Supervising correction: TECHNICAL_LOSS lifecycle reconciled with series continuation | Referenced |
| 4A-CLOSE | Stage-4A final graph/ownership audit, tracking, commit, push, CI | Referenced |
| 4B | Protocol event / transition evidence foundation - tests first (per-transition evidence, no invented event enum) | Referenced |
| 4B-FIX1 | Supervising corrections: transition evidence valid by construction against the single frozen graph; repository-wide physical-LOC reconciliation | Referenced |
| 4B-CLOSE | Stage-4B final evidence/graph invariant audit, LOC proof, tracking, commit, push, CI | Referenced |
| 4C | Local orchestrator / protocol guard foundation - tests first (sub-game cursor, one cursor-owned branch) | Referenced |
| 4C-FIX1 | Supervising correction: counted series is num_games = 6 FIXED, not a floor; bootstrap/constructor audit | Referenced |
| 4C-CLOSE | Stage-4C final FIXED-series/cursor audit, package-surface alignment, tracking, commit, push, CI | Referenced |
| 4D | Application port contracts foundation - tests first (BLOCKED before code; no signature guessed) | Referenced |
| 4D-R1 | Application port architecture reconciliation: 20-port inventory, app.ports dependency policy, signature-freeze policy | Referenced |
| 4D-R1-CLOSE | Stage-4D-R1 final architecture-diff audit, tracking, commit, push, CI | Referenced |
| 4E | Protocol semantic message contracts foundation - tests first (BLOCKED before code; two blockers) | Referenced |
| 4E-R1 | Semantic message architecture / turn-cursor reconciliation: app.peer_messages home, FR-044 scope, 10-family inventory | Referenced |
| 4E-R1-FIX1 | Turn-cursor consistency + sub-game-control identity reconciliation | Referenced |
| 4F | Protocol value representation contracts foundation - audit first (BLOCKED before code) | Referenced |
| 4F-R1 | Shared protocol value architecture / representation reconciliation | Referenced |
| 4F-R1-FIX1 | Runtime value-consumer dependency + readiness-accounting hardening | Referenced |
| 4F-R1-CLOSE | Stage-4F-R1 final contract/accounting audit, tracking, commit, push, CI | Referenced |
| 4F-RESUME | Sha256Digest + FinalAuditVerdict only - tests first | Referenced |
| 4F-RESUME-FIX1 | Digest error contract (ValueError) + public surface consistency | Referenced |
| 4F-CLOSE | Stage-4F final implementation audit, tracking, commit, push, CI | Referenced |
| 4E-R2 | Peer message runtime contract readiness reconciliation: app.peer_messages capability + protocol_values dependency, cycle proof, TurnCursor home, ten-family readiness, Stage-4E subset selection | Referenced |
| 4E-R2-FIX1 | Current result-agreement contract consistency (NDEC-006 object-form residue) + TurnCursor/Commitment static-construction error semantics | Referenced |
| 4E-R2-FIX2 | PRD result-agreement propagation (FR-142/FR-085/FR-190) + TurnCursor fixed-constant dependency reconciliation | Referenced |
| 4E-RESUME | TurnCursor + Commitment foundation - tests first (the one ready peer-message family) | Referenced |
| 4E-RESUME-CLOSE | Stage-4E slice final implementation audit, tracking, commit, push, CI | Referenced |
| 4E-R3 | Acknowledgement + Reveal contract reconciliation: by_role provenance, sealed-action semantics, barrier binding, shared action home | Referenced |
| 4E-RESUME2 | Acknowledgement foundation - tests first (the second ready peer-message family) | Referenced |
| 4E-RESUME2-FIX1 | Clean-parent TDD replay + scope reconciliation after an interrupted attempt left an unclean preflight and a reconstructed RED | Referenced |
| 4E-RESUME2-CLOSE | Acknowledgement slice final implementation audit, tracking, commit, push, CI | Referenced |
| 4E-RESUME2-CLOSE-FIX1 | External Claude-memory boundary audit and narrow repair (repositories untouched) | Referenced |
| 4E-R4 | Shared physical action + canonical move representation reconciliation: action home, type model, turn_service migration, sealed `move` encoding | Referenced |
| 4E-R4-CLOSE | Shared physical-action reconciliation final audit, tracking, commit, push, CI | Referenced |
| 4E-R5 | Shared physical-action foundation + LocalTurnService migration - tests first, impact-scan-derived scope | Referenced |
| 4E-R5-CLOSE | Physical-action migration final audit, Reveal readiness, tracking, commit, push, CI | Referenced |
| 4E-RESUME3 | Reveal foundation - tests first (the third peer-message family) | Referenced |
| 4E-RESUME3-CLOSE | Reveal final audit, module-capacity ruling, tracking, commit, push, CI | Referenced |
| 4E-R6 | Remaining turn-protocol readiness (#8/#11/#12) + peer-message module organization reconciliation | Referenced |
| 4E-R6-FIX1 | Final-nonce contract hardening: recomputation rationale, CSPRNG separation, sub-game batch, full type inventory | Referenced |
| 4E-R6-FIX2 | Nonce representation negotiation consistency: one v1 profile, pre-match echo, no alternative codec | Referenced |
| 4E-R6-CLOSE | Remaining turn-protocol + module organization final audit, tracking, commit, push, CI | Referenced |
| 4E-R7 | Peer-message module reorganization - pure behaviour-preserving migration, tests first | Referenced |
| 4E-R7-SUPPLEMENT | Mandatory report completion (evidence only; no code change) | Referenced |
| 4E-R7-CLOSE | Module reorganization final audit, tracking, commit, push, CI | Referenced |
| 4E-R8 | Final nonce reveal foundation - nonce value, reveal entry and batched reveal, tests first | Referenced |
| 4E-R8-CLOSE | Final nonce reveal final audit, tracking, commit, push, CI | Referenced |
| 4E-R9 | Canonical commitment codec + recompute foundation - dependency audit first, then tests-first implementation if ready | Referenced |
| 4E-R9-R1 | Sealed commitment semantic prerequisites reconciliation (role, intent, state, ensure_ascii, hash-mismatch ownership) | Referenced |
| 4E-R9-R1-CLOSE | Semantic prerequisites final audit, tracking, commit, push, CI | Referenced |
| 4E-R9-R2 | Sealed record semantic values foundation - ActorRole, Intent and SealedState, tests first | Referenced |
| 4E-R9-R2-CLOSE | Sealed record semantic values final audit, tracking, commit, push, CI | Referenced |
| 4E-R9-RESUME | Canonical commitment codec + recompute foundation - tests first, fixed known-answer vectors | Referenced |
| 4E-R9-RESUME-CLOSE | Codec final audit, narrow architecture correction, tracking, commit, push, CI | Referenced |
| 4E-R10 | Final audit + move validation readiness reconciliation | Referenced |
| 4E-R10-R1 | Final-audit inventory + audit-material exchange reconciliation | Referenced |
| 4E-R10-R1-CLOSE | Final-audit inventory final audit, tracking, commit, push, CI | Referenced |

The full prompt texts may be pasted here later if the reviewer approves; they
contain no secrets.
