# Attachment Evidence Register — group MaRs-777

**Status: STAGE 2A-R2 — evidence record. Documentation only.**

## Evidence levels (strictly separated)

| Level | Meaning | Weight |
|---|---|---|
| **PRIMARY-PDF** | Read directly from `police_thief_p2p.pdf` (SHA-256 `7c9e1d75…dd02e`) by this project | **Authoritative** |
| **REFERENCE-REPOSITORY** | Observed in `rmisegal/Game-P2P-Cop-Chase` @ `960499fd` | Non-binding implementation example |
| **CHATBOT-SOURCE-EXTRACTION** | Text the lecturer's chatbot reported as coming from an attachment file, supplied to us by the **user** | **Secondary provenance** — the attachment bytes were **not independently accessible to us** |
| **CHATBOT-INTERPRETATION** | The chatbot's own commentary/inference | Weakest; never binding |
| **PROJECT-DECISION** | Our engineering choice, labelled as such | Ours, reversible |

> **Standing rule.** Chatbot-extracted text is **never** called independently verified
> primary evidence. We preserve it verbatim, attribute it, and cross-check it against
> the PDF. Where they disagree, **the PDF wins**.

## Common provenance facts for AE-01…AE-04

- **Supplied by:** the **user**, relaying output from the lecturer's second chatbot.
- **We did not open the attachment bytes.** The user cannot access the chatbot's source
  files directly; we therefore **cannot** confirm the extraction is complete, literal,
  or unmodified.
- **Level:** CHATBOT-SOURCE-EXTRACTION.
- **PDF status of the attachments (PRIMARY, verified by us):** Appendix F §3 states
  *"לספר זה מצורפים ארבעה קובצי JSON **לדוגמה** … הממחישים את פורמט השימוש המלא"* —
  "four **example** JSON files are attached to this book … illustrating the full usage
  format". The attachments are therefore **examples**, not a binding schema.

---

## AE-01 — role alternation

**Source filename reported by chatbot:** `1-pre-game-declaration.txt`

**Exact extracted text (verbatim, unparaphrased):**

> "Roles (cop/thief) switch across the sub-games, so no role and no
> sub_game_number appear here."

**Reported location:** inside the `_schema` descriptive field of the example
declaration — **not** presented as a separately identified MUST rule.

**Primary-PDF cross-check (performed by us):** exhaustive search of all 160 pages for
`החלפת תפקידים`, `מתחלפים`, `לסירוגין`, `מחליפים תפקיד`, `החלפת התפקידים`,
`תפקידים מתחלפים` → **0 hits each**; `alternat` → 1 unrelated hit (RL "Two Equal
Alternatives"); `rotate` → 1 unrelated hit (rotating leaked credentials). **The book
neither requires nor forbids role alternation.**

**Final classification: ATTACHED-EXAMPLE-CONVENTION** (reinforced by
REFERENCE-REPOSITORY, which implements `role_for()` alternation). **NOT
SOURCE-MANDATORY.** No new MUST is created.

---

## AE-02 — Ed25519 in the declaration example

**Source filename reported by chatbot:** `1-pre-game-declaration.txt`

**Exact extracted field (verbatim), appearing for both groups:**

> `"signature": "ed25519:base64-signed-blob"`

**What this proves:** Ed25519 appears **in the attachment example**.
**What this does NOT prove:** that Ed25519 is the required algorithm.

**Primary-PDF cross-check (performed by us):** Ch 5 p.55–56 requires the Step-0
specification to be *"נחתם קריפטוגרפית באמצעות מפתח המסופק מראש, כך שלא ניתן לזייפו
בדיעבד"* — cryptographically signed using a **pre-supplied key** so it cannot be forged
retroactively. **The PDF names no algorithm.**

**Final classification: ATTACHED-EXAMPLE-MECHANISM.** Ed25519 becomes a **supported
compatibility profile**, never a SOURCE-MANDATORY algorithm. It does, however,
independently corroborate that the intended mechanism is **producer authentication**,
not a bare digest.

---

## AE-03 — final-result structure

**Source filename reported by chatbot:** `4-final-result.txt`

**Exact extracted `_schema` text (verbatim):**

> "Static team metadata (identity, members, repos, MCP, hardware, model) is NOT
> repeated here — it lives in 1-pre-game-declaration.json and is referenced via
> game_id / group_id."

**Extracted structure (semantic areas, as reported):** `_schema`, `schema_version`,
`report_type`, `game_id`, `game_uid`, `links`, `timezone`, `groups`, `num_sub_games`,
`sub_games[]`, `final_result`, `mutual_agreement`.

**Per sub-game (as reported):** `sub_game_number`, `roles`, `started_at`, `ended_at`,
`result`, `winner_group`, `tie`, `github_commit`, `tokens`, `score`, `log_files`,
`audit`.

**`final_result` (as reported):** `total_score`, `sub_games_won`, `ties`,
`winner_group`, `series_tie`, `tokens_total_series`, `games_played_including_this`,
`first_meeting_between_groups`, `diversity_reward_applied`.

**`mutual_agreement` (as reported):** `sha256`, `confirmed`.

**Primary-PDF cross-check (performed by us) — this is the decisive one:**
- **Ch 9 p.78, four-file list — DECLARATION:** *"מרכזת את **כל הנתונים הקבועים של המשחק
  כולו** … זהות שתי הקבוצות וחבריהן, כתובות מאגרי השוטר והגנב, **כתובות שרתי ה-MCP,
  מפרטי החומרה**, מודל השפה, תקרת הטוקנים המוסכמת, וזמני תחילת המשחק וסיומו."*
- **Ch 9 p.78 — RESULT:** *"דוח התוצאות הסופי. סיכום כלל תת-המשחקים: ניקוד כל קבוצה בכל
  משחקון והתוצאה המצטברת, לשקלול ציון הליגה."*
- **Ch 9 p.79 — mandatory report fields:** *"השדות המחייבים בדוח כוללים את **קישורי
  ה-GitHub של שתי הקבוצות**, את **מזהה הקומיט של כל משחקון**, ואת **סך הטוקנים
  שנצרכו**."*
- **App F Table 20:** declaration = static game/team metadata; result = final league
  result; and the table *"היא טבלת ייחוס בלבד … ואינה נתונה למשא ומתן"*.

**Result:** the attachment's non-duplication statement **agrees with the PDF's own
artifact-role split**. This is the basis for the Stage-2A-R2 correction to
`RESULT_CONTRACT.md` (see `STAGE1_CLARIFICATION_IMPACT.md`).

**Final classification: ATTACHED-SCHEMA-EXAMPLE — corroborating, not binding.**
Individual keys/values are **not** automatically mandatory (see §"Why AE-03 is not a
1:1 schema" below).

---

## AE-04 — config `_note` keys

**Source filename reported by chatbot:** `2-agreed-config.txt`

**Exactly two `_note` keys reported:** root `_note` and `world._note`.
**Explicitly absent from the reported attachment:** `_axis_note`,
`_hint_max_words_note`.

**No extracted rule** states that `_note` is mandatory or generally allowed — the keys
simply exist in the example.

**Note on the reference repository (separate evidence level):** the *reference repo's*
`config/*/game.json` contains `_note`, `_axis_note` **and** `_hint_max_words_note` —
i.e. the reference and the attachment **already differ from each other**, which is
itself evidence that these comment keys are presentational, not contractual.

**Final classification: ATTACHED-EXAMPLE-CONVENTION.** Not mandatory, not forbidden.
See `COMPATIBILITY_PROFILES.md` for the strict/compatibility split.

---

## Why AE-03 must not be promoted to a 1:1 parser schema

1. **The PDF itself calls the four attachments examples** (App F §3, verified above).
2. **`_schema` / `_note` are explanatory example metadata**, not contract fields.
3. **The extracted result states its own filenames are examples.**
4. **Internal inconsistency in the extraction:** `links.log` is reported as
   `log_<game_id>_g<NN>.json` (the official Table-20 convention) while
   `sub_games[].log_files` uses illustrative names such as
   `police_match_S01R02G001.json` / `thief_match_S01R02G001.json`, which **do not match
   Table 20**. A binding schema would not contradict Table 20 inside itself.
5. **The extraction is not proven literal:** the chatbot used an ellipsis/comment for
   omitted sub-games, so the reported text is **not** demonstrably parser-ready JSON.
6. **Provenance:** it is CHATBOT-SOURCE-EXTRACTION, not bytes we opened.

**Final classification: ATTACHED-SCHEMA-EXAMPLE — NOT VERIFIED-PARSER-SCHEMA.**

## Where each artifact-name conflict is resolved

Where the attachment example conflicts with **Table 20** on filenames, **Table 20
wins** — it is primary, explicitly non-negotiable, and the official artifact-name
authority. Our emitters therefore always use:
`declaration_<game_id>.json`, `config_<game_id>_g<NN>.json`,
`log_<game_id>_g<NN>.json`, `result_<game_id>.json`.
