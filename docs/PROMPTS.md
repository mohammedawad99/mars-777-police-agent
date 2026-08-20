# Prompt Register - group MaRs-777

> **Status: CURRENT.** Backfilled through Stage 9A-2B.
> **Purpose:** The prompt-engineering log. It records the supervising-reviewer
> prompts that drove each stage — their goal, their binding constraints, what
> the AI got wrong, what the human correction was, and what shipped.
> **Honesty rule:** nothing here is a reconstructed transcript. Rows in section 1
> are labelled `Referenced` — the prompt existed and drove the named stage, and
> its text is not reproduced. Entries in section 2 are labelled
> **`RECONSTRUCTED PROMPT INTENT`**: they summarise the goal and constraints
> from evidence that exists in this repository (`docs/PLAN.md`,
> `docs/TODO.md`, `docs/DECISIONS.md`, `docs/AI_WORKFLOW.md`, the commit
> history). Where the exact wording is not available it is **not invented**.
> **Note:** Never store secrets, tokens, or credentials here.

## 1. Stage register (Stages 0A — 4E-R18-R1)

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
| 4E-R10-R2 | MoveValidation existence + payload reconciliation | Referenced |
| 4E-R10-R3 | Move-rejection inventory + transport-response reconciliation | Referenced |
| 4E-R10-R3-CLOSE | Move-rejection reconciliation tracking, commit, push, CI | Referenced |
| 4E-R11 | Peer operation + transport contract reconciliation | Referenced |
| 4E-R11-CLOSE | Peer operation contract tracking, commit, push, CI | Referenced |
| 4E-R11-R1 | Log artifact interoperability + audit exchange reconciliation | Referenced |
| 4E-R11-R1-CLOSE | Audit log interoperability final audit, payload-core guard, tracking, commit, push, CI | Referenced |

| 4E-R12 | Step-0 + config negotiation + config lock readiness reconciliation | Referenced |
| 4E-R12-FIX | Scope repair + full readiness proof (exact vocabulary, cores, models) | Referenced |
| 4E-R12-R1 | Token accounting temporal semantics + Step-0 declaration reconciliation | Referenced |
| 4E-R12-R2 | Token-accounting evidence provenance + current FIELD_MATRIX baseline reconciliation | Referenced |
| 4E-R12-R3 | Token-budget agreement chronology reconciliation | Referenced |
| 4E-R12-CLOSE | Pre-match contract final audit, tracking, commit, push, exact-SHA CI | Referenced |

| 4E-R13 | ResultAgreement payload + result artifact reconciliation | Referenced |
| 4E-R13-R1 | Result approval core joint-derivability reconciliation | Referenced |
| 4E-R13-R2 | Result timestamp carriage + deterministic agreement cadence reconciliation | Referenced |
| 4E-R13-CLOSE | ResultAgreement + joint result core final audit, tracking, commit, push, exact-SHA CI | Referenced |

| 4E-R14 | Pregame peer semantic types implementation (stopped before code) | Referenced |
| 4E-R14-R1 | Pregame semantic implementation dependency contract freeze | Referenced |
| 4E-R14-R1-FIX | Hardware type + profile-count + shared-primitive ownership repair | Referenced |
| 4E-R14-R1-FIX2 | VRAM numeric type final freeze | Referenced |
| 4E-R14-R2 | Pregame peer semantic types - full implementation | Referenced |
| 4E-R14-CLOSE | Pregame semantic types tracking, commit, push, exact-SHA CI | Referenced |

| 4E-R15 | ResultAgreement semantic types implementation | Referenced |
| 4E-R15-CLOSE | ResultAgreement values tracking, commit, push, exact-SHA CI | Referenced |

| 4E-R16 | Peer application protocol runtime implementation | Referenced |
| 4E-R16-FIX | Conditional VRAM Step-0 projection + framing verification | Referenced |
| 4E-R16-CLOSE | Runtime doc reconciliation, tracking, commit, push, exact-SHA CI | Referenced |

| 4E-R17 | FastMCP + peer transport adapter integration *(stopped BLOCKED-BEFORE-CODE)* | Referenced |
| 4E-R17-R1 | FastMCP dependency provisioning + transport wire contract freeze | Referenced |
| 4E-R17-R1-FIX | Direct pydantic dependency ownership | Referenced |
| 4E-R17-R1-CLOSE | Transport prerequisites tracking, commit, push, exact-SHA CI | Referenced |
| 4E-R17-RESUME | FastMCP + peer transport adapter integration (implementation) | Referenced |
| 4E-R17-RESUME-FIX | Result cadence + watchdog + error-identity completion proof | Referenced |
| 4E-R17-RESUME-FIX2 | Digest-disagreement error + PeerTransportPort architecture proof | Referenced |
| 4E-R17-RESUME-CLOSE | Attempted close; **stopped** on `RESULT-DIGEST-DISAGREEMENT-INTEGRATION: BLOCKED-BY-UNWIRED-PRODUCTION-GUARD`, 0 files changed | Referenced |
| 4E-R17-RESUME-FIX3 | Wire result digest verification into the production agreement workflow | Referenced |
| 4E-R17-RESUME-CLOSE-RETRY | R17 architecture reconciliation, tracking, commit, push, exact-SHA CI | Referenced |

| 4E-R18-R1-FIX3 | Wire and prove the persistent lifecycle in production composition; **stopped** on `PUBLIC-MCP-PERSISTENT-LIFECYCLE: BLOCKED-BY-MISSING-PRODUCTION-COMPOSITION-OWNER` | Referenced |
| 4E-R18-R1-CR0 | Production composition root + BOOT architecture audit (read-only) | Referenced |
| 4E-R18-R1-CR1 | Typed runtime settings + production clock | Referenced |
| 4E-R18-R1-CR2 | Concrete inbound `PeerOperations`; **stopped** on five missing application runtimes | Referenced |
| 4E-R18-R1-CLOSE-RESCOPE | Public ingress / transport infrastructure close; Stage 5 boundary decision | Referenced |

The full prompt texts may be pasted here later if the reviewer approves; they
contain no secrets.

---

## 2. Prompt engineering log (Stages 5 — 9A-2B)

Every entry below is **`RECONSTRUCTED PROMPT INTENT`**, not verbatim prompt text.

### Stage 5 (5-R1 … 5-R8) — production application runtime integration

- **Goal.** Turn the assembled protocol parts into a production runtime, then
  give the scent system a pre-game contract: a canonical model, its digest, and
  agreement on it before a game starts.
- **Constraints.** No second configuration schema. Exact model agreement — no
  tolerance, no "close enough" float comparison. The scent model must be inside
  what the configuration lock covers, or locking is theatre.
- **Finding.** Canonical decimal text had to become a single shared authority;
  two independent renderings of the same number are two different sealed bytes.
- **Correction.** The decimal authority was extracted and shared rather than
  duplicated at each call site.
- **Result.** Scent model defined, carried in proposals, agreed exactly, bound
  into the config lock, frozen across the series, persisted as artifact
  evidence, and traced closed against `SCENT-001`/`SCENT-003` (C-14, JDEC-018).

### Stage 6A / 6B — baseline strategy

- **Goal.** A separate strategy module that chooses a legal action.
- **Constraints.** Fully algorithmic. No LLM. No randomness. **No opponent
  position** — it is not observable, and a strategy that reads it would be
  cheating even if it were.
- **Correction.** 6A was held to contract and design only; no code was written
  until the contract was locked.
- **Result.** `BaselineStrategy` behind `StrategyPort`, deterministic, covered.

### Stage 6C-A / 6C-B / 6C-C1 — autonomous game owner, sub-game, series

- **Goal.** Something that actually plays: one lockstep sub-game, then exactly
  six.
- **Constraints.** No fixture may supply an action, an outcome, or a lifecycle
  call. The terminal event must be **derived** from the domain, never asserted.
- **Result.** `SubGameDriver`, then `SeriesDriver` producing `g01`…`g06`, six
  natural outcomes and the fourteen official files.

### Stage 6C-C2 — permanent autonomous CLI boot

- **Goal.** A real process that boots, plays and exits.
- **Constraint.** Prove it as **separate OS processes**, not in-process.
- **Finding — the most valuable of the project.** The in-process proof had
  hidden three real defects: (1) `SeriesDriver.open()` re-opened the round it
  was already on, destroying an authenticated proposal that had arrived first;
  (2) closing a sub-game did not wait for the **peer's** audit disclosure;
  (3) the peer's Step-0 had no awaitable moment at all.
- **Correction.** Each was fixed at its owner. None was fixed by weakening a
  guard or by loosening a test.
- **Result.** Both roles' shipped CLIs play a full series over real FastMCP/HTTP
  against a separate process and exit 0.

### Windows exact-six investigation

- **Goal.** Find out why a native Windows run stalled.
- **Constraint.** Do not "fix" it with a skip.
- **Finding.** After a long trace through the event loop, the HTTP request-body
  path and the MCP session handoff, the root cause was a session read deadline
  that was not refreshed after the configuration lock.
- **Result.** Fixed at its owner; the residual native limitation runs in its own
  CI job so it stays visible instead of disappearing behind a skip.

### Stage 7B — deterministic hint channel

- **Goal.** The natural-language half of a turn, at the T0 (no-model) scope.
- **Constraints.** Zero tokens, no network, no model. Refuse direct coordinate
  syntax such as `(3,4)` — **while leaving ordinary numeric prose sayable**, so
  the filter cannot be satisfied by banning digits.
- **Result.** A template catalogue, an NFC-normalising validator with
  deterministic word counting against the negotiated cap, and a narrow detector.
  A failing candidate is replaced by a safe template, never sent in violation.

### Stage 7C — belief-level scent interpretation

- **Goal.** Let the strategy use what the opponent disclosed.
- **Constraint.** Scent is evidence about the **environment**, never the
  opponent's position, and it may only decide where the existing objective ties.
  With nothing heard, behaviour must be byte-identical to before.
- **Result.** `ScentBelief`, folded through the existing physics under the
  locked model.

### Stage 7D-B — competitive barrier policy

- **Goal.** A legal competitive edge.
- **Constraints.** Promote on measured evidence or not at all. Never declare a
  capture on belief — a missed barrier costs a turn, a wrong claim forfeits.
- **Finding.** The police candidate cleared its gate (0 → 12 captures over 140
  deterministic scenarios). The **thief candidate failed its gate.**
- **Correction.** The thief candidate was **rejected and not shipped**; that
  repository still runs the frozen baseline. Recording the rejection is the
  point.

### Stage 8A-1R / 8A-1S — interoperability kit core

- **Goal.** Speak the pinned third party's semantics without vendoring or
  patching their code.
- **Constraints.** Pinned SHA only. Never copy their artifacts into either
  repository.
- **Finding.** Their scent family could not be declared compatible: the model
  form matches exactly, but 29 of 90 published field-walk cells differ by one
  ULP — binary64 against our exact `Decimal`.
- **Correction.** Declared **undeclared** rather than approximately compatible.

### Stage 8A-1T — kit transport envelopes

- **Goal.** A second envelope profile over the same four tools.
- **Constraints.** Selected **before boot**; never negotiated, never inferred
  from a message, never auto-downgraded. Do not weaken authentication.
- **AI mistake (significant).** The stage report claimed the pinned harness
  could run a six-sub-game series with **fixed roles**. It cannot.
- **Result.** The profile shipped; the false claim survived into the next stage
  and was caught there.

### Stage 8A-2 — fixed-role kit series — **STOPPED**

- **Goal.** Run a six-sub-game fixed-role series against the kit.
- **Constraint given.** "If full gameplay is blocked by a **new** issue: stop and
  name the exact blocker. Do not add another workaround in the same checkpoint."
- **Finding.** The premise was false. The harness alternates roles every
  sub-game by construction.
- **Correction.** The stage stopped with **zero repository changes**, and the
  previous stage's incorrect claim was retracted explicitly rather than quietly
  worked around.

### Stage 8A-2R — role-split alternation and terminal settlement

- **Goal.** Play the alternating series for real.
- **Constraints.** Neither repository may become a dual-role agent. No importing
  the sibling package, no copying its strategy, no changing `GROUP_CODE`.
- **Finding.** A live divergence: we settled `CAPTURE`, the peer settled
  `timeout`. The tempting explanation — a missing terminal message — was only
  half of it.
- **Correction.** The real root cause was ours: the self-capture rule was being
  applied to the **police**, although `BAR-004` lets the police place a barrier
  on its own cell and lawfully stand on a blocked one. A lawful placement was
  manufacturing a capture. Fixed at the rule **and** the missing settlement
  signal.
- **Result.** Six live sub-games against an independent implementation.

### Stage 8A-2F — development evidence path

- **Goal.** Persist evidence from a friendly run without pretending it is
  counted.
- **Constraints.** "Do not lie to preserve a filename." "The number 14 is **not**
  more important than semantic truth." No secret, no live URL, no stale endpoint
  in any artifact.
- **Result.** A store that **structurally refuses** any name not beginning
  `friendly_`, and a series document that records `ABSENT` for counted
  authentication and mutual agreement, `evidence_class:
  DEVELOPMENT_EVIDENCE`, `counted_eligible: false`.

### Stage 8A-2G — counted identity and artifact compatibility

- **Goal.** Make the kit's `game_id` writable without corrupting our identity.
- **Constraint.** "Do not silently lower-case the group id. Do not alter
  `GROUP_CODE`."
- **Finding.** Our own identifier alphabet (JDEC-005) rejected the kit-derived
  id because `MaRs-777` contains capitals.
- **Correction.** The **project-owned** decision was amended to admit the wider
  alphabet — the frozen group code was not bent to fit a project rule.

### Stage 8A-2G-CI — exact-SHA CI recovery

- **Goal.** Get green CI on the exact commits.
- **Constraint.** "No code change is authorized." No empty commit, no amend, no
  force, no tag, no whitespace push to trigger a run.
- **Finding.** The three-second failures were **not** a code failure: GitHub had
  blocked the account for a billing reason.
- **Result.** Existing runs re-run by id once billing was fixed. Both SHAs green,
  history untouched.

### Stage 8B-P — public production readiness without a partner

- **Goal.** Wire the gateway and the tunnel adapter — both previously uncalled
  from production — behind one public route.
- **Constraints.** Report credentials as `PRESENT`/`ABSENT` only, never their
  contents. Do not commit live URLs or runtime evidence. Do not start the tunnel
  prematurely.
- **Finding.** The framework-confinement test refused the new launcher's FastMCP
  imports.
- **Correction.** The allowlist was **deliberately not widened**; the mechanics
  moved into the transport package instead, where framework imports belong.
- **Result.** One public route, a ten-check readiness gate, proven teardown, and
  the counted-readiness authority still correctly refusing while the tunnel was
  up.

### Stage 9A-0 — academic excellence gap audit

- **Goal.** Audit the repositories against the book, the professional-software
  guideline and their own contracts, and produce a gap matrix.
- **Constraints.** Read-only. No code, no strategy, no tag. Do not authorise the
  closure slices; return them for approval.
- **Finding.** The largest gaps were deliverable coverage (Replay Viewer, GUI,
  reporting, rate-limit enforcement) and **document truth** — eight
  machine-detectable contradictions between the front-door documents and the
  committed state.
- **Result.** Zero repository changes; a supervising report.

### Stage 9A-1A — academic truth and guideline foundation closure

- **Goal.** Close the low-risk truth, documentation and hygiene defects, and
  perform the measurements the heavier slices depend on.
- **Constraints.** Use the lecturer's **actual** v3.00 PDF, verified by SHA-256,
  read-only, never committed. No production code. No SDK, no gatekeeper, no test
  split, no GUI, no replay, no Gmail, no strategy change, no tag.
- **AI mistake corrected by supervision (three).** (1) Stage 9A-0 proposed
  narrowing the published 150-line rule to `src/**`; the guideline's §6.1
  explicitly applies it to test files too, so the rule stands and the tests must
  be split. (2) 9A-0 counted **physical** lines and reported 29 violating test
  files; measured the guideline's way — blank and comment lines excluded — the
  true count is **13**. (3) 9A-0 treated the SDK requirement as satisfied by
  hexagonal architecture; §4.1 asks for an explicit single public entry
  boundary, which does not exist, so it is a mapped gap rather than a
  justified N/A.
- **Result.** Front-door documents reconciled with reality, the prompt book
  backfilled, `.env.example` and `docs/PRD.md` added,
  `docs/GUIDELINE_ALIGNMENT.md` written against the real guideline, and complete
  version-authority, SDK-equivalence and Gatekeeper-equivalence audits recorded.

### Stage 9A-1B1 — software version authority and public SDK facade

- **Goal.** Close the two guideline gaps the audit had mapped: one software
  version authority, and one public entry point for every consumer.
- **Constraints.** Resolve the guideline's version semantics from the PDF rather
  than guessing. The facade holds **zero** business logic. No test split, no
  gatekeeper, no Gmail, no replay, no GUI, no strategy change, no tag. Command
  line behaviour - flags, defaults, exit codes, error semantics, banner - must
  not change.
- **Finding (version).** The guideline's `1.00` is not a PEP-440-stable string:
  the packaging rules normalise it to `1.0`, so declaring `1.00` in
  `pyproject.toml` would publish metadata that disagrees with the declaration.
  Two truths, to satisfy formatting.
- **Correction.** The value is stored once as `MAJOR.MINOR` and *rendered* twice
  - `1.00` for the guideline, `1.0` for packaging. Nothing can drift, because
  neither string is stored.
- **Finding (boot validation).** §8.1's boot clause asks for **configuration**
  version compatibility, not software version compatibility. Reading it as a
  peer check would have coupled our package version to another group's
  implementation.
- **Correction.** The configuration half was mapped to the authority that
  already exists and is already covered by the mutual config digest; the
  software half became a **local** integrity check - installed distribution
  metadata against the source authority - that no peer can cause or observe.
- **Finding (facade).** Moving composition out of the command lines broke two
  boot guards that asserted "only the entrypoint declares the role" and "only
  the entrypoint reads the environment".
- **Correction.** The guarded property - *exactly one* place - was still true;
  the assertions were retargeted to follow it to `identity` and `compose_series`
  rather than deleted or weakened.
- **Result.** `shared/version.py`, `sdk/` with five forwarding operations, four
  composition modules below it, three command lines reduced to parse-request-
  classify, and structural tests holding both dependency directions.

### Stage 9A-1B1F — configuration version compatibility

- **Goal.** Close the one part of guideline §8.1 that the version stage had left
  `PARTIAL`: local support for the configuration schema version.
- **Constraints.** Do not add software-version comparison to the peer protocol.
  Do not change `config_sha256` bytes. Do not add a KIT wire field. Do not invent
  a rate-limit or artifact version. Resolve the supported token mechanically
  rather than from a historical report.
- **Finding (the distinction).** `NegotiatedConfig.schema_version` was validated
  non-empty, hashed and mutually agreed - and never checked against anything this
  build supports. Agreement is byte-identity between peers; compatibility is a
  local question about representation. Two peers could agree perfectly on a
  version neither of them supported.
- **Finding (the value).** No supported-version constant existed in `src/` at
  all: the token appeared only in test builders. It was resolved from the
  project's own contract instead - `VERSIONING.md` records JDEC-003 naming
  `mars777-1` and NDEC-004 making it a negotiated pre-match term because it sits
  inside the signed core.
- **Correction.** One authority, `SUPPORTED_CONFIG_SCHEMA_VERSIONS`, enforced at
  the single point where a configuration first becomes a value - the domain
  constructor - so no entry path can route around it and no layer duplicates it.
  `UnsupportedConfigSchemaError` subclasses the existing section error, so every
  caller that already classified configuration failures keeps working.
- **Finding (a fixture, not a defect).** A test fixture built "a different but
  valid config" by setting `schema_version` to `9.9.9`. That is no longer a
  representable value, so the fixture varies the board size instead - its intent
  preserved, and its failure was the first proof the authority works.
- **Result.** An unsupported revision is refused at the domain boundary and
  reported at the operator boundary as a local refusal naming the version. The
  frozen configuration digest vector is unchanged.

### Stage 9A-1B2 — test modularity and the 150-line gate

- **Goal.** Clear the known test-file size debt and make the rule enforceable
  instead of auditable.
- **Constraints.** Split by responsibility, never `part1`/`part2`. No production
  change of any kind. No test semantics lost - same assertions, same parameter
  sets, same marks, same skips. Docstrings **count** as code lines: a checker
  that excluded them would reward deleting documentation to pass a size gate.
- **Method, stated honestly.** The splits are a **refactor of existing tests**,
  so no RED was manufactured for moving code. The **checker** is new behaviour
  and was written RED-first: its rule tests (blank lines, comment-only lines,
  inline comments, docstrings, decorators, multi-line expressions, exactly 150,
  151) and its scanner tests (both trees, non-Python ignored, sorted output)
  all failed before it existed.
- **Finding.** The checker's own "this repository is clean" test was RED for the
  whole stage and only went green when the last file was split - which is the
  most useful test in the batch, because it is the one CI will run.
- **Finding.** Two helpers were shared across the new files and had to be
  extracted rather than duplicated (`drop`, `empty_chain`); both lost their
  leading underscore because they became imported names. Two module pairs would
  otherwise have imported each other, so their shared doubles moved into
  modules of their own instead.
- **Finding.** `r7_builders` had twenty-nine consumers. Rather than repoint all
  of them, the implementations were grouped into three modules by what they
  build and the original module became the family's explicit re-export surface -
  the same boundary pattern the production SDK uses.
- **Correction.** An automated import-linker bound a name called `play` to the
  wrong module - two helper modules defined that name. Caught by the suite, not
  by review, and fixed by importing from the module that actually owns it.
- **Result.** Police 13 and thief 12 over-limit files became zero; every original
  test function is present and mapped; production coverage totals are unchanged;
  the gate is now automatic on both operating systems.

### Stage 9A-1C — provider gatekeeper and rate-limit authority

- **Goal.** Close the guideline's generic external-call control and the last
  §8.1 version row, without putting peer gameplay behind a generic queue.
- **Constraints.** Establish REPORT-003's provenance **before** writing code. No
  Gmail. No generic retry, queue or 429 loop on `receive_turn`, `submit_audit`
  or `receive_control`. Local provider limits and peer-negotiated limits stay
  separate authorities.
- **Finding (provenance).** REPORT-003 is **reporting-specific**. Appendix E
  rule 28 says "implement a token-bucket rate-limiter for **sending reports to
  Gmail**"; NET-002 says the same; the book's page for REPORT-003 is the
  reporting page, its sanction is "account suspension", and the chapter map puts
  the Gatekeeper trio inside *9.3 Gmail automation*. So it could not be closed by
  gating tunnel calls, and was not claimed to be.
- **Finding (the provider surface is smaller than it looks).** The only outbound
  provider call in production is a **loopback** read of the locally started ngrok
  Agent API, polled because the API answers 200-with-empty while registering.
  There is no metered cloud quota to protect today - which is exactly why the
  429 machinery is proved against a fake provider rather than claimed against
  this one.
- **Finding (cleanup was already safe).** Teardown makes no provider HTTP call:
  it stops a child process, cancels a task and closes a socket. So the smallest
  safe design was **no** reserved lane - a rate limit cannot strand a tunnel it
  never sees.
- **Correction.** The discovery loop polls twice a second for its whole window,
  so a 30-per-minute default would have broken it. The shipped policy for that
  operation is a ceiling that catches a runaway loop and cannot interfere, with
  retries set to zero because the loop above it already is the retry.
- **Result.** `rate_limits.version` closed as text `"1.00"`, all three §8.1 rows
  met, §5.1/§5.2/§5.3 met for every surface where generic control is safe, and a
  structural test in both directions.

### Stage 9A-2A — the cryptographic Replay Viewer

- **Goal.** Deliver the viewer `REPLAY-001` requires, over existing authorities.
- **Constraints.** No second replay engine - no board movement, barrier
  legality, scent physics, capture truth, commitment hashing or outcome scoring
  of its own. Reachable through the SDK. No GUI. No fabricated screenshot.
- **Finding (the words are the requirement).** `REPLAY-002` does not ask for "a
  status"; it asks the viewer to show **`Verified OK`** and **`TAMPERED`**. Those
  are the literals in the code, and the log's own audit block already used the
  first one - the viewer and the audit now say the same word because they read
  the same authority.
- **Finding (four statuses, not two).** A commitment whose nonce was never
  disclosed to this side is neither verified nor tampered. Collapsing it into
  `Verified OK` would be a false claim and into `TAMPERED` a defamatory one, so
  `NOT_CHECKABLE` is preserved end to end, exactly as the evidence-layered audit
  already did.
- **Finding (development evidence cannot be replayed, and the code says so).**
  The friendly contribution's own docstring states it *"deliberately cannot carry
  a board, a position, a barrier set or a nonce"*. So the viewer refuses it with
  that reason rather than supporting a shape it cannot reconstruct.
- **Correction.** A first structural guard forbade the substring `sha256` in
  viewer modules and failed on `config_sha256` - a **field name**, not a
  computation. The guard now forbids `hashlib`, `hexdigest` and `sha256(`, which
  is what it always meant.
- **Result.** Nine small modules, a command with a three-value exit contract, a
  textual board, containment-checked reads, and 79 tests over a sub-game that
  production really played.

### Stage 9A-2AF — replay audit completeness

- **Goal.** Answer one question about the shipped viewer: can incomplete
  source-required evidence produce a successful verification?
- **Constraints.** Measure before changing. Do not turn `NOT_CHECKABLE` into
  `TAMPERED` to make automation fail, or a real mismatch into `NOT_CHECKABLE`.
  Report `PASS_NO_CHANGE` if the invariants already held.
- **Finding (measured, not assumed).** Success was already safe: a missing nonce
  returned `3`, never `0`. But `3` is documented as *"found something"*, so a
  grader could not tell an accusation from a gap - and a record with no
  commitment to check dragged the whole summary below `Verified OK`, which made
  an inapplicable record look like an incomplete audit.
- **Finding (the source sets the bar).** `LOG_CONTRACT.md` marks the nonce
  `Required`, `CRYPTO-008` releases it at the end-of-game audit, `CRYPTO-007`
  makes a comprehensive audit a precondition for agreeing the result, and
  `REPLAY-002` asks for a recomputation *for each log step*. So "everything that
  happened to be checkable passed" is not the audit the source asks for.
- **Correction.** Exit `4` for an incomplete audit; `worst_check` states the
  ordering as an invariant - a mismatch outranks an absence, an absence outranks
  every verified record, `NOT_APPLICABLE` outranks nothing; a commit entry
  without its `Required` digest is corruption, not a record with nothing to
  check; `audit_complete` exported so a caller never parses text.
- **Result.** Six measured cases, six distinct honest answers, and no accusation
  inflation in either direction.

### Stage 9A-2B — the live and replay graphical interface

- **Goal.** Close `GUI-001`, `GUI-002` and `GUI-003`; give the project a live
  view and a replay view; produce the real screenshots `DOC-001` needs.
- **Constraints.** Do not choose a toolkit before proving it works under the
  project's Windows/Linux/CI constraints. The GUI must never decide a move, a
  barrier, a capture, a scent, a commitment, a verdict, a transition, a score or
  a result agreement. It must never block gameplay. No CDN, no remote script, no
  web font, no analytics. The screenshot must be produced by the real
  application - not drawn, not mocked, not a diagram - and must not present a
  fixture as a tournament match.
- **Finding (the whitelist already existed).** The safest set of facts a live
  window may show is not one to design: it is `Observation`, the value the
  strategy itself is restricted to. Projecting the window from it makes
  `GUI-002` structural - there is no field an opponent cell could arrive in -
  instead of a rule someone has to keep remembering.
- **Finding (the toolkit question had two halves).** `tkinter` ships with the
  interpreter CI installs, so the window costs no dependency; but `Tk()` needs a
  display and no runner has one. Splitting layout from rendering answered both:
  one toolkit-free `Frame`, an interactive adapter, and an offscreen rasteriser
  that runs on every gating leg and produces the screenshots.
- **Finding (the GUI found a defect in something else).** The first *lockstep*
  log ever rendered showed our own turns as `TAMPERED`. The replay viewer keyed
  disclosed nonces by step alone, and in lockstep both sides commit at every
  step, so the peer's nonce overwrote ours and one whole side was recomputed
  against the wrong secret. Stage 9A-2A had not seen it because its fixture
  scripted one role per step. Keyed by `(step, role)`; a whole thirty-five-round
  sub-game now verifies end to end.
- **Finding (the toolkit claim was only half-verified, and CI proved it).** The
  first push failed on Ubuntu and passed on Windows: `tkinter` is standard
  library but *packaged separately* on Debian family, and the Ubuntu runner uses
  the preinstalled system interpreter, which has none. The local check had used
  the uv-managed interpreter instead of the one CI actually runs. Corrected by
  obtaining the toolkit only when a window is built - which the two-adapter
  design already made natural - and by running the graphical suite against an
  interpreter where `tkinter` is genuinely unimportable.
- **Result.** Two windows, one drawing model, 100% coverage of the graphical
  package with **and** without a window toolkit, and two screenshots taken from
  one real sub-game rather than staged.

## 3. Practices this project actually learned

1. **Prove it as a process.** Every in-process proof in this project hid at
   least one defect that a separate OS process exposed immediately.
2. **A stop is a result.** Stage 8A-2 delivered more value by stopping with zero
   changes than it would have by working around a false premise.
3. **Fix at the owner.** Every live divergence was traced to a rule or a state
   owner and fixed there — never at the symptom, never by loosening a guard.
4. **Never bend an identity to fit a rule you own.** Amend the rule you own;
   leave the frozen identity alone.
5. **Measure the way the standard defines the measure.** Counting physical lines
   against a code-line rule produced a wrong answer by more than a factor of two.
6. **Name what is absent.** `ABSENT`, `counted_eligible: false` and a rejected
   strategy candidate are all more useful than a tidy document.
7. **Read the standard's own words before satisfying it.** `1.00` looked like a
   literal to copy; it is a value to represent. Copying it would have created the
   drift the clause exists to prevent.
8. **When code moves, move the guard with it.** A structural test that fails
   because its subject moved is a test to retarget, never one to delete.
9. **Agreement is not compatibility.** Two parties holding identical bytes is a
   different fact from either party being able to run them, and only one of the
   two was ever checked.
10. **A rule nobody checks is a claim.** The 150-line rule was published,
    audited by hand three times, and still drifted. It stopped drifting the day
    a command returned a non-zero status.
11. **Read what a requirement governs before satisfying it.** The book's
    rate-limiter is about Gmail sends. Building one for tunnel calls is good
    engineering and closes a different clause; calling it REPORT-003 would have
    been a false claim with a real test behind it.
12. **Sometimes the requirement names the output string.** `Verified OK` and
    `TAMPERED` are not a status vocabulary to design; they are the words the
    grader is told to look for.
13. **A green result must say what it verified.** "Everything checkable passed"
    and "everything required was checked and passed" are different claims, and
    only the second deserves exit zero.
14. **Build the view that the rules already permit.** The hardest part of the
    GUI was deciding what it may show; the answer was a value that already
    existed, and reusing it turned a prohibition into a shape.
15. **A new consumer is a new test of an old component.** The replay viewer had
    tests, a document and a green suite. Rendering one log it had never been
    given - a lockstep one - exposed a false accusation of cheating in it.
    A fixture that only ever exercises half a shape proves half a component.
16. **Verify against the interpreter that will run it, not the one at hand.**
    "The standard library has it" and "this machine has it" are different
    claims, and so are "my interpreter" and "CI's interpreter". The gap between
    them was one `apt` package wide and failed an entire gating job.
