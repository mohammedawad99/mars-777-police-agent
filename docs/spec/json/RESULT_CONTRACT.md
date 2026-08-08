# Result Contract — `result_<game_id>.json` — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Contract
specification only — no JSON file, no schema, no code.**

The final results report for a game/series: per-sub-game and cumulative scores,
for league scoring by the lecturer. **This is the binding report emailed** (as a
**JSON attachment**, never free text — **JSON-001, JSON-002**) by **each** team
separately to `rmisegal+uoh26finalgame@gmail.com` (**REPORT-001, REPORT-002**).
Primary sources: **Ch 9 §9.3.3 (PDF p.94–95)**, **Ch 9 §9.4 (PDF p.96)**, **App E
#49, #54 (PDF p.149–150)**, App F Table 20 (PDF p.157).

**Provenance note:** the book requires the *fields* but prints no JSON layout →
most keys are **SOURCE-SEMANTIC** with **PROJECT-CONTRACT** naming (JDEC-008/009).
`github_commit` is SOURCE-EXPLICIT (Ch 5 p.56).

## Field inventory

| Semantic field | Proposed key | Provenance | Required? | Type | Source | Notes |
|---|---|---|---|---|---|---|
| game id | `game_id` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.94; App F Tbl 20 | INV-01 |
| shared uid | `game_uid` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.95 | INV-01 |
| team A identity | `teams.group_a.group_id/name` | SOURCE-SEMANTIC + PC | Required | object | Ch 9 p.94 | 8-char id (SUB-003) |
| team A members | `teams.group_a.members[]` | SOURCE-SEMANTIC + PC | Optional | array | Ch 9 p.94 | where required |
| team B identity/members | `teams.group_b.*` | SOURCE-SEMANTIC + PC | Required | object | Ch 9 p.94 | — |
| four GitHub links | `github_links` (4) | **SOURCE-SEMANTIC** (four links required) + PC representation | Required | object/array(4 urls) | Ch 9 p.96; App E #49 | INV-04; JDEC-009 |
| declaration reference | `declaration_ref` (via `game_id`/`game_uid`; `group_id`) | SOURCE-SEMANTIC (four artifacts share `game_uid`; declaration owns static data) + PC key | Required | object/string | Ch 9 p.78 (four-file list); App F Tbl 20 | **Stage 2A-R2:** joins result → declaration. FastMCP endpoints, full hardware and `hardware_auth` are **declaration-owned and NOT duplicated here** (JDEC-014) |
| per-sub-game scores | `sub_games[]` | SOURCE-SEMANTIC + PC | Required | array[object] | Ch 9 p.95; E-48 | one per sub-game |
| — sub-game number | `sub_games[].sub_game` | SOURCE-SEMANTIC + PC | Required | int | Ch 9 p.95 | INV-02 |
| — police score | `sub_games[].cop_score` | SOURCE-SEMANTIC + PC | Required | int | App F Tbl 17 | per scoring table |
| — thief score | `sub_games[].thief_score` | SOURCE-SEMANTIC + PC | Required | int | App F Tbl 17 | — |
| — outcome | `sub_games[].outcome` | SOURCE-SEMANTIC + PC | Required | enum(`capture`/`survival`/`tie`/`technical_loss`) | Ch 3; E-48; C-07 | technical_loss 0/0 (C-07) |
| — played commit | `sub_games[].github_commit` | **SOURCE-EXPLICIT** | Required | string(sha) | Ch 5 p.56; GIT-003 | per sub-game |
| — tokens (sub-game) | `sub_games[].tokens` | SOURCE-SEMANTIC + PC | Required | int | Ch 5 p.56; E-54; PERF-001 | — |
| cumulative cop | `cumulative.cop_total` | SOURCE-SEMANTIC + PC | Required | int | Ch 9 p.95 | — |
| cumulative thief | `cumulative.thief_total` | SOURCE-SEMANTIC + PC | Required | int | Ch 9 p.95 | — |
| series outcome / tie | `cumulative.series_outcome` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.87 (tie rule) | LEAGUE-006 |
| total tokens (series) | `total_tokens` | SOURCE-SEMANTIC | Required | int | E-54; PERF-001 | — |
| timestamp | `timestamp` | SOURCE-SEMANTIC + PC | Required | string(ISO-8601 UTC) | Ch 9 p.94 | JDEC-011 |
| mutual-agreement flag | `mutual_agreement` | SOURCE-SEMANTIC + PC | Required | bool | Ch 9 p.94; E-35 | both teams agree |
| mutual approval hash | `result_sha256` | SOURCE-SEMANTIC (SHA-256-backed approval required) → **NEGOTIATED-PRE-MATCH** | Required | string(hex) | Ch 9 p.94; E-35/36 | SHA-256 over the **agreed result core**, stored **outside** the core (non-self-ref); both teams' reports must be **present and carry the same** `result_sha256` (NDEC-006). Missing-from-either-side **or** contradictory ⇒ **0 to both** (**C-09**). No PKI invented. |
| reporting team | `reported_by` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.94 | each team sends its own |

## Classification totals

- **SOURCE-EXPLICIT: 1** (`github_commit`, per sub-game).
- **SOURCE-SEMANTIC: 9 semantic-field rows** (identity/`declaration_ref`, team identity, four links, per-sub-game set, cumulative, total tokens, timestamp, mutual approval, `result_sha256`) — **Stage 2A-R2**: the three K3 static-metadata rows were removed (declaration-owned).
- **PROJECT-CONTRACT (keys/representation): all SOURCE-SEMANTIC keys** (JDEC-008 scores; JDEC-009 four-links; **JDEC-014** declaration reference).
- **EXAMPLE-ONLY: 0** adopted.
- **REVIEW-REQUIRED: 0** — `result_sha256` is resolved to a SHA-256-backed mutual acknowledgement (NDEC-006), and static metadata is referenced, not duplicated (INV-10 corrected; INV-12/13 retargeted to the declaration — see §Stage 2A-R2).

**Four GitHub links (INV-04, JDEC-009):** the book requires *four* links (both
teams' police+thief) in the emailed JSON (Ch 9 p.96, E-49) but names no JSON key →
SOURCE-SEMANTIC requirement + PROJECT-CONTRACT representation. **Do not invent
nesting beyond a defensible 4-URL structure.**

## Stage 1D.1 — reporting sanction (K4/C-09)

> **SUPERSEDED IN PART BY STAGE 2A-R2 (below).** Stage 1D.1's K3 conclusion — that the
> emailed result must itself carry FastMCP endpoints, full hardware declarations and
> `hardware_auth` — over-read §9.3.3 against the Ch 9 four-file list and App F Table 20,
> which assign that static metadata to the **declaration**. The self-containment
> requirement is satisfied by the **four-artifact set**, not by the result file alone.
> The reporting-sanction finding (K4/C-09) below is **unchanged and still binding**.
- **Reporting sanction (C-09):** a required report **missing from either team** **or**
  **contradictory** reports ⇒ **game invalid, 0 to both** (App E #35, stricter than the
  Ch 9 per-side non-credit; see `CONFLICT_REGISTER.md` C-09). Both teams must send
  matching reports (`result_sha256` equal, `mutual_agreement:true`) or neither scores.

The keyed-auth objects are **never self-referential** (the `auth_tag` excludes the
envelope) and are **domain-separated** from the config/Step-0 by `context`.

## Stage 2A-R2 — FOUR-ARTIFACT-SET SELF-CONTAINMENT (corrects Stage-1D.1 K3)

**Decision: the *artifact set* is self-contained, not the result file alone.**

**Primary evidence (PDF, re-read directly).**
- **Ch 9 (p.78), four-file list — the DECLARATION** "מרכזת את **כל הנתונים הקבועים של
  המשחק כולו** (כלל תת-המשחקים): זהות שתי הקבוצות וחבריהן, **כתובות מאגרי השוטר והגנב,
  כתובות שרתי ה-MCP, מפרטי החומרה**, מודל השפה, תקרת הטוקנים המוסכמת, וזמני תחילת
  המשחק וסיומו" — concentrates **all constant data**: both groups' identity and members,
  police/thief repo addresses, **MCP server addresses, hardware specs**, model, token
  cap, start/end times.
- **Ch 9 (p.78) — the RESULT** "דוח התוצאות הסופי. סיכום כלל תת-המשחקים: ניקוד כל קבוצה
  בכל משחקון והתוצאה המצטברת, לשקלול ציון הליגה" — the final results report: per-sub-game
  scores + cumulative, for league weighting.
- **Ch 9 (p.79) — mandatory report fields** "השדות המחייבים בדוח כוללים את **קישורי
  ה-GitHub של שתי הקבוצות**, את **מזהה הקומיט של כל משחקון**, ואת **סך הטוקנים שנצרכו**".
- **App F Table 20** assigns *static game/team metadata* → declaration; *final league
  result* → result; and states the table "היא טבלת ייחוס בלבד … ואינה נתונה למשא ומתן".

**Documented book-internal tension.** §9.3.3 (p.77) describes the emailed report as
containing "כל פרטי הזהות של הקבוצה, כתובות ה-GitHub שלה, **כתובות שרתי ה-FastMCP,
הצהרות חומרה חתומות קריפטוגרפית**, חותמת-הזמן … ואישורי הסכמה-הדדית מגובי SHA-256".
Read literally that would duplicate declaration-owned data. **Resolution:** §9.3.3
describes the *information scope of the reporting package*; Table 20 and the Ch 9
four-file list define the *physical placement*, and both put static metadata in the
declaration. The attached example (secondary provenance, AE-03) agrees: *"Static team
metadata … is NOT repeated here — it lives in 1-pre-game-declaration.json and is
referenced via game_id / group_id."* We therefore **reference, not duplicate**, and the
**declaration is delivered as part of the same four-artifact set**, so the lecturer
still receives every element §9.3.3 lists.

**STRICT_COUNTED_MATCH result content (mandatory):**

1. `game_id`, `game_uid` — identity/join keys (INV-01).
2. `declaration_ref` — explicit join to `declaration_<game_id>.json` (**JDEC-014**).
3. `teams.<g>.group_id` (+ name) — minimal identity needed to attribute scores.
4. `github_links` — **four** links (explicitly mandatory, p.79; SUB-004, INV-04).
5. `sub_games[]` — `sub_game`, `cop_score`, `thief_score`, `outcome`,
   **`github_commit`** (explicitly mandatory, p.79), `tokens`.
6. `cumulative` — per-team totals + series outcome.
7. `total_tokens` — explicitly mandatory (p.79; PERF-001, E-54).
8. `timestamp` — game timestamp (§9.3.3).
9. `mutual_agreement` + `result_sha256` — SHA-256-backed mutual approval (§9.3.3);
   missing-from-either-side **or** contradictory ⇒ **0 to both** (C-09, INV-11).
10. `reported_by` — each team sends its own report (REPORT-001).

**NOT duplicated in the result** (declaration-owned, referenced by `game_uid`):
FastMCP/MCP endpoints · full hardware specifications · `hardware_auth` evidence ·
full member lists · full repository metadata beyond the four required links · LLM model
· agreed token cap · start/end times.

**Compatibility.** `LECTURER_ATTACHMENT_COMPATIBILITY` may align naming/nesting with the
extracted attachment example, and may **inline** static metadata if a grader parser is
shown to require it — never weakening any mandatory semantic. See
`../../reference/COMPATIBILITY_PROFILES.md`.


## RESULT APPROVAL CORE — the one hashing model (non-self-referential)

**`result_sha256 = SHA256( canonical_bytes( RESULT_APPROVAL_CORE ) )`**

**INCLUDED in the core** (the content both peers must agree on):
`game_id` · `game_uid` · `declaration_ref` · each team's `group_id` ·
`github_links` (the four required links) · `sub_games[]` each with
{`sub_game`, `cop_score`, `thief_score`, `outcome`, `github_commit`, `tokens`} ·
`cumulative` · `total_tokens` · `timestamp`.

**EXCLUDED from the core (must not be in the bytes hashed):**
1. **`result_sha256` itself** — the hash field can never be part of the bytes from
   which its own value is computed;
2. **`mutual_agreement`** (agreement *state*, recorded after the hash is agreed);
3. `reported_by` and any reporter-local presentation metadata outside the approval core.

**Agreement flow.** Both peers independently build the same canonical approval core,
compute `result_sha256`, exchange it, and only then — with both values equal — set
`mutual_agreement = true`. *(Stage 4F-R1 internal consistency correction: this section
previously wrote `mutual_agreement.sha256` and `mutual_agreement.confirmed`, treating
the field as an object, while the field table, the scoring rule and the JSON example
all define `mutual_agreement` as a **bool** beside the separate top-level
`result_sha256`. The object form also duplicated `result_sha256` inside itself. The
exclusion semantics are unchanged: neither the approval hash nor the agreement state
may sit inside the bytes it approves.)*
Unequal hashes, or a report missing from either side, ⇒ **0 to both** (C-09, INV-11).

**NON-SELF-REFERENTIAL: YES.** This is the same discipline already applied to
`config_sha256` and every `auth_tag` (JDEC-010) — the digest is stored **outside** the
bytes it covers. No keyed signature is introduced for result approval: the source
requires a SHA-256-backed **mutual acknowledgement**, not producer authentication.

## RESULT ↔ DECLARATION JOIN INVARIANT

- `declaration_ref == "declaration_<game_id>.json"` (official Table-20 filename);
- `result.game_id   == declaration.game_id`;
- `result.game_uid  == declaration.game_uid`;
- each `result.teams.<g>.group_id == declaration.teams.<g>.group_id`.

**No second identity is created** — the join reuses the existing source-named
`game_id`/`game_uid` (INV-01). The **four GitHub links remain in the result** even though
repository metadata is otherwise declaration-owned, because Ch 9 p.79 makes them an
explicitly mandatory *report* field (SUB-004, INV-04).

## Illustrative example (Markdown only; placeholder identifiers/scores)

Fields marked **[PC]**; **[RR]** = review-required. Example uses valid Appendix F
score values (capture cop 20 / thief 5).

```json
{
  "game_id": "mars777-vs-groupx-2026w1-uid0001",
  "game_uid": "uid0001",
  "reported_by": "MaRs-777",
  "timestamp": "2026-08-07T01:00:00Z",
  "mutual_agreement": true,
  "teams": {
    "group_a": { "group_id": "MaRs-777", "group_name": "MaRs-777" },
    "group_b": { "group_id": "GROUP-XY", "group_name": "Group X" }
  },
  "github_links": {
    "group_a_police": "https://github.com/mohammedawad99/mars-777-police-agent",
    "group_a_thief": "https://github.com/mohammedawad99/mars-777-thief-agent",
    "group_b_police": "https://github.com/other/pol",
    "group_b_thief": "https://github.com/other/thf"
  },
  "sub_games": [
    {
      "sub_game": 1,
      "cop_score": 20, "thief_score": 5,
      "outcome": "capture",
      "github_commit": "2113e68d141ab087b849f83a7d91d66620e8ad85",
      "tokens": 0
    }
  ],
  "cumulative": { "cop_total": 20, "thief_total": 5, "series_outcome": "group_a_lead" },
  "total_tokens": 0
}
```

- `github_links` uses a 4-key object — **[PC]** representation of the SOURCE-SEMANTIC
  "four links" requirement (JDEC-009).
- `sub_games[]` / `cumulative` nesting is **[PC]** (JDEC-008).
- `result_sha256` (mutual approval) intentionally **omitted** from the example — its
  value depends on the agreed result core (**NDEC-006**). Both teams' reports must
  carry the **same** `result_sha256`; a mismatch or one-sided report ⇒ 0 to both.
  No PKI signature is invented (Stage 1D §H).
- `github_commit` is the **only SOURCE-EXPLICIT** key. No secrets; scores conform to
  Appendix F.
