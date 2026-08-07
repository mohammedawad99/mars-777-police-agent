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
| C-05 | Games in a series: config default vs series length | `config/game.json` `network_and_league.num_games` default **1** (PDF p.129–130); text "single demo sub-game" | Appendix F Table 18 #1 `[games per series]` = **6** (FIXED); Ch 9 full series needs 6 (PDF p.130,154) | Yes | Appendix F wins for the binding series length (6); the `1` is a **default demo** value in the sample config | **CONFIRMED (resolved by App F):** a counted league series = 6 sub-games; `num_games:1` is only a single-demo default. | High | Config for a counted league game must set 6 (or the agreed higher). | Resolved-by-book |
| C-06 | Scoring label order in the E-48 shorthand | App E #48 shorthand "לכידה 5/20, הישרדות 10/5" (thief/police order) (PDF p.149) | App F Table 17 explicit per-role: capture cop 20 / thief 5; survival cop 5 / thief 10 (PDF p.154); Ch 3 Table 2 (PDF p.38) | Yes | Appendix F (explicit per-role) governs | **NOT CONFIRMED as a conflict:** E-48 simply lists thief/police; it equals App F (cop 20, thief 5; cop 5, thief 10). Captured as GAME-006 with an explicit note on label order. | High | Scoring table must be keyed by role, not by shorthand order, to avoid mislabeling. | Resolved-by-book; keep the ordering note in GAME-006 |
| C-07 | **technical_loss provenance omission** (Stage 1B) | App E #48 (PDF p.149) says "score every end scenario **per the parameter table** (… technical loss 0/0)"; Ch 3 Table 2 (PDF p.38) defines technical loss 0/0; App B config (PDF p.129) has field `"technical_loss": 0` | **Appendix F Tables 13–19 (PDF p.151–155) contain NO technical-loss row** (Table 17 = 5 rows only) | Yes (a numeric value with no App F row) | App F is the sole numeric authority, yet it **omits** this value; other binding text (Ch 3, E-48) still requires 0/0 | **CONFIRMED omission (book-internal):** the 0/0 technical-loss scoring rule **is binding** (Ch 3 + E-48) and the config carries a real `technical_loss` field (App B), but its numeric provenance is **not** Appendix F. Distinguish: (a) operational value supported elsewhere = 0/0 (Ch 3, App B, E-48, binding); (b) Appendix-F numeric provenance = **none**; (c) unresolved book-internal omission = App F should arguably list it. | High | The 0/0 rule is **retained** and binding; do **not** attribute it to Appendix F. Config `scoring.technical_loss` sources its value from Ch 3, not App F. Flag for the lecturer as a possible App F omission. | Open (omission documented); rule preserved, provenance corrected |

## High-risk conflict classes checked (per Stage 1A directive)

- **Example game count vs binding series length** → **C-05 (CONFIRMED)**.
- **Example timeout/watchdog values vs Appendix F** → **C-02 (CONFIRMED)**.
- **Reporting sanctions** → checked (E-32/33/34/35, Ch 9 PDF p.94–95): consistent across chapter and appendix. **NOT CONFIRMED** as a conflict.
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
