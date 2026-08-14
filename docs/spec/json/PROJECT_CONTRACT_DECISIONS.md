# Project-Contract Decision Register (JDEC) — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Every PROJECT-CONTRACT choice, made **only** where the book leaves the
representation open (academic-freedom basis, PDF p.5 / book v). None overrides a
binding source requirement; none is claimed lecturer-specified. Conservative,
simple, reversible representations are preferred.

| JDEC | Decision | Source freedom (why allowed) | Options considered | Selected | Why | Interop impact | Security impact | Future test | Reversal cost |
|---|---|---|---|---|---|---|---|---|---|
| **JDEC-001** | Key spelling = `snake_case` for all SOURCE-SEMANTIC keys | book names meanings, not keys | camelCase / snake_case | snake_case | matches the App B SOURCE-EXPLICIT keys (`grid_size`, `capture_cop`) | must be agreed with opponent for shared files | none | schema lint | low (rename) |
| **JDEC-002** | Canonical serialization params: `sort_keys=True`, `separators=(",",":")`, UTF-8, LF, no trailing newline in hashed payload; **`ensure_ascii=False`** *(Stage 4E-R9-R1 pinned the exact value here and in `CANONICALIZATION_CONTRACT.md`/NDEC-003; it was previously written only as "fixed & agreed", which left it an implementation-time choice even though PRD06-FR-005 already carried the value)*; locale-independent number formatting | Ch 5 requires "canonical, sorted keys, fixed separators, UTF-8, byte-identical"; exact params/`ensure_ascii`/line-endings unspecified | reference params vs custom | **reference-code params** + explicit `ensure_ascii`/LF rule | reproduces the book's reference hash behavior; deterministic cross-OS | **critical**: both peers must use identical params or hashes differ | correct hashing prevents false TAMPERED | cross-impl byte-identity test | medium (affects all hashes) |
| **JDEC-003** | `schema_version` optional, informational (`"mars777-N"`); no version handshake | book prints the key but binds no value/compat rule | mandatory 1.2 / optional project value / omit | optional project value | `1.2` is illustrative; no handshake mandated | none (informational) | none | presence check | trivial |
| **JDEC-004** | `<NN>` = 2-digit zero-padded (`g01`…`g06`) | book writes `g<NN>` without a width | 1-digit / 2-digit / 3-digit | 2-digit | lexical=numeric order; ≤10 fits 2 | filenames must match opponent's expectation | none | filename regex | low |
| **JDEC-005** | `game_id` = opaque `[a-z0-9-]` string (e.g., `<a>-vs-<b>-<yyyyww>-<uid>`); `game_uid` short shared token | book requires uniqueness + filename derivation, not a format | freeform / structured | structured, filesystem-safe | uniqueness, no file mixing (App F §2.3) | agreed at declaration | none | uniqueness test | low |
| **JDEC-006** | Declaration key names (hardware `os/cpu_cores/cpu_freq_ghz/ram_gb/gpu/vram_gb`, `teams.<g>.*`) | Ch 5/9 require the info, not keys | flat / nested-by-team | nested-by-team | groups per-team data cleanly | shared file → agree keys | none | schema lint | low |
| **JDEC-007** | Log entry nesting: `entries[]` with `phase` ∈ {commit, ack, reveal}; hashed `sealed_record` is a separate object | Ch 5 names the fields/flow, not JSON layout | one-object-per-turn / event-list | event-list (`entries[]`) | maps Commit→Ack→Reveal→Audit; auditable | replay must parse same shape | must not leak nonce early | replay round-trip test | medium |
| **JDEC-008** | Result scores: `sub_games[]` array + `cumulative{}` | Ch 9 requires per-sub-game + cumulative, not keys | flat / array+cumulative | array+cumulative | clear per-game + totals | grader parses | none | scoring test | low |
| **JDEC-009** | Four GitHub links = object with 4 explicit keys (`group_a_police`, …) | E-49 requires four links; no key given | array(4) / 4-key object | 4-key object | unambiguous role/team mapping | grader parses 4 links | none | link-count test | low |
| **JDEC-010** | Internal hash storage: `config_sha256`/`result_sha256` stored **outside** the bytes they cover (non-self-referential). **[MODIFIED — Stage 1D non-self-ref; Stage 1D.1 K1/K2]** Step-0/config authentication is **no longer REVIEW-REQUIRED**: it is **keyed authentication** (JDEC-013, NDEC-005/007), envelope `{auth_alg,key_id,auth_tag}` stored outside the authenticated core; **key out-of-band**. | book states hashes/keyed signing exist, not exact primitive/storage | embedded / sidecar | **outside** the hashed/authenticated bytes (declaration/config sidecar) | conservative; non-self-referential; primitive negotiated | **no secret material stored** (only `key_id`) | hash/tag-presence test | low | supersedes the old "defer interop signatures" note |
| **JDEC-011** | Timestamps = ISO-8601 UTC (`Z`) strings | Ch 9 requires times, not a format | epoch / ISO-8601 | ISO-8601 UTC | human+machine readable, unambiguous TZ | agree with opponent | none | format test | trivial |

| **JDEC-015** | Terminal threshold admissibility: a counted configuration MUST satisfy `survival_threshold <= max_moves`; a violating configuration is refused before `CONFIG_LOCKED` | App F T15 #3/#4 fix only the two MINIMUM-35 floors and let both be raised **independently**; Ch 3 Table 2 defines exactly three end events (capture, prolonged survival, technical loss) and **no** outcome for a survival threshold the step ceiling can never reach | (a) invent a terminal for `max_moves` reached first (tie / survival / capture / technical loss) · (b) let the sub-game run past its own ceiling · (c) treat the combination as an inadmissible configuration | **(c) admissibility invariant `survival_threshold <= max_moves`** | Preserves every source-defined terminal outcome instead of inventing a fourth; keeps both MINIMUM-35 floors intact; the only alternative that adds no game rule | both peers must reject the same configurations before play; refusal happens pre-`CONFIG_LOCKED`, never mid-game | none (no key, hash or nonce involvement) | admissibility unit tests (35/35, 40/35, 40/40 accepted; 35/40 rejected) | low (validation-only; no artifact field, no numeric change) |
| **JDEC-016** | Capture-resolution turn contract: `Reveal` gains a nullable `capture_claim` (one cell), and the operation carrying it answers with `TurnOutcome(accepted, capture)` where `CaptureAnswer` is exactly `NO_QUESTION` / `NOT_CAUGHT` / `CAUGHT`; the current strict counted-turn posture is `STRICT_COUNTED_MATCH_TURN_OUTCOME_V1` | The source requires capture by contact, by barrier and by trapping, and truthful capture declarations, but fixes no bytes for them; the previous legality-`bool` result was PROJECT-CONTRACT (C-12) and is corrected by C-13 | (a) a new peer family / wire kind / FastMCP tool for capture · (b) a control-channel adjunct · (c) an adjunct on the existing Reveal plus a typed operation result | **(c) adjunct on the existing Reveal, typed result** | Capture belongs to the turn that asks it; the lecturer reference likewise carries `capture_claim` on its turn message, so the request stays reference-compatible while the synchronous result removes the reference's deferred-answer ambiguity | both peers must agree the posture **before** `CONFIG_LOCKED`: `STRICT_COUNTED_MATCH` keeps its legacy legality-`bool` meaning and is **not** accepted for current counted play | none — `capture_claim` and `TurnOutcome` are outside `H_commit`; the sealed eight-member record is unchanged | codec round-trip, live runtime and two-agent real-FastMCP capture tests | low (no register growth: tools 4, families 8, kinds 9, ports 21, errors 22) |
| **JDEC-017** | Scent pre-game model contract: the complete agreed emission/decay model is a separate semantic `ScentModelAgreement` (id, the three FIXED App-F values, 25 kernel weights, worked examples) carried in full by the existing `ConfigProposal`, agreed by exact three-way comparison, identified by an unkeyed `scent_model_sha256`, bound into `ConfigLockContext` under the existing keyed config-auth proof, frozen for `g01…g06`, and persisted with the config artifact | `SCENT-001`/`SCENT-003` require the full model to be exchanged, verified and locked, but the book fixes no representation for a scent model — no class, no key set, no canonical byte form and no digest — so the carrier and the bytes are open (C-14) | (a) widen `NegotiatedConfig` beyond its 35 members · (b) a new peer family / wire kind / FastMCP tool for the model · (c) a fifth artifact family or sidecar for the model · (d) a separate semantic model on the existing proposal + a separate digest in the existing lock context | **(d) separate model, existing carrier, separate digest in the existing context** | Keeps the Appendix-B core and `config_sha256` exactly as they were, adds no message and no file, and still makes the model as strongly bound as the config — the same keyed proof covers both identities because both digests sit in the one context it authenticates | both peers must exchange, compare and lock the **same complete model** before `CONFIG_LOCKED`; a missing or valid-but-different model refuses counted play with the existing `E-CONFIG-MISMATCH` | none — the model is public physics, the digest is unkeyed, and only `key_id` and a tag are ever persisted | strict agreement, crypto-lock differential, series-freeze and artifact tamper suites | low (no register growth: families 8, kinds 9, tools 4, ports 21, errors 22, artifact families 4) |
| **JDEC-018** | *(Authorized contract for **Part 2B**; **not yet implemented** — production is still `SemanticVerdict` 8 / `TAMPERING` 5 / `SCORED_AS_TECHNICAL_LOSS` 3 and carries no such member.)* Final scent truthfulness failure classification: a historically genuine `ScentEmission` that does **not** equal the deterministic emission recomputed from the emitter's own reconstructed post-action trajectory, the emitter-correct board and the locked `ScentModelAgreement` **will be** the semantic finding `DISHONEST_SCENT_EMISSION`, which **will NOT** be added to `TAMPERING` and **will** be added to `SCORED_AS_TECHNICAL_LOSS` | Ch 4 §4.4 asserts the scent map "cannot lie … is not forgeable" because in the book's shared environment it is emitted by the movement mechanism itself; two isolated peers share no environment, so C-14 / JDEC-017 already required the emission to travel. The source therefore never classifies a *transmitted* emission that contradicts its own emitter — the enforcement case is under-specified, not contradicted | (a) treat it as `TAMPERING` · (b) leave it undetected / unclassified · (c) reuse an existing scored verdict such as `ILLEGAL_ACTION` · (d) a new peer-visible verdict message or error identity · (e) a new scored semantic finding consumed locally | **(e) new scored semantic finding, existing technical-loss lifecycle** | (a) is wrong because Ch 5 §5.4, Ch 7 §7.4 and E-19 bind "Tampering" to a recomputed-hash mismatch, and this case can have perfect hashes and perfectly faithful historical disclosure; (b) would leave a deterministic exploit inside a mandatory mechanism and make the book's own unforgeability premise false in this architecture; (c) would mislabel a physics fault as an illegal action; (d) would grow the peer surface for a finding the source never requires to be transmitted | none — no wire, tool, family, kind or profile changes; the finding is derived locally by each side from material already exchanged at the final audit | none — scent stays outside `H_commit`, the sealed eight are unchanged, and no key, nonce or digest handling moves | honest move / STAY / police-barrier emitter-board timing, wrong-centre, wrong-intensity, wrong-model, V1 absence, privacy and sealed-eight regressions | low (one closed-vocabulary member and one frozenset entry; no register growth: tools 4, families 8, kinds 9, ports 21, errors 22, artifact families 4) |

### JDEC-016 amended in place (Stage 5-R8 semantic-audit checkpoint) — **no new decision id**

The decision above fixed the live representation. What it deliberately left open
was how a claim and an answer become *evidence*, since neither is a member of
`H_commit` and neither can be checked while the game is being played. That is
settled here, inside the same decision, because it is the same contract:

1. **Retention.** Each side keeps one `CaptureRecord{cursor, claim, answer}` for
   **every** reveal that produced a `TurnOutcome`, in both directions and
   including the ordinary `NO_QUESTION` ones — an omitted row would let a whole
   interaction disappear. The outbound row is written only once the transport
   invocation has actually returned the peer's answer.
2. **Disclosure.** The existing `AuditDocument` gains one member, `capture[]`,
   whose rows are `{step, claim, answer}` with `claim` either `null` or `[r,c]`.
   No new message, tool, wire kind or file. A document with **no** `capture`
   member is refused rather than read as an empty transcript.
3. **Cross-check.** The receiver compares the disclosed transcript against the
   rows it observed, as an ordered sequence, before any verdict is derived.
4. **Replay convention (interoperability-binding, see point 6).**
   `state.self_pos` is the mover's cell **before** that step's action — the cell
   it occupied when it sealed the commitment, never the cell the action leads
   to. `state.barriers` is likewise the public barrier set **before** that
   step's action: every placement revealed in steps `1…k-1` by either side, and
   no placement revealed at step `k`, because both step-`k` commitments are
   sealed before either step-`k` reveal. Consequently a step-`k` capture claim
   is recomputed against the answerer's own sealed cell for step `k`, both sides
   of a step are checked against the same board, and the step's effects are
   applied only afterwards.
5. **Findings and sanctions.** The replay yields one `SemanticFinding`, the
   first violation in step order, recorded in the official log under
   `audit.semantic` and mapped to the sanctions listed in **C-13**. The single
   event that carries a fault on **each** side — a false declaration the
   opponent affirmed — is the closed verdict `FALSE_CLAIM_AFFIRMED`, which names
   both roles (`at_fault`, `also_at_fault`); no fault is dropped for being
   second.
6. **The counted posture binds all of the above.** A peer that echoes
   `STRICT_COUNTED_MATCH_TURN_OUTCOME_V1` is agreeing to the whole contract in
   this decision, not only to the live `TurnOutcome` shape: the `capture[]`
   transcript member, the row-for-row cross-check, and the pre-action reading of
   `state.self_pos` and `state.barriers`. A peer that read either member as
   post-action would compute different capture truth from the same bytes, so
   there is no interoperable semantic audit without this clause. It is stated in
   the profile tables themselves (`COMPATIBILITY_PROFILES.md`,
   `INTEROPERABILITY_NEGOTIATION.md`, `CONFIG_CONTRACT.md`); **no fifth profile
   value exists**, and that checkpoint created no decision id of its own.
   (`JDEC-017` was created later, by the scent pre-game checkpoints, and
   concerns the agreed scent model rather than the turn contract.)

### JDEC-017 — the pre-game scent-model contract (Stage 5-R8)

The row above names the decision; this section is the frozen contract, recorded
once so a later reader does not have to reconstruct it from seven commits. It
resolves **C-14** and consumes, without restating, the recurrence resolution of
**C-10**.

1. **Semantic model.** `ScentModelAgreement` is a separate domain value, not a
   config section. **`NegotiatedConfig` remains exactly 35 members** and
   `pheromones` keeps only the three Appendix-F scalars it always had.
2. **Model id.** The current identifier is `BOUNDED_SATURATING_RADIAL_V1`. It is
   **PROJECT-CONTRACT** wording: no source or Appendix-F row names a scent model
   identifier, and none is claimed.
3. **Fixed source parameters.** Centre intensity **0.9**, decay **0.10**, field
   **5×5** are SOURCE/Appendix-F values (App F Table 16, Ch 4 §4.3) and are
   carried unchanged inside the agreed model as well as in the config core.
4. **Project default kernel.** The default 5×5 weight matrix is
   `0.04 0.14 0.20 0.14 0.04 / 0.14 0.42 0.62 0.42 0.14 / 0.20 0.62 0.90 0.62
   0.20 / 0.14 0.42 0.62 0.42 0.14 / 0.04 0.14 0.20 0.14 0.04`. It is a
   **PROJECT DEFAULT derived from, and consistent with, the illustrative figure**
   — it is **not** an Appendix-F mandatory 25-value matrix and **not** a
   lecturer MUST. Another radial matrix is legal if both peers fully agree it and
   the semantic validators accept it.
5. **Recurrence.** The agreed evolution stays the C-10 resolution,
   `τ_next = min(0.9, max(0, (1−ρ)·τ + Δτ))`. **The written source equation
   contains the lower clamp only**; the upper saturation is the project's
   documented resolution of the state-domain conflict, not a source formula.
6. **Numerical examples.** The model carries the two worked numbers the source
   asks for: `τ=0.9, Δ=0 → 0.81` (pure decay) and `τ=0.9, Δ=0.9 → 0.9`, the
   second of which pins the saturation reading specifically. Both are executed
   against the real recurrence before a model is accepted, so a model whose
   stated numbers its own physics does not produce is refused as malformed.
7. **Canonical identity.** The model has its own deterministic canonical
   rendering under the existing canonicalization contract; the default model
   renders to **344 bytes** and hashes to
   `e587d487716a9cb67688fc8b51b2a895a0dd75a5c49ae0fc9b86683574257600`. Both
   numbers are **PROJECT regression / interoperability vectors** — the source
   supplies no digest and no length.
8. **Exchange.** The complete model travels inside the existing `ConfigProposal`
   family. **No new FastMCP tool, no new peer family, no new wire kind**, and no
   peer-supplied digest is ever adopted: a digest travelling beside the model it
   covers proves nothing about it.
9. **Agreement.** Before the round may lock, the receiver requires the model to
   be present and then compares it three independent ways — values, canonical
   rendering, and a digest each side derives itself. A missing or valid-but-
   different model is `E-CONFIG-MISMATCH`; a structurally invalid or untruthful
   one is refused earlier by the existing malformed-message path.
10. **Cryptographic lock.** `scent_model_sha256` is derived locally from the
    agreed model and is the sixth member of `ConfigLockContext`. The keyed
    framing is unchanged — `b"config" + canonical_json_bytes(lock_context_core)`
    — so the model becomes authenticated purely by being inside the bytes the
    existing proof already covered. **`config_sha256` keeps its prior meaning
    over the 35-member core alone**; the two digests are never merged.
11. **Local expectation.** A peer cannot substitute a model by computing a valid
    proof over a different digest: the receiver compares the authenticated digest
    against the identity **it** derived from the model it agreed, so a correct
    proof over the wrong model is still refused.
12. **Series freeze.** The first sub-game whose lock verified establishes the
    series identity; `g02…g06` must present the same one. Even a **bilaterally
    agreed and validly authenticated** mid-series switch is refused before play.
    A fresh, independent series may legitimately agree a different valid model.
13. **Artifact evidence.** The existing `config_<game_id>_g<NN>.json` persists
    the 35-member core, the lock context and proof, the **actual** agreed model
    in full, and its digest. Read-back proves `full model → scent_model_sha256 →
    authenticated ConfigLockContext` and, independently, `35-member core →
    config_sha256 → the same context`. **No fifth artifact family**, and no key
    material is ever written.
14. **Non-closure.** This decision covers the **pre-game / series model
    contract** only. It does **not** claim Reveal V2, live `ScentEmission`
    transport, consumption of the opponent's scent, a live scent transcript or a
    final scent audit. Those remain later implementation surfaces.

### JDEC-018 — final scent truthfulness classification (Stage 5-R8 Part 2A-R1)

The row above names the decision; this section is the frozen contract. It closes
the one question the Part-2A discovery could not answer from the source, and it
is recorded here rather than in the Conflict Register because it resolves an
**under-specification**, not a contradiction — `C-01…C-14` are unchanged and
**no `C-15` exists**.

> **Implementation status at the time this decision was locked.** This is an
> **authorized future contract**, not a description of shipped code. The
> committed production tree still has `SemanticVerdict` = **8**, `TAMPERING` =
> **5**, `SCORED_AS_TECHNICAL_LOSS` = **3**, and **no**
> `DISHONEST_SCENT_EMISSION` member; `tests/audit/test_scent_scope_freeze.py`
> actively asserts that absence and is correct until Part 2B retires it through
> RED TDD. Every "will" below is deliberate: Part 2B implements this contract,
> and **Part 2B has not started**.

1. **What the source does and does not say.** Ch 4 §4.3 makes the emission a
   consequence of movement, centred on the cell the emitter occupies **after**
   moving or staying. Ch 4 §4.4 then asserts that the scent map *"cannot lie …
   is not forgeable"*, because in the book's shared environment it is emitted by
   the movement mechanism itself; the cheat the book analyses there is a **false
   verbal hint**, whose remedy is explicitly strategic (the reader lowers the
   weight it gives to declarations) and which Ch 5 §5.3.1 legalises outright via
   the sealed `intent` flag. Ch 4 §4.5 and App E #23 require the model to be
   cryptographically locked before counted play *"so that any future deviation
   in the mechanism's behaviour is detected immediately"*, and App F Table 16
   fixes centre `0.9`, decay `0.10` and window `5×5`. **No source rule names a
   sanction for a transmitted emission that is internally well-formed, faithfully
   disclosed, and inconsistent with its own emitter.** In the book's model that
   case cannot arise; in two isolated processes it can, because C-14 / JDEC-017
   already established that the emission must travel.
2. **The finding.** `SemanticVerdict.DISHONEST_SCENT_EMISSION` **will be** raised
   when, for an accepted counted reveal, the historically retained
   `ScentEmission` is not equal to the emission recomputed deterministically from
   evidence the verifier anchors independently. **Classification: PROJECT-DERIVED.** The
   lecturer does not name this verdict, does not call a wrong-centred emission
   "TAMPERED", and Appendix F does not give this case an explicit sanction. Only
   the *obligation to lock the model so deviation is detectable* is source-borne
   (App E #23, MUST).
3. **Expected emission.** `emission_of(emitter_correct_board, locked.kernel,
   reconstructed_post_action_position, locked.params)`.
4. **Position.** Post-action, from the existing `semantic_replay.Replay`
   authority: a move resolves to its destination, `STAY` leaves the cell
   unchanged, a police `BarrierAction` does **not** move the police, and a thief
   placement is already `ILLEGAL_ACTION` under the role contract. The position is
   **never** inferred from the emission being checked, and no opponent truth is
   created or persisted — the reconstruction lives for one review call.
5. **Board.** The board at the start of the step **plus that emitter's own
   action effect**, never the opponent's same-step placement: both step-`k`
   commitments are sealed before either step-`k` reveal (JDEC-016 §4), so an
   emitter could not have seen the other side's step-`k` barrier.
6. **Model.** The authenticated `ScentModelAgreement` carried by the verified
   `ConfigLockContext` and frozen for `g01…g06` (JDEC-017 §10/§12). **Never
   `default_scent_model()`**, and never a model inferred from the emission under
   test.
7. **Comparison.** Semantic `ScentEmission` equality. Ordering, uniqueness,
   board clipping and positivity are already enforced by the domain constructor;
   intensities compare as `Decimal` numbers, so `Decimal("0.90")` and
   `Decimal("0.9")` are one value at this boundary. The canonical **spelling**
   authority for wire and artifact bytes remains `app/decimal_text.py` and is
   untouched — no float, and no string-based physical comparison.
8. **Scope.** V2 counted reveals only; a V1 sub-game carries no emission and is
   not checked. Decay is **not** part of this check: §4.3 applies decay at the
   end of a **full** turn, after both sides have moved, and this audit verifies
   the isolated per-action `Δτ`. No accumulated `ScentField` replay, no half-turn
   consumption — those belong to a later belief/consumption surface.
9. **Not TAMPERING.** Ch 5 §5.4, Ch 7 §7.4 and App E #19 bind "Tampering" and
   its no-appeal disqualification to a **recomputed commitment-hash mismatch**.
   This case can occur with every hash verifying and with Part-1A/1B historical
   correspondence perfectly intact, because scent is not a member of the sealed
   eight. Calling it Tampering would extend a cryptographic term to a physics
   fault. **`DISHONEST_SCENT_EMISSION` is therefore to be excluded from
   `TAMPERING`, which stays at five members.**
10. **Scored as a technical loss.** It **will join** `SCORED_AS_TECHNICAL_LOSS`,
    so the sub-game ends `Outcome.TECHNICAL_LOSS` and `domain.scoring` already scores it
    **0/0** (Ch 3 Table 2, App E #48, C-07). No new scoring system, no
    asymmetric custom score, no new terminal phase. This reuses the lifecycle
    C-13 already established for an honest record of bad play.
11. **Why not silence.** Leaving the case unclassified would leave a
    deterministic, repeatable exploit inside a mandatory mechanism: a peer could
    lock the correct model, produce valid hashes, send a deliberately misleading
    emission every turn, disclose that same emission faithfully, and pass every
    Part-1A and Part-1B check. The book's own premise that the scent map cannot
    lie would then be false in this implementation. This decision closes exactly
    that gap and nothing wider.
12. **Surface cost.** The finding is derived **locally** by each side from
    material the final audit already exchanges, and is recorded in the existing
    `audit.semantic` block. **No** FastMCP tool, peer family, wire kind,
    compatibility profile, artifact family, port or protocol error identity is
    added, and the sealed commitment remains exactly eight members. The verifier
    is deterministic and LLM-free.
13. **Predicted implementation counts (Part 2B, not yet code).**
    `SemanticVerdict` **8 → 9**; `SCORED_AS_TECHNICAL_LOSS` **3 → 4**;
    `TAMPERING` **stays 5**; errors stay **22**; every other register unchanged.

## Stage 1D audit (KEEP / MODIFY / RETIRE) + JDEC-012/013 + Stage-2A-R2 JDEC-014

| JDEC | Action | Change |
|---|---|---|
| JDEC-001 | KEEP | — |
| JDEC-002 | KEEP | now the PROJECT-LOCKED **default** confirmed via **NDEC-003** |
| JDEC-003 | **MODIFY** | config `schema_version` **value = NEGOTIATED** (NDEC-004, in the byte-identical config); **declaration `schema_version` REMOVED** (redundant) |
| JDEC-004 | KEEP | — |
| JDEC-005 | **MODIFY** | `game_uid` **and** `game_id` are **SOURCE-EXPLICIT names** (Ch 9 p.95); only their **format** is project (D3) |
| JDEC-006 | KEEP | declaration presentation keys; Step-0 hashed subset → NDEC-005 |
| JDEC-007 | **MODIFY** *(re-amended in place, Stage 4E-R11-R1)* | sealed commitment payload → **NDEC-001**. The Stage-1D shorthand "persistent log = **LOCAL-ONLY**" was **over-broad** and is narrowed rather than replaced: **internal logger mechanics, artifact metadata and the locally-derived verification annotations** (`entries[].verified`, `audit.result`, `audit.tampered_step`, `by_role`) stay **LOCAL**, while the finalized per-sub-game log's **audit-disclosure core** is **SHARED / INTEROPERABLE at final audit** — because Ch 5 §5.4 requires each side to disclose enough of its log for the opponent to recompute every commitment independently, which the earlier wording would have forbidden. Key spelling and the separate-event `entries[]` nesting remain **PROJECT-CONTRACT** (this decision's original choice, confirmed at 4E-R11-R1). **There is still exactly one log schema — no parallel audit schema — and the receiver derives its own verification result and never trusts an incoming one.** No new decision ID: JDEC count stays **15**. |
| JDEC-008 | KEEP | result presentation; approval core → NDEC-006 |
| JDEC-009 | KEEP | — |
| JDEC-010 | **MODIFY** | `config_sha256` stored **outside** the hashed config (non-self-referential); Step-0/result hashes → NDEC-005/006 |
| JDEC-011 | KEEP | — |
| **JDEC-012** | **NEW** | `state` sealed representation `{config_sha256, self_pos, barriers(sorted), step, role}` (own-known only); PROJECT-LOCKED default, confirmed via **NDEC-002** ; **Stage 4E-R9-R1** additionally pins that this decision - not JDEC-006 - owns the `[row,col]` coordinate-array convention reused by the sealed `move` barrier form, that `barriers` are sorted **and duplicate-free in the semantic value** so no mapper ever sorts, and that `state.role` uses the `"police"`/`"thief"` vocabulary with `state.step`/`state.role` required to equal the top-level members before hashing |
| **JDEC-013** | **NEW (Stage 1D.1)** | **Keyed authentication default = HMAC-SHA256** over `context ‖ canonical_payload`, `context ∈ {"step0","config"}`, key referenced by `key_id` (no key material anywhere). **Source requirement = keyed authentication with a pre-supplied key (Ch 5 p.55–56; App B p.128); the algorithm is our choice, not lecturer-specified.** Out-of-band key provisioning; `auth_tag`/`auth_alg`/`key_id` envelope is non-self-referential. No compatible key/mechanism pre-match ⇒ **refuse counted play**. |
| **JDEC-014** | **NEW (Stage 2A-R2)** | **Result references the declaration instead of duplicating static metadata.** The emitted `result_<game_id>.json` carries a `declaration_ref` join (via `game_id`/`game_uid`/`group_id`) plus the explicitly-mandatory report fields (four GitHub links, per-sub-game `github_commit`, total tokens, scores, cumulative, timestamp, mutual agreement, `result_sha256`). FastMCP/MCP endpoints, full hardware specifications, `hardware_auth`, member lists and the token cap are **declaration-owned** (Ch 9 p.78 four-file list; App F Table 20) and are **not repeated** in the result. Self-containment is a property of the **four-artifact set**. Corrects the Stage-1D.1 K3 over-read of §9.3.3. Compatibility profiles may inline them if a grader parser is shown to require it. |

**No JDEC retired.** JDEC-001…018 active, unique. Negotiated items are tracked as
NDEC-001…007 in `INTEROPERABILITY_NEGOTIATION.md`.

### JDEC-013 key handling (security)

Key material MUST NOT appear in Git, JSON artifacts, logs, docs, email, runtime
evidence, or error messages. Only a non-secret `key_id` reference is stored; the
pre-shared key is provisioned out-of-band ("pre-supplied key"). HMAC-SHA256 is
PROJECT-CONTRACT — the **source requirement is keyed authentication**, not HMAC
specifically; an asymmetric signature is an allowed alternative if both peers agree.

## Rules

- No JDEC changes any Appendix F value, any MUST/MUST NOT, or C-07.
- **JDEC-015 (Stage 3B-FIX1)** is an *implementation-discovered* source-gap
  resolution: it is a PROJECT-CONTRACT admissibility rule, **not** a new
  Appendix-F row, not a lecturer MUST, not a changed numeric minimum, and not a
  new scoring, tie or technical-loss rule. Both `max_moves` and
  `survival_threshold` keep their independent **MINIMUM 35** status.
- JDEC-002, JDEC-010, JDEC-012 are the interop/security-relevant ones (hashing
  determinism, non-self-referential hash storage, sealed `state`); each has a
  PROJECT-LOCKED default confirmed via an NDEC.
- **JDEC-018 (Stage 5-R8 Part 2A-R1)** is a PROJECT-DERIVED classification of an
  enforcement case the source leaves open, **not** a lecturer-named verdict, not
  an Appendix-F sanction and not a new reading of "Tampering". It adds no
  register member outside the semantic vocabulary it defines.
- IDs are unique JDEC-001…JDEC-018; no duplicates. `game_uid` is **not** invented —
  it is source-named (D3). JDEC-013 (keyed authentication) fixes only the **primitive**;
  the **requirement** (keyed auth with a pre-supplied key) is SOURCE, not a JDEC.
