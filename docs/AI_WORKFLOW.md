# AI Workflow - group MaRs-777

> **Status: DRAFT.**

## Roles

- The **human** receives a prompt from the supervising reviewer.
- **Claude Code** performs repository and terminal work inside a single repository.
- Claude returns an **evidence report** (exact commands + results).
- Work is **reviewed** before any commit or push.

## Principles

- No implementation before an approved plan.
- No commit/push without explicit instruction.
- Exact command/result reporting; explicit statement of what was not verified.
- Stage prompt texts (e.g., Stage 0A through Stage 0C) may be recorded or
  referenced in `docs/PROMPTS.md` **without** including any secrets.
- Stage 0C established the two private GitHub remotes (owner mohammedawad99),
  pushed the initial commit over **SSH** (the OAuth token lacked the `workflow`
  scope), and achieved green CI on Ubuntu + Windows; commits and pushes happen
  only under explicit reviewer approval, and no authentication output or secret
  is ever recorded here.
- Stage 0D found that branch protection / rulesets are **unavailable** on the
  current GitHub plan for private repositories (a platform limitation, reported,
  not worked around).
- Stage 1A was a **specification-only** extraction of the authoritative 160-page
  book v3.0.0 into `docs/spec/` and the traceability/conflict artifacts. No game
  logic, JSON schema, or protocol code was written. All extracted requirements
  cite book pages. The Stage 1B independent cross-audit and the **supervising
  review (PASS)** have since accepted this corrected baseline; the four JSON
  contracts were built and reviewed in Stage 1C/1D/1D.1 (now **LOCKED**).
- Stage 1B independently re-audited the Stage 1A artifacts against the PDF and
  applied corrections (Appendix F has **32** parameter rows — 14 FIXED / 9 MINIMUM
  / 9 NEGOTIABLE — not 26; `technical_loss` 0/0 is binding via Ch 3 + App E #48 but
  is **not** an Appendix F row; `num_games` is **6, FIXED**; exact catalog modality
  MUST 76 / MUST NOT 9 / SHOULD 4 / MAY 2). Still specification-only; no code,
  schema, commit, or sibling access. Stage 1B review = PASS; the corrected
  baseline is approved for Stage 1C.
- Stage 1C defined **contracts** for the four mandatory JSON artifacts in
  `docs/spec/json/` — specification only, no JSON files/schemas/serializers/code.
  Every field is provenance-classified (SOURCE-EXPLICIT / SOURCE-SEMANTIC /
  PROJECT-CONTRACT / EXAMPLE-ONLY / REVIEW-REQUIRED); project decisions are JDEC-001…011.
  Contracts were **reviewed and approved** (Stage-1 lock); **implementation has not
  begun**; **Stage 1D** independently audited them (below) before any synchronization
  or implementation.
- Stage 1D independently audited and **locked** the contracts for interoperability:
  `verdict` = `intent` (C-08); `game_uid` confirmed **source-named** (kept); `state`
  PROJECT-LOCKED; `config_sha256` non-self-referential; every interop dependency is
  SOURCE-LOCKED, PROJECT-LOCKED, or NEGOTIATED-PRE-MATCH — **0 blocking**.
  Specification-only; no code/schema/sibling access; **reviewed and LOCKED**.
- Stage 1D.1 **corrected** the cryptographic/reporting contract: Step-0 and the config
  signature exchange are **keyed authentication with a pre-supplied key** (SOURCE-
  REQUIRED; HMAC-SHA256 default = PROJECT-CONTRACT, JDEC-013) — **not** unkeyed SHA-256
  digests and **not** invented PKI; the reporting-sanction conflict (Ch 9 vs App E #35) is
  recorded as **C-09** with the strictest 0-both rule. *(Stage 1D.1's K3 — that the result
  itself must carry FastMCP endpoints and signed hardware declarations — was later
  **superseded by Stage 2A-R2/JDEC-014**: that static metadata is declaration-owned and the
  result references it.)* Registers **at that stage**: NDEC-001…007, JDEC-001…013,
  INV-01…15; **current: JDEC-001…015**. The crypto taxonomy is kept precise
  (HASH ≠ MAC ≠ PKI signature ≠ mutual acknowledgement); **no key material** in any
  artifact. Specification-only; no code/schema/sibling access; **reviewed and LOCKED**
  (committed at Stage 1-CLOSE; status relabel at Stage 1-CLOSE.1).
- **Phase 2 (Stages 2A → 2-CLOSE)** froze the architecture and authored all seven PRDs.
  Stage 2-CLOSE resolved the two final cross-contract issues **without changing any locked
  contract**: the series convention is negotiated protocol metadata (not a declaration field)
  and the declared MCP endpoint is a stable group-level ingress. **PRD-01…07 are
  APPROVED — PHASE 2 LOCKED; implementation has NOT started.**
- **Phase 3 (Stage 3A →)** is the first implementation phase. Stage 3A was driven
  **tests-first**: every domain test was written and observed failing in both repositories
  before any production module existed. It delivers only the deterministic, role-neutral
  foundation - grid configuration, coordinates, board geometry with blocked cells, the
  five-token move set, movement legality and safe move application. The project grid
  minimum is enforced by `GridConfig`, deliberately **not** by the policy-free `Board`
  geometry, per the frozen domain-layer boundary. **PRD-01…07 remain APPROVED — PHASE 2
  LOCKED**; the deterministic core is **not** complete and no protocol, networking,
  cryptography, strategy, GUI or reporting code exists.
- **Stage 3B** completed the deterministic game-rule layer tests-first: barriers,
  capture, terminal/survival, scoring and bounded scent physics. Two supervising
  corrections were applied. **JDEC-015** records a source *gap* — Appendix F fixes two
  independent MINIMUM-35 step limits but Ch 3 Table 2 defines no outcome when the
  ceiling precedes the survival threshold, so `survival_threshold <= max_moves` became
  an admissibility condition instead of an invented terminal. **C-10** records a source
  *contradiction* — Ch 4 §4.3 defines tau in [0, 0.9] yet writes the update with a lower
  clamp only, so the state domain wins and the recurrence saturates. Registers are now
  **JDEC-001…015** and **C-01…C-10**; every authoritative count is unchanged. Turn
  orchestration, protocol, networking, cryptography, strategy, GUI and reporting remain
  **not implemented**; PRD-01 stays **IN PROGRESS** and PRD-02…07 **NOT STARTED**.
- **Stage 3C** opened the application layer with the **local** turn-execution step,
  tests-first. Supervising review accepted it except for one state-ownership defect:
  `LocalTruth` carried a `barriers_placed` counter that duplicated the public board's
  barrier facts and could drift from them, and it was police-only state sitting in a
  role-neutral object. **Stage 3C-FIX1** removed it; remaining budget is derived from
  `max_barriers - len(board.blocked)`, and `STATE_OWNERSHIP.md` anti-duplication rule 2
  is satisfied. No architecture document was changed. **PRD-02 is now IN PROGRESS**
  for this one slice; the state machine, orchestrator, ports, FastMCP, networking and
  cryptography remain **not implemented**, and PRD-03…07 stay **NOT STARTED**.
- **Stage 4A** added the local protocol phase machine, tests-first, pinning the frozen
  graph literally rather than against the implementation: an exhaustive 324-pair sweep
  makes a hidden or missing edge impossible. Supervising review then found a genuine
  contradiction inside the frozen table itself - TECHNICAL_LOSS was absorbing although
  the same table makes "technical loss" an entry condition of SUBGAME_COMPLETE, tells
  the phase to "proceed per series rules", and excludes it from rule R5. **Stage
  4A-FIX1** added the single edge `TECHNICAL_LOSS -> SUBGAME_COMPLETE` and recorded the
  reasoning in `STATE_MACHINE.md` §4 as an implementation-discovered architecture
  correction - not a lecturer rule, not a source conflict, no register increment.
  Primary source agrees: Ch 3 Table 2 lists technical loss as a **sub-game** end event
  scored 0/0 beside capture and survival. TAMPERED keeps its severe, non-repairable
  status. PRD-06 remains **NOT STARTED** despite the crypto-named phases.
- **Stage 4B** added transition evidence, tests-first. The instructive part was what
  the stage did **not** build. The prompt allowed typed transition signals, but an
  audit of every source and architecture document found **no frozen transition-signal
  vocabulary** - `PROTOCOL_TIMELINE.md`'s 15 numbered events are protocol-timeline
  entries, not state-machine signals - so inventing a 31-value event enum would have
  created a second representation of a graph that already exists once. The target
  phase stayed the typed request. Likewise, the per-state Evidence column names
  artifacts, hashes and log entries, but event 10 fixes the *state machine's* share as
  literally "phase transition" with persistence and hashing both "—", so evidence is
  the two phases and nothing else. Supervising review then raised two close-critical
  points. **Stage 4B-FIX1** answered the first by making evidence **valid by
  construction**: R7 records a *successful* transition and R1/R5 forbid the skips, so
  a value naming a non-edge could never be truthful. Validation reuses `_ALLOWED`
  directly - one dict literal, one enum class in the module. That deleted the old
  negative test's subject, and the honest fix was to move the corruption boundary
  forward to the constructor and **add** replay negatives (duplicated record,
  out-of-position record) rather than relax the constructor to keep an obsolete test
  alive. The second point was a reported contradiction between a "153-line" file and
  "0 files over 150"; it resolved as a **units error in the report** - 153 was the
  cross-repo semantic-diff count, physical LOC was 150 - and a repository-wide sweep
  of all 48 `*.py` files per repo proved max 150 and 0 over. Throughout, the honest
  claim was kept narrow: structural validity is not authenticity, and phase replay is
  not game replay. PRD-06 and PRD-07 remain **NOT STARTED**.
- **Stage 4C** added the local orchestrator, tests-first, and its lesson was about
  *authority* rather than code. The ownership audit had to reconcile two frozen
  documents that disagree: `MODULE_BOUNDARIES.md` lists "turn cursor, sub-game
  index" as `app.orchestrator` state, while `STATE_OWNERSHIP.md` - the authority
  for mutable-state ownership - puts turn/step under `domain.truth`. The
  already-approved D17 precedent settled it, so no turn cursor was stored and no
  blocker was raised. The same audit found that the table *also* assigns the
  **recorded score** to the orchestrator; that responsibility was reported and
  **deferred**, not silently dropped and not quietly implemented, because its
  input is a terminal `Outcome` the local agent cannot yet know. Role alternation
  was likewise refused: PRD02-FR-011 makes it a negotiated `SeriesLauncher`
  convention with no silent default, so nothing was derived from an odd/even
  index. The real defect surfaced at review. Stage 4C had implemented the series
  length as a floor (`>= 6`) on the strength of one sentence in
  `CONFIG_CONTRACT.md` - "6 (or the agreed higher)" - without checking it against
  Appendix F's own status table, which lists `num_games` under **FIXED** and
  defines FIXED as "binding, unchangeable; deviation disqualifies". **Stage
  4C-FIX1** corrected the code to exact equality and, because the stale wording
  really was in the committed tree (in `CONFIG_CONTRACT.md` and the C-05 impact
  cell), narrowed those two sentences to the meaning App F and C-05 had already
  locked - no new JDEC, conflict or requirement. The lesson is the authority
  hierarchy the project already had: a derived contract sentence never outranks
  the Appendix-F status it is derived from. The error was caught before commit,
  and this record keeps it rather than hiding it.
