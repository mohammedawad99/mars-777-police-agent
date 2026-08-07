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
| **FastMCP endpoints** | `teams.<g>.mcp_endpoint` | **SOURCE-SEMANTIC (MANDATORY, K3)** + PC | **Required** | url | **Ch 9 p.94** | **self-contained** (INV-12); no secret in URL |
| **hardware declaration data** | `teams.<g>.hardware` | **SOURCE-SEMANTIC (MANDATORY, K3)** + PC | **Required** | object | Ch 9 p.94; Ch 5 p.55 | the OS/CPU/RAM/GPU/model snapshot |
| **hardware-authentication evidence** | `teams.<g>.hardware_auth` `{auth_alg,key_id,auth_tag}` | **SOURCE-SEMANTIC (MANDATORY, K3: "cryptographically-signed hardware declarations")** + PC | **Required** | object | Ch 9 p.94; Ch 5 p.55–56 | copy/reference of the **Step-0 keyed auth** so the lecturer can verify what was declared (INV-13); **no key material** |
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
- **SOURCE-SEMANTIC: 22** (identities, four links, **FastMCP endpoints**, **hardware declaration + `hardware_auth`** (K3), scores, outcomes, tokens, timestamp, mutual approval, `result_sha256`).
- **PROJECT-CONTRACT (keys/representation): all SOURCE-SEMANTIC keys** (JDEC-008 scores; JDEC-009 four-links; JDEC-013 `hardware_auth` primitive).
- **EXAMPLE-ONLY: 0** adopted.
- **REVIEW-REQUIRED: 0** — `result_sha256` is resolved to a SHA-256-backed mutual acknowledgement (NDEC-006), and the K3 report contents are mandatory (INV-10/12/13). The keyed-auth **primitive** for `hardware_auth` is a labelled PROJECT-CONTRACT default (JDEC-013), not an open item.

**Four GitHub links (INV-04, JDEC-009):** the book requires *four* links (both
teams' police+thief) in the emailed JSON (Ch 9 p.96, E-49) but names no JSON key →
SOURCE-SEMANTIC requirement + PROJECT-CONTRACT representation. **Do not invent
nesting beyond a defensible 4-URL structure.**

## Stage 1D.1 — self-contained report (K3) + reporting sanction (K4/C-09)

Ch 9 p.94 lists, among the required report contents, the **FastMCP server addresses**
and **cryptographically-signed hardware declarations** backed by SHA-256 mutual
acknowledgements. The emailed `result` must therefore be **verifiable from itself**:

- **FastMCP endpoints** (`teams.<g>.mcp_endpoint`) — **Required** (INV-12); match the
  declaration; no secret in the URL.
- **Hardware declaration** (`teams.<g>.hardware`) + **keyed-authentication evidence**
  (`teams.<g>.hardware_auth = {auth_alg,key_id,auth_tag}`) — **Required** (INV-13). The
  evidence is the **Step-0 keyed authentication** (K1) carried into the report so the
  grader can confirm what hardware was declared and that it was signed with the
  pre-supplied key. **No key material** — only the non-secret `key_id`.
- **Reporting sanction (C-09):** a required report **missing from either team** **or**
  **contradictory** reports ⇒ **game invalid, 0 to both** (App E #35, stricter than the
  Ch 9 per-side non-credit; see `CONFLICT_REGISTER.md` C-09). Both teams must send
  matching reports (`result_sha256` equal, `mutual_agreement:true`) or neither scores.

The keyed-auth objects are **never self-referential** (the `auth_tag` excludes the
envelope) and are **domain-separated** from the config/Step-0 by `context`.

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
