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
- **Stage 4D** was authorized to build the application port contracts and instead
  stopped before writing a single line, which is the outcome the process is for.
  Three internal contradictions made a truthful implementation impossible:
  `API_BOUNDARIES.md` says in its own header "**No Python signatures are fixed
  here**", and a repository-wide search of every architecture and PRD document
  found no `def`, no `Protocol` and no return annotation - so every method name
  would have been invented; the `app.ports` row allowed **stdlib typing only**
  while the same architecture defines `GameRulesPort` over board/action/config and
  `ScoringPort` over outcome to per-role scores, leaving those ports
  unrepresentable in the module assigned to them; and `PLAN.md` still claimed 18
  ports where the frozen table has 20. The tempting move was to ship a thin
  `ClockPort` with a `monotonic() -> float`, since that is the one port whose input
  is "—" and whose headline output is a stdlib scalar. It was refused: the method
  name is not frozen, and the row's own Returns column also lists deadlines and
  timers whose machinery `CONCURRENCY_MODEL.md` assigns to the Watchdog, the
  Deadline timers and the executor. Shipping a third of a port under its full name
  would have been an overclaim. **Stage 4D-R1** repaired the architecture instead
  of the symptom, changing exactly one cell of one module row - dependency
  inversion is aimed at concrete adapters, not at the domain model, and `app`
  already imports `domain` - and recorded that any future Python signature is a
  **PROJECT-CONTRACT**, never source- or reference-mandated. The analysis also
  found that not every row named `*Port` needs a Protocol: wrapping a pure
  deterministic domain function the orchestrator may already call directly adds
  indirection without substitutability. The blocked stage is kept in the record as
  evidence, not erased.
- **Stage 4E** stopped before code for the second time in a row, and the reconciliation
  that followed is the more interesting half. The stage was scoped to build internal
  semantic peer-message values in `protocol.messages`, and the audit found the home
  itself was wrong: that row is a **wire** boundary, while `CONCURRENCY_MODEL.md` has
  the server "validate, convert to an **event**, and submit it to the executor queue" -
  and the Turn Executor is `app`. Since `app` may never import `protocol`, a semantic
  value the executor consumes simply cannot live there. That turned a naming debate
  into a proof. The second blocker looked worse: PRD02-FR-044 required every inbound
  message to carry `(sub_game, step, phase)`, yet nothing anywhere defines step
  numbering, the pre-turn value, or what `phase` even denotes. The temptation was a
  `step=0` sentinel. Instead the answer came from inside PRD-02: **FR-063**, the
  requirement that actually names the "cursor guard" and traces to R8 exactly as
  FR-044 does, lists only **sub-game and step**, while the phase rejection is
  **FR-062** under **STATE-003** - a receiver-side check against the receiver's own
  machine. A state-machine walk confirmed it: turns are lockstep, so a transmitted
  phase is either constant per message family (redundant) or not independently
  computable (peers sit in different phases at the same moment). Narrowing FR-044
  dissolved the phase-dependency blocker for free, because nothing needs to transmit a
  phase at all - and the single `ProtocolPhase` stayed exactly where it was. The audit
  also caught an omission in the project's own earlier planning: the peer-visible
  family count is **10**, not 9; Event 8 "Move validation" transmits accept/reject and
  had been dropped. Both the blocked stage and the miscount are kept in the record.
- **Stage 4F** audited nine value representations and stopped before code again, this
  time on a subtler problem: two representations were genuinely ready, but there was
  nowhere legal to put them. A SHA-256 digest is produced by `protocol.commitment` and
  `protocol.config_lock` and carried by `app.peer_messages`, and no module in the frozen
  table was reachable by all three. The easy answers were both wrong - duplicating the
  validator per layer would have created the semantic drift the anti-duplication rule
  exists to prevent, and a `types.py` would have been the junk drawer the stage brief
  explicitly forbade. **Stage 4F-R1** fixed it by first correcting the project's own
  analysis: `infra.logger`, `infra.artifacts` and `infra.reporter` had been listed as
  consumers, but they are **mappers** - they serialize whatever structured record they
  are handed, and that record already reaches them through `app.ports`. With the real
  consumer set down to three, one inner contract module plus two narrow type-reference
  dependencies sufficed, reusing the pattern Stage 4E-R1 had already established. Two
  representation defects surfaced in the same review. The digest had been called
  ready while its case policy was called unresolved - a contradiction in one report;
  resolving it meant separating **algorithm** (SOURCE), **encoding** (project-locked
  hex), **length** (entailed by SHA-256) and **case** (genuinely free), then adopting
  lowercase as a labelled PROJECT-CONTRACT that **rejects** uppercase rather than
  silently rewriting it. And `RESULT_CONTRACT.md` turned out to define
  `mutual_agreement` as a bool in its field table, scoring rule and example while its
  approval-core prose treated it as an object whose `.sha256` duplicated the separate
  `result_sha256` - the prose was the stale side, and correcting it kept the locked
  11-field result count intact. Seven representations remain deferred rather than
  guessed.
- **Stage 4F resumed** and delivered the two values the reconciliation had made
  placeable, and the interesting part was again what supervising review caught after
  the tests were green. The implementation was correct on every semantic axis - strict
  lowercase 64-hex, uppercase refused rather than normalised, no hashing, the closed
  `Verified OK` / `TAMPERED` pair - yet `InvalidDigestError` subclassed bare
  `Exception`. That looked harmless until you noticed its sibling in the same module:
  `FinalAuditVerdict("OK")` raises `ValueError` natively, so the two values disagreed
  about what a malformed construction *is*, and a caller writing `except ValueError`
  would have caught one and missed the other. It was also the only application error
  missing from a package surface that exports every other one. **Stage 4F-RESUME-FIX1**
  fixed both in two lines of production change, driven by a fresh RED of six failures.
  The lesson is that an API can be semantically flawless and still be inconsistent with
  the language it is written in, and with the project's own conventions - neither the
  test suite nor the type checker had any reason to complain.
- **Stage 4E-R2** was scheduled to unblock message implementation, and its most useful
  output was three *refusals*. Paying the tracked debt was straightforward - the
  `app.peer_messages` row allowed only "stdlib typing" and could not name
  `app.protocol_values`, so a message literally could not hold the `Sha256Digest` the
  previous stage had built for it - and the fix rhymed with 4F-R1-FIX1 closely enough
  to be routine. What was not routine was declining to grant `enum` "while we are in
  there": no peer message defines a vocabulary of its own, `Move` and
  `FinalAuditVerdict` already exist, and a permission granted early is a permission
  someone eventually uses. The cycle question got the same treatment: rather than
  writing "`app.protocol_values` must not import `app.peer_messages`" as a rule to be
  obeyed, the note records that it *cannot*, because its allow-list is pure stdlib -
  a structural argument needs no discipline to hold.
  Then the family audit contradicted the plan. The stage brief flagged Reveal and
  Mutual result agreement as high-priority likely-ready; both turned out blocked, and
  for reasons no amount of enthusiasm could paper over. A police turn may legally be a
  barrier placement instead of a move, and BAR-001 requires the **exact cell** to be
  declared openly - yet every contract describing the reveal says `move` + `hint`, so a
  `(cursor, Move, hint)` record cannot express a legal police turn at all. That is not
  a missing field; it is a missing contract. And result agreement failed on a residue:
  Stage 4F-R1 corrected `RESULT_CONTRACT.md`'s `mutual_agreement` from object to bool
  but never reached NDEC-006, which still says `.confirmed`. Worse, the corrected
  contract sets the bool *after* the peers exchange hashes, so a single message cannot
  honestly carry both its own digest and a verdict about agreement it has not yet
  reached. Acknowledgement was the opposite case - two of its three open questions
  dissolved once PRD06-FR-082 was read properly (the ack binds a *specific* digest for
  a *specific* cursor, which settles both whether the digest is repeated and whether
  `ack_of_step` is a second field) leaving one genuinely open question about the acking
  role. One family out of ten survived: Commitment, whose timeline row says
  "`H_commit` **only**", the rarest thing in this specification - an explicit
  exclusivity statement. The lesson is that a readiness audit that returns the answer
  the brief expected has probably not been performed.
- **Stage 4E-R2-FIX1** was scoped as a two-item cleanup and turned into a lesson about
  how far a withdrawn decision travels. Supervising review had spotted that NDEC-006
  still carried the `mutual_agreement.sha256` / `.confirmed` object form Stage 4F-R1
  removed from `RESULT_CONTRACT.md`, and the instruction was to correct that one cell.
  Correcting it was easy. Running the sweep the instruction implied - every current
  occurrence, classified CURRENT versus HISTORICAL - was not: the same withdrawn shape
  is still asserted by **PRD06-FR-142**, **PRD07-FR-085** and **PRD07-FR-190**, and
  FR-085 contradicts FR-080 four rows above it in the same table. Stage 4F-R1 had
  corrected the document it was looking at and, reasonably, assumed that was the
  contract; Stage 4E-R2 then found one more and, equally reasonably, assumed *that* was
  the last. Both were wrong for the same reason: nobody had asked "where else does this
  shape live?" until a sweep was mandated. The honest consequence is that this stage
  closes **PARTIAL** - the object form is gone from `docs/spec/**` but is not extinct,
  and the PASS wording would have asserted it was.
  The provenance turned out to be the interesting part. The nesting is not a project
  invention: it is the shape of the lecturer's extracted attachment example, recorded as
  secondary provenance, which PRD07-FR-087 already says is not a verified parser schema.
  It reached three PRDs because attachment compatibility was in view while they were
  written. That reframes the remaining fix from "correct an error" to "stop treating a
  compatibility example as a contract" - and it means no source requirement is at risk,
  because Ch 9 requires a SHA-256-backed mutual approval, never a nesting.
  The error-contract half went the other way: the audit *reduced* the plan. The obvious
  move was a narrow `ValueError` subclass, matching `InvalidDigestError` next door. But
  the same module also contains `FinalAuditVerdict`, which raises **native** `ValueError`
  and has a test asserting exactly that - so the project already had a precedent for a
  new semantic value needing no custom error, and `InvalidDigestError` being a
  `ValueError` subclass means one `except ValueError` covers both modules regardless.
  The deciding argument was asymmetry: adding a narrow subclass later is non-breaking,
  removing one is not. So the contract is built-in `ValueError`, zero supporting types,
  written down now rather than discovered during TDD - which was the actual point of the
  exercise.
- **Stage 4E-R2-FIX2** was the cleanup FIX1's PARTIAL had scoped, and it is worth
  recording how ordinary it turned out to be once the sweep had already been done. The
  three PRD rows were corrected in place in a few minutes; the hard work had been the
  sweep that found them, one stage earlier. The lesson generalises: a contract
  correction is cheap, and *knowing where the contract is asserted* is what costs. Two
  stages had each corrected the one document in front of them and stopped.
  The genuinely interesting half was the constant dependency, because it looked like a
  formality and was not. The `app.peer_messages` row permitted "immutable `domain` value
  **types**". `FIRST_SUB_GAME` and `FIXED_NUM_GAMES` are not types - they are
  module-level `Final[int]` constants - so the row did not authorize them, and the
  tempting move was to read "value types" loosely and move on. That is exactly the
  reading this project has now refused three times: at 4D-R1 for `app.ports`, at
  4F-R1-FIX1 for `app.protocol_values`, and here. An allow-list that is only true if you
  squint is not an allow-list.
  Choosing the fix required rejecting three plausible alternatives. A literal `6` in the
  message module, or a copied constant, would have created a *second* authority for a
  number Appendix F marks FIXED with "deviation disqualifies" - the cheapest possible way
  to lose a match years from now. Deriving the bound from a `SeriesConfig`, which was
  already permitted and therefore needed no architecture change at all, was the subtlest
  wrong answer: it would have made a *transmitted* cursor look like it depended on locked
  configuration it does not carry, or forced a third field onto a value frozen at two.
  The bound a cursor needs is the global constant, not a config value, and those are
  different things even when they hold the same integer. Checking the claim mechanically
  was worth the thirty seconds: exactly one `= 6` exists in the source tree, and
  `app.orchestrator` was already importing `FIRST_SUB_GAME` at runtime - so the widening
  documented a dependency the codebase had been relying on lawfully all along, which is
  the most comfortable kind of architecture correction to make.
- **Stage 4E finally resumed**, ten reconciliation stages after it was first blocked, and
  the striking thing is how small the result is: two classes, 96 lines. Everything that
  made it possible was the argument, not the code. The module could not have been written
  in the shape the original Stage-4E prompt imagined - there was no legal home for the
  values, no permission to hold a digest, no permission to read the sub-game bound, and
  nine of the ten families still have no frozen payload. What shipped is precisely the
  part that survived every audit.
  Two implementation choices are worth recording because both were tempting to get wrong.
  The first is `type(x) is TurnCursor` instead of `isinstance`. That looks pedantic until
  you write the adversarial test: a `Sha256Digest` subclass can override `__post_init__`
  and thereby *weaken* the validation the composition is relying on, and `isinstance`
  would wave it through. Exact identity refuses it. The second is the deliberate absence
  of an upper bound on `step`. Every instinct says a step number should be bounded, and
  `max_moves` is sitting right there in the config - but it is *per-sub-game locked*
  configuration, and a transmitted cursor does not carry it. Embedding it would have made
  a structural contract silently depend on state the value has no access to, which is the
  same category of error as the "value types" wording that blocked this module twice. The
  test that proves the point accepts `step = 10**9` and says why.
  The RED came twice, which is the useful part of the record: once for the missing module,
  and once - after the implementation was complete and correct - for the missing export on
  the exhaustive public surface. The second failure is the one a less strict convention
  would never have caught, and it is the same class of defect Stage 4F-RESUME-FIX1 found
  by review rather than by test. This time the test found it first.
- **Stage 4E-R3** is the clearest example so far of why "read the source, not your own
  notes" is a rule and not a slogan. Stage 4E-R2 had blocked Reveal on a finding I still
  believe was correctly reported: no *project* contract said how a police barrier and its
  exact cell reach the peer, and a `(cursor, Move, hint)` record could not express a legal
  police turn. What R2 never did was go back to the book. Chapter 5 page 51 defines the
  sealed `Move` as "the physical action - the chosen action (movement, **barrier
  placement**, etc.)", and the Reveal step sends "the action (Move) and the verbal
  sentence". Chapter 3 page 37 adds that a turn is a single action, that the police may
  place a barrier only in a turn where he forgoes movement, and that every placement and
  its **exact location** must be declared truthfully and never in hiding. The source had
  answered the question all along; our derived contracts had quietly narrowed "action" to
  "move" and then the narrowing propagated. That is a documentation defect of exactly the
  kind the `mutual_agreement` nesting was - a wrong shape copied forward until someone
  went back to the primary text.
  The honest consequence is mixed, which is the point. Reveal did **not** become ready: the
  semantics are now settled, but there is still no shared action *type* in a home both the
  commitment producer and the message module can reach, and the sealed `move` value's
  canonical representation is unfrozen where `state`'s was frozen years of stages ago by
  NDEC-002. Those are smaller and much better-named blockers than "no contract says how a
  barrier reaches the peer", but they are real, and inventing a JSON shape to close them
  would have broken commit/reveal verification for a peer who agreed a different one.
  Acknowledgement went the other way and cost almost nothing. The whole source content is
  one sentence - the opponent confirms it received the commitment and is locked onto it -
  and the `by_role` question dissolved once it was asked precisely: the book names an
  acknowledging party, but Figure 6 carries that party as the *direction of an arrow
  between two lifelines*, not as a field. A local writer always knows the direction, and
  the role is frozen at config lock, so the log can persist `by_role` truthfully while the
  message never carries it. The nice side effect is a security one nobody asked for: a
  field that is never transmitted is a field a hostile peer cannot forge.
