# Source Conflict Register - group MaRs-777

> **Status: DRAFT (expanded in Stage 1A).**
> **Purpose:** Record any conflict/tension between sources (book chapters vs
> Appendix E/F vs example code vs Moodle) so it is resolved deliberately, not
> silently.
> **Rule:** Numeric conflicts are resolved by **Appendix F** (it wins).
> Non-numeric conflicts are **not** resolved during Stage 1A — alternatives are
> recorded per the academic-freedom rule (PDF p.5 / book v); a selected
> interpretation is deferred to a reviewed stage unless the book itself resolves it.

Confidence = how sure we are the conflict is real. "NOT CONFIRMED" = checked
against the book and found **not** to be a genuine conflict.

| # | Topic | Source A | Source B | Numeric? | Binding resolution rule | Current resolution | Confidence | Implementation consequence | Review status |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | Board dimensions: illustrative vs binding minimum | Examples `5×5` (Ch 3, PDF p.35) and `10×10` (Ch 2 abstract PDF p.24; Ch 6 belief map PDF p.64) | Appendix F Table 13 #1 `[board size]` = **7×7**, status MINIMUM (PDF p.152) | Yes | Appendix F wins; earlier values are illustrative | **CONFIRMED (resolved by App F):** default 7×7, MINIMUM ≥7; other sizes only by agreement in the harder direction. | High | Board code must read size from signed config, floor 7. | Resolved-by-book; note in Stage 1C config validator |
| C-02 | Watchdog / turn-timeout numeric values | Ch 8 code sample `timeout_sec=180` (PDF p.83); private TOML `turn_timeout_seconds=180` / `step_deadline_seconds=30` (PDF p.131) | Appendix F Table 19: watchdog threshold **60s** (NEGOTIABLE), response timeout **30s** (NEGOTIABLE) (PDF p.155) | Yes | Appendix F wins for the binding values; TOML `turn_timeout` is a **private** per-peer value, not the negotiated one | **CONFIRMED (resolved by App F):** binding watchdog=60s, response=30s (NEGOTIABLE, may raise). The `180s` are illustrative/private, not the shared floor. | High | Deadline Tracker / Watchdog defaults come from App F, not the code sample. | Resolved-by-book |
| C-03 | LLM deciding the move | E-25 recommendation + Ch 6 default: move is **always algorithmic**; "don't delegate move to LLM" (PDF p.65,146) | Ch 6 exception: an LLM-based move tactic is allowed **by explicit mutual documented agreement** (PDF p.66) | No | Book resolves it: default algorithmic; exception only by mutual, documented agreement; legality still code-enforced | **NOT CONFIRMED as a conflict:** these are a rule + its explicit, bounded exception, not contradictory. Captured as LLM-001 (SHOULD) + LLM-005 (MAY). | High | Default implementation stays algorithmic; any LLM-move path requires a signed agreement + legality guard. | Resolved-by-book |
| C-04 | Commit payload: simplified example vs full record | Ch 7 `verify_step` payload `f"{nonce}|{move}"` (PDF p.74); Ch 5 core code hashes `{state,move,intent,nonce}` (PDF p.53) | Ch 5 prose: the **real** sealed record covers State, Move, Intent, Nonce **and** hint, verdict, step, role, sub_game (PDF p.50,74) | No | Book explicitly flags the code as a **simplification** for illustration | **NOT CONFIRMED as a conflict:** the book states the samples are simplified; the binding record is the fuller canonical one. Captured as CRYPTO-009. | High | Stage 1C must define the full canonical log-entry payload (the sample is not the contract). | Resolved-by-book; flagged REVIEW REQUIRED for exact fields in JSON_SOURCE_MAP |
| C-05 | Games in a series: config default vs series length | `config/game.json` `network_and_league.num_games` default **1** (PDF p.129–130); text "single demo sub-game" | Appendix F Table 18 #1 `[games per series]` = **6** (FIXED); Ch 9 full series needs 6 (PDF p.130,154) | Yes | Appendix F wins for the binding series length (6); the `1` is a **default demo** value in the sample config | **CONFIRMED (resolved by App F):** a counted league series = 6 sub-games; `num_games:1` is only a single-demo default. | High | Config for a counted league game must set exactly 6 (FIXED: deviation in either direction is refused). | Resolved-by-book |
| C-06 | Scoring label order in the E-48 shorthand | App E #48 shorthand "לכידה 5/20, הישרדות 10/5" (thief/police order) (PDF p.149) | App F Table 17 explicit per-role: capture cop 20 / thief 5; survival cop 5 / thief 10 (PDF p.154); Ch 3 Table 2 (PDF p.38) | Yes | Appendix F (explicit per-role) governs | **NOT CONFIRMED as a conflict:** E-48 simply lists thief/police; it equals App F (cop 20, thief 5; cop 5, thief 10). Captured as GAME-006 with an explicit note on label order. | High | Scoring table must be keyed by role, not by shorthand order, to avoid mislabeling. | Resolved-by-book; keep the ordering note in GAME-006 |
| C-07 | **technical_loss provenance omission** (Stage 1B) | App E #48 (PDF p.149) says "score every end scenario **per the parameter table** (… technical loss 0/0)"; Ch 3 Table 2 (PDF p.38) defines technical loss 0/0; App B config (PDF p.129) has field `"technical_loss": 0` | **Appendix F Tables 13–19 (PDF p.151–155) contain NO technical-loss row** (Table 17 = 5 rows only) | Yes (a numeric value with no App F row) | App F is the sole numeric authority, yet it **omits** this value; other binding text (Ch 3, E-48) still requires 0/0 | **CONFIRMED omission (book-internal):** the 0/0 technical-loss scoring rule **is binding** (Ch 3 + E-48) and the config carries a real `technical_loss` field (App B), but its numeric provenance is **not** Appendix F. Distinguish: (a) operational value supported elsewhere = 0/0 (Ch 3, App B, E-48, binding); (b) Appendix-F numeric provenance = **none**; (c) unresolved book-internal omission = App F should arguably list it. | High | The 0/0 rule is **retained** and binding; do **not** attribute it to Appendix F. Config `scoring.technical_loss` sources its value from Ch 3, not App F. Flag for the lecturer as a possible App F omission. | Open (omission documented); rule preserved, provenance corrected |

## High-risk conflict classes checked (per Stage 1A directive)

- **Example game count vs binding series length** → **C-05 (CONFIRMED)**.
- **Example timeout/watchdog values vs Appendix F** → **C-02 (CONFIRMED)**.
- **Reporting sanctions** → **C-09 (CONFIRMED, Stage 1D.1)** — see below. **This
  supersedes the Stage-1A "NOT CONFIRMED / consistent" note, which was wrong:** Ch 9
  p.94 and App E #35 prescribe *different* sanctions for the same reporting failure
  (per-side non-credit vs. game-void/0-both). The stricter Appendix-E behaviour governs.
- **LLM tactical movement examples vs stated default mode** → **C-03 (NOT CONFIRMED** — rule + explicit exception).
- **Illustrative board dimensions vs binding minimum** → **C-01 (CONFIRMED)**.
- **Simplified hash examples vs complete real protocol records** → **C-04 (NOT CONFIRMED** — book flags the simplification).

Numeric conflicts C-01, C-02, C-05, C-06 are governed by **Appendix F**. **C-05
(num_games) is closed** — the counted league series is **6, FIXED** (App B `1` is
an illustrative example); it is no longer an Open Question. **C-07 is the one
case where Appendix F is silent** — the binding 0/0 technical-loss rule comes from
Ch 3 + App E #48 and the App B config field, and the omission is flagged for the
lecturer rather than resolved by inventing an App F row. No non-numeric conflict
currently requires an interpretation choice the book does not itself resolve;
none is decided unilaterally.

**Stage 1B corrections (this pass):** added C-07 (technical_loss App F omission);
closed C-05 (num_games = 6, FIXED); confirmed C-01/C-02 resolved by App F; C-03/C-04
remain NOT CONFIRMED.

| C-08 | **`verdict` vs `intent` terminology (sealed record)** (Stage 1D) | Ch 5 p.53 English code comment: sealed record "(hint, **verdict**, step, role, sub_game)" | Ch 5 p.50 Hebrew prose: sealed record adds "hint, **intent classification (סיווג הכוונה)**, step, role" | No | Book resolves by alignment: the two lists are position-for-position identical ⇒ `verdict` = intent classification = the truth/lie tag = the core `intent` | **NOT a conflict; source terminology ambiguity:** `verdict` and `intent` denote the same commit-time classification. The sealed payload uses **`intent`** (8-field set); **no separate `verdict` field**. The post-reveal legality/capture "verdict" is a *different* object (PROTOCOL_TIMELINE event 9). | High | Do not add a separate `verdict` field to the hashed payload (would diverge the hash). | Resolved (D1); recorded to prevent a future re-split |

| C-09 | **Reporting-failure sanction: chapter vs Appendix E** (Stage 1D.1) | **Ch 9 §9.3.3 p.94:** "אם לא יתקבל דוח מאחד הצדדים, אותו צד לא יזוכה בניקוד" — if a report is not received from **one** side, **that side** is not credited (a **one-sided, per-team** non-credit; the reporting side can still score) | **App E #35 p.147:** "דיווח סותר גורם ל**פסילת המשחק וציון 0 לשתי הקבוצות**" — a **contradictory** report voids the **whole game**, **0 to both** teams | **No** (a sanction/severity conflict, not a numeric value) | Non-numeric; App F does not arbitrate. Resolve by the **stricter, safer** rule and by scope: missing-from-one-side (Ch 9) and contradictory (E-35) are partly different triggers, but where they overlap the **harsher E-35 game-void/0-both** governs | **CONFIRMED conflict (severity/scope):** the two texts are **not** the same sanction. We adopt the **strictest composite**: **(a)** a required report missing from **either** team **or (b)** contradictory reports ⇒ **game invalid, 0 to both** (E-35). We do **not** rely on the milder Ch 9 per-side non-credit when E-35's harsher rule can apply. Both teams must send **matching** reports (equal `result_sha256`, `mutual_agreement:true`) or neither is credited. | High | Result/report validation MUST treat any missing-or-contradictory report as **0 to both**; never silently credit one side. Surfaced in `RESULT_CONTRACT.md`, NDEC-006, INV-11, and the adversarial cases. | Open (book-internal severity conflict; strictest rule adopted, flagged for lecturer) |

| **C-10** | **Scent state bound vs additive update formula** (Stage 3B-FIX2; **post-lock, implementation-discovered**) | **Ch 4 §4.3 (PDF p.43 / book p.27)** defines the state variable: `τij(t) — עוצמת הריח בתא בזמן הנוכחי. **ערך רציף בתחום [0, 0.9]**` — τ is a continuous value **in [0, 0.9]**. This constrains the STATE, not merely the emission delta. | **Ch 4 §4.3 update equation:** `τij(t+1) = max(0, (1−ρ)·τij(t) + ∆τij)` — a lower clamp only, with centre `∆τ = 0.9`. Literal repeated emission yields e.g. `0.81 + 0.9 = 1.71`, which violates Source A. | **No** (App F fixes 0.9 / 0.10 / 5×5 but does not resolve the update expression) | Non-numeric semantic conflict → documented project interpretation (academic-freedom rule, PDF p.5) | **The state invariant wins: `0 <= τ <= 0.9`.** The implemented evolution is the saturated recurrence `τ_next = min(Decimal("0.9"), max(Decimal("0"), (1−ρ)·τ_cur + ∆τ))`. Below the bound the recurrence stays exactly additive — saturation is a boundary operation, not a replacement. | **Confirmed** (both statements quoted from the same section) | Upper saturation in `domain.scent`; construction-time `[0, 0.9]` validation of every `ScentField` cell; Figure 5 is corroborating illustration only | **RESOLVED — Stage 3B-FIX2 (post-lock)** |

| **C-11** | **Peer-family inventory overreach — a transmitted `FinalAudit` verdict** (Stage 4E-R10 / R10-R1; **post-lock, reconciliation-discovered**) | **Derived project inventory:** our peer-visible message inventory counted a **Final audit** family, and `PROTOCOL_TIMELINE.md` event 12 carried `**[RR]** audit verdicts` as a transmitted item. | **Book:** Ch 5 §5.4 (p.55) has each side **submit its full log including every nonce reveal** and then **independently recompute** the opponent's commitments locally; Ch 7 §7.5 + Figure 10 place `Verified OK`/`TAMPERED` in the **Replay Viewer** over the persisted log; **Figure 6 (p.52) draws no audit-verdict arrow**; App E requires a comprehensive **mutual log audit** as a precondition to agreeing the shared result. | No | Non-numeric; App F silent. Source minimality: a family is peer-visible only where the source requires transmission. | **RESOLVED (Stage 4E-R10-R1).** There is **no peer-visible `FinalAudit` verdict family**; the derived inventory is corrected **10 → 9**. `FinalAuditVerdict` survives unchanged as the **local audit / log / replay** vocabulary, `ProtocolPhase.FINAL_AUDIT` survives as a workflow phase, and the **source-required end-of-game audit-material / full-log disclosure** survives as a separate artifact/transport obligation whose interchange shape is newly recorded as `AUDIT-EXCHANGE-PAYLOAD: BLOCKED-BY-INTEROPERABILITY-SHAPE`. **The source does not forbid a verdict message; it simply does not require one, and the project declines to invent it.** | High — three independent source lines converge, and Stage 4E-R10 stopped rather than change the inventory unilaterally. | Peer-visible families **9**; matrix **4 implemented / 0 ready / 5 blocked**. No Python changes: `FinalAuditVerdict`, `FINAL_AUDIT` and `FinalNonceReveal` are untouched, and no `FinalAudit` class ever existed. Timeline events stay **15**; no requirement, JDEC, NDEC, INV or Appendix count changes. | **Stage 4E-R10-R1 — supervising-authorized; awaiting CLOSE review** |

| **C-12** | **Peer-family inventory overreach — a standalone `MoveValidation` message** (Stage 4E-R10-R2 / R10-R3; **post-lock, reconciliation-discovered**) | **Derived project inventory:** our peer-visible inventory counted a **Move validation** family, and `PROTOCOL_TIMELINE.md` event 8 carried `**[RR]** accept/reject` as a transmitted item with an unfrozen shape. | **Book:** App E #14 gives the *sanction* — *"no diagonal moves; sanction: **rejection of the move by the opponent** and loss"* — but no passage describes a transmitted validation payload, cadence, vocabulary or association; **Figure 6 (p.52) draws no move-validation arrow**; Ch 6 §6.4-6.5 reserve legality to the **local algorithm**, whose "reject" is of *its own model's* proposal; and the only response-shaped artifact, the FastMCP `receive_move` return `{"accepted": is_valid, …}`, computes `is_valid = verify_signature(...)` — **signature authentication, not game legality**. | No | Non-numeric; App F silent. The source requires the *outcome*; the mechanism is source-unspecified, so it is a project choice under source minimality. | **RESOLVED (Stage 4E-R10-R3, supervising architecture decision).** The rejection is **not** modelled as a standalone `app.peer_messages` family; the peer-facing legality outcome is placed at the **transport / port response boundary** of the operation that receives the turn. The derived inventory is corrected **9 → 8**. `domain.rules` + `LocalTurnService` remain the sole game-legality authority (already contracted as `GameRulesPort`, which *"never raises for legality — returns a verdict"*), and `E-PROTO-ILLEGAL-MOVE` already owns the rejection outcome. **PROJECT-CONTRACT: the source is not claimed to forbid a distinct message.** The exact response shape is **not** frozen here — see `MOVE-REJECTION-TRANSPORT-SHAPE` in `INTEROPERABILITY_BLOCKERS.md`. | High — Stage 4E-R10-R2 stopped `BLOCKED-BY-EXISTENCE-EVIDENCE` rather than decide unilaterally, and the mechanism was chosen by supervising review, not inferred. | Peer-visible families **8**; matrix **4 implemented / 0 ready / 4 blocked**. No Python changes and no `MoveValidation` class ever existed. Timeline events stay **15**; events 8 and 9 survive, reconciled rather than deleted. No requirement, JDEC, NDEC, INV or Appendix count changes. | **Stage 4E-R10-R3 — supervising-authorized; awaiting CLOSE review** |

**Stage 1D.1 correction (this pass):** added **C-09** (reporting-failure sanction:
Ch 9 per-side non-credit vs App E #35 game-void/0-both). The Stage-1A high-risk-class
line that called reporting sanctions "consistent / NOT CONFIRMED" is **corrected** —
it **is** a genuine non-numeric conflict; the stricter E-35 rule is binding. No
numeric authority is involved (App F is silent), so this is resolved by
severity/scope, not by Appendix F.

**Stage 1D note:** `game_uid` is **source-named** (Ch 9 p.95), not a project
invention — Stage 1C's PROJECT-CONTRACT label was corrected to SOURCE-EXPLICIT
(kept). Added **C-08** (verdict = intent). No other new conflict; C-07 preserved and
surfaced in the config/result contracts. Unspecified interop representations are
now LOCKED-PROJECT or NEGOTIATED-PRE-MATCH (NDEC-001…006), not open conflicts.

**Stage 1C note:** the four JSON contracts (`docs/spec/json/`) were defined without
discovering any **new** source conflict. C-07 (technical_loss) is preserved and
surfaced in `CONFIG_CONTRACT.md`/`RESULT_CONTRACT.md`; C-04 (simplified commit
example vs full sealed record) is handled in `LOG_CONTRACT.md` (the simplified Ch-5
4-field and Ch-7 `nonce|move` examples are EXAMPLE-ONLY, not the real format).
Unspecified JSON key names / signature storage are **REVIEW-REQUIRED**, not
conflicts (silence ≠ conflict).

## C-10 — scope and non-effects (Stage 3B-FIX2)

**Rationale.** (1) The source explicitly defines τ's legal state domain as
`[0, 0.9]`. (2) The unsaturated recurrence can produce a value outside that
domain. (3) Upper saturation is the smallest deterministic interpretation that
lets the stated state-domain invariant and the intended additive decay/emission
mechanism coexist. (4) **Figure 5** (bounded re-emission) is corroborating
*illustrative* evidence only, never the source of the rule. (5) Appendix-F
numeric values are unchanged. (6) The exact update model is still to be mutually
agreed and hash-locked before a series, as Ch 4.5 requires.

**C-10 does NOT:** change `pheromone_center_intensity` · change
`pheromone_decay` · change `pheromone_grid_size` · add an Appendix-F row · add a
new source MUST · make Figure 5 binding · make the Figure-4 values binding ·
alter the radial-kernel project contract · introduce a config field (the bound
is a source-defined state-domain invariant, never negotiated and never written
to an official artifact) · relate to `pheromone_min_center_intensity`.

## C-11 — scope and non-effects (Stage 4E-R10-R1)

**Rationale.** (1) Ch 5 §5.4 describes an end-of-game mutual audit that is
**complete without a verdict message**: logs are disclosed, each side recomputes
the opponent's commitments itself, and *"the cryptography, and not human
judgement, decides"* — a transmitted verdict would be the other side's assertion
about its own conduct, which unforgeable local recomputation exists to make
unnecessary. (2) Ch 7 §7.5 and Figure 10 place the `Verified OK`/`TAMPERED`
verdict in the **Replay Viewer**, a local submission-requirement tool reading a
persisted log file. (3) **Figure 6 (p.52) draws four arrows only** — Commit,
Acknowledge, Reveal, Final Reveal — and no audit-verdict arrow. (4) App E and
**PRD06-FR-100** make the mutual audit a **precondition to agreeing the shared
result**, locating the outcome downstream rather than in an audit message.
(5) **PRD06-FR-104** requires audit evidence to be *preserved*, not transmitted.

**C-11 does NOT:** claim the source *forbids* an audit-verdict message (the
correct classification is **NOT SOURCE-REQUIRED**) · delete or rename
`FinalAuditVerdict` · remove `ProtocolPhase.FINAL_AUDIT` or the final-audit
workflow · change any Python · delete timeline event 12 or change the event
count · weaken the TAMPERED consequence, which keeps its frozen source sanction ·
resolve `MoveValidation`, which stays `BLOCKED-BY-PAYLOAD-SHAPE` · resolve
`ResultAgreement`, which stays `BLOCKED-BY-PAYLOAD-SHAPE` and is **not** the
transport of a verdict · claim `FinalNonceReveal` is the complete audit material ·
add a requirement, JDEC, NDEC, INV or Appendix-F row.

## C-12 — scope and non-effects (Stage 4E-R10-R3)

**Rationale.** (1) App E #14 states a **sanction** — who bears the loss when a
move is illegal — not a message contract; sanction columns describe consequences
throughout that appendix. (2) The rejection Ch 6 §6.5 *does* specify is the
**local algorithm rejecting its own model's** illegal proposal, which is a
different act from a peer-facing one and must not be conflated with it. (3)
**Figure 6 (p.52)** draws four arrows and no move-validation arrow. (4) The only
response-shaped artifact in the source validates a **signature**, not legality,
and is the return of the *same* call that submits the move. (5) The mechanism is
therefore source-unspecified, and the project chooses the minimal one — a
transport/port response — rather than inventing a peer-message family.

**C-12 does NOT:** claim the source *forbids* a distinct validation message (the
classification is **NOT SOURCE-REQUIRED**) · weaken App E #14's required
rejection or its loss consequence · move any legality logic out of `domain.rules`
/ `LocalTurnService` · let transport become a second rules engine · repurpose the
cryptographic `Acknowledgement` as a legality signal · promote the FastMCP
signature-validation example to game-legality law · add a positive "move was
legal" message for symmetry · delete timeline event 8 or 9, or change the
**15**-event count · freeze the transport response shape, which remains
`MOVE-REJECTION-TRANSPORT-SHAPE: BLOCKED-BY-TRANSPORT-SHAPE` · resolve
`ResultAgreement`, `AUDIT-EXCHANGE-PAYLOAD`, Step-0 or the config families · add
a requirement, JDEC, NDEC, INV or Appendix-F row · supersede **C-11**, whose own
non-effects list correctly records that *C-11* did not resolve `MoveValidation`.

**Identifier note.** Conflict-Register **C-10**, **C-11** and **C-12** are
distinct from the unrelated review-local finding labels "C-10", "C-11" and
"C-12" used inside `docs/prd/PRD_05_07_REVIEW.md`, which number that document's
own Stage-2C red-team findings — its "C-11" is a *profile-downgrade* risk row and
its "C-12" a *result-hash self-reference* row, both resolved there, and neither
has any relation to the peer-family inventory. Those are **not**
Conflict-Register entries, and that historical review is left unchanged. The
Conflict Register is the single authority for `C-01…C-12`.
