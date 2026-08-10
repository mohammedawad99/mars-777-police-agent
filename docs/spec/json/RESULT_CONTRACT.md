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
| — played commit | `sub_games[].github_commit` | **SOURCE-EXPLICIT** (key); participant-scoped nesting **PROJECT-CONTRACT** | Required | **object `{group_a, group_b}`, each a 40-hex commit** *(Stage 4E-R13-R1; was a bare `string(sha)`)* | Ch 5 p.56; GIT-003 | per sub-game, **both** participants' exact played commit |
| — tokens (sub-game) | `sub_games[].tokens` | SOURCE-SEMANTIC + PC | Required | **object `{group_a, group_b}`, each `int >= 0`** *(Stage 4E-R13-R1; was a bare `int`)* | Ch 5 p.56; E-54; PERF-001 | per sub-game, **both** participants' reported actual usage |
| cumulative cop | `cumulative.cop_total` | SOURCE-SEMANTIC + PC | Required | int | Ch 9 p.95 | — |
| cumulative thief | `cumulative.thief_total` | SOURCE-SEMANTIC + PC | Required | int | Ch 9 p.95 | — |
| series outcome / tie | `cumulative.series_outcome` | SOURCE-SEMANTIC + PC | Required | string | Ch 9 p.87 (tie rule) | LEAGUE-006 |
| total tokens (series) | `total_tokens` | SOURCE-SEMANTIC | Required | **object `{group_a, group_b}`, each `int >= 0`** *(Stage 4E-R13-R1; was a bare `int`)* | E-54; PERF-001 | **derived**: each participant's total is the sum of its six sub-game values |
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

## Stage 4E-R13 — ResultAgreement reconciliation

> **Blocker RESOLVED at Stage 4E-R13-R1 (see §Stage 4E-R13-R1 below).** This section is
> retained as the reasoning trail. Two of its statements are superseded there: the
> `RESULT-APPROVAL-CORE-JOINT-DERIVABILITY` blocker of **§R13-2** is now
> **RESOLVED-PROJECT**, and the digest-only request shape of **§R13-4** is replaced by a
> request carrying the sender's `ResultContribution` — a peer cannot compute the common
> digest before it holds the opponent's contribution. Everything else here — the
> mutual-audit precondition, identity association, multiplicity, response semantics,
> disagreement behaviour, lifecycle, non-self-reference, the four named links, the
> six-sub-game inventory and the timestamp rule — stands unchanged.

### R13-1 — what this stage determined, and the one thing it could not

The `ResultAgreement` peer family was blocked on its **payload shape**. That shape is
now determinate (R13-3…R13-9). What is **not** determinate is something the shape sits
on top of: **whether both peers can independently construct a byte-identical
`RESULT_APPROVAL_CORE` at all.** See **R13-2**. The family therefore stays blocked, with
its label sharpened from `BLOCKED-BY-PAYLOAD-SHAPE` to
**`RESULT-APPROVAL-CORE-JOINT-DERIVABILITY: BLOCKED-BY-CORE-COMPOSITION`**. The
peer-family inventory is unchanged at **8**.

### R13-2 — the blocker, exactly

`PRD06-FR-145` requires that *"both peers compute the core independently and compare"*,
and `PROTOCOL_TIMELINE.md` event 13 lists what each team knows **before** constructing
it. `PRD06-FR-141` and NDEC-006 put inside that core three members that are **per-team**,
not joint:

| Member | Why it is not jointly derivable |
|---|---|
| `sub_games[].tokens` | each team's **own** actual LLM consumption, metered privately by `infra.metrics` via `TokenAccountingPort` (`STATE_OWNERSHIP.md`) |
| `total_tokens` | the same quantity aggregated over the series |
| `sub_games[].github_commit` | the declaration carries **one commit per team** (`teams.<g>.github_commit`) and **INV-05** binds the result's per-sub-game commit to it — a single value cannot equal both teams' |

**No frozen contract transmits the opponent's token consumption before the digest is
computed.** The Step-0 declaration carries the token **cap**, not usage; the audit
disclosure core carries commitments, nonces and sealed members but **no token field**
(the log artifact has exactly nine rows, none of them tokens); and timeline event 14
transmits `result_sha256` **only**. So a peer cannot place the opponent's figures in its
core, and if each peer uses **its own** figures the two cores differ, the digests never
match, and **`E-REPORT-DISAGREE` ⇒ 0 to both fires on every conforming match** — the
mechanism would be unusable rather than merely strict.

Three readings are possible and **none is stated anywhere**: the values are (a) the
reporting team's own, (b) the two teams combined, or (c) a per-team pair inside the core.
(a) is self-defeating; (b) and (c) both require an exchange step that no contract
defines. Choosing among them changes **what the approval core contains**, which is a
supervising decision, not a payload-shape decision — the same class as the
Stage 4E-R10-R3 move-rejection ruling. **This stage deliberately does not guess.**

`timestamp` has the same joint-derivability question but is **resolvable without a
ruling**, and R13-9 resolves it.

### R13-3 — mutual-audit precondition (frozen)

`ResultAgreement` may be produced only after **local** final audit has passed.
`PRD02-FR-022` already encodes it: `SERIES_COMPLETE → FINAL_AUDIT → REPORT_READY`, with
`FINAL_AUDIT` forbidding *"report before audit"* and `REPORT_READY` entered only on
*"audit verified"*. `FinalAuditVerdict` stays **LOCAL** (C-11): no `Verified OK`,
`TAMPERED`, recomputed digest or audit reason is transmitted to enable agreement, and a
peer's claim that its own audit passed is **never** evidence for the receiver. Each side
relies on its own recomputation over the audit material it received.

### R13-4 — series-control scope and identity (frozen)

`ResultAgreement` is **game-final / series-control**. It carries **no `TurnCursor`, no
`step`, no `phase`, no `sub_game` sentinel**. It must bind `game_id`, `game_uid`,
`declaration_ref` and `result_sha256` so that a stale digest from another game or another
declaration can never be accepted; group identity is **not** carried separately, because
each team's `group_id` is already inside the hashed core and the operation direction is
already authenticated. The join invariants of §RESULT ↔ DECLARATION JOIN apply unchanged.

### R13-5 — multiplicity and response (frozen)

Symmetric and bounded, matching `REPORT_READY`'s inbound *"peer result hash"*:

1. each peer independently builds `RESULT_APPROVAL_CORE`;
2. each independently computes `result_sha256`;
3. each sends **exactly one** `ResultAgreement`;
4. each verifies the peer's identity binding and digest against its own local value;
5. only on mutual equality does the local state become reporting-ready and
   `mutual_agreement` be set **true**.

**No unbounded dialogue, no "first sender wins", no unilateral result, no score
negotiation.** Per **O1/O2** the response path is ordinary **successful operation
completion**; there is **no `ResultAck`, `ResultAgreementAck`, `ResultAcceptedMessage` or
`accepted: bool`, and no ninth family**.

### R13-6 — disagreement (frozen; C-09 preserved)

| Condition | Outcome |
|---|---|
| malformed message | **`E-PROTO-MALFORMED`** |
| wrong phase / duplicate / stale | **`E-PROTO-STALE`** |
| `game_id`, `game_uid`, `declaration_ref` or group-id mismatch, or a locally reconstructed core that differs | **`E-REPORT-DISAGREE`** |
| `result_sha256` mismatch | **`E-REPORT-DISAGREE`** — *"`result_sha256` differs / contradictory reports"*, evidence *"both result cores"* |
| a required report absent from either side | **`E-REPORT-DELIVERY`** / C-09 |

All of these preserve **C-09**: missing-from-either-side **or** contradictory ⇒ **game
invalid, 0 to both** (App E #35, INV-08/INV-11) — the stricter Appendix-E rule, **never**
the weaker Ch 9 per-side non-credit reading. **No error ID was created.** A pre-submit
digest mismatch is **not** TAMPERED: TAMPERED belongs to commitment recomputation
(INV-06, `E-REPLAY-MISMATCH`), and no retroactive repair after submission exists.

### R13-7 — artifact lifecycle and non-self-reference (frozen)

One authoritative result semantic value with three **documentation lifecycle labels** —
**LOCAL-DRAFT** (independently constructed), **PEER-AGREED** (digests equal),
**PERSISTED-FINAL** (`result_<game_id>.json` written with the agreed core, its digest and
the reporter's presentation fields). **These are labels, not three schemas**, and no
second `ApprovalBundle` model is introduced. `RESULT_APPROVAL_CORE` is a **deterministic
projection** of that one value; `ResultAgreement` **binds its digest** rather than
carrying the result twice.

Non-self-reference holds mechanically: `result_sha256` hashes the core only, and the core
excludes `result_sha256`, `mutual_agreement`, `reported_by` and all reporter-local
presentation metadata. **Filename, filesystem path, email message id, Gmail delivery
status and any Git commit of the result file itself are outside the core.**

### R13-8 — four GitHub links (frozen representation)

**Four named keys, never positional**: `github_links.{group_a_police, group_a_thief,
group_b_police, group_b_thief}` — a 4-key object, **PROJECT-CONTRACT** (JDEC-009) over the
SOURCE-SEMANTIC "four links" requirement (Ch 9 p.96; App E #49; INV-04). Named keys remove
list-order ambiguity from the hashed core. **No fifth link, no reordering, and the links
must match the repositories declared in the declaration (INV-04).**

### R13-9 — timestamp agreement (PROJECT-CONTRACT, frozen)

`timestamp` is inside the hashed core, so both peers must hold the **identical string**;
JDEC-011 fixes the format (ISO-8601 UTC, `Z`) but no rule established a common **value**.
Frozen: the timestamp is **proposed by the peer whose `group_id` sorts first** under exact
byte-wise ascending comparison of the two ids — the same deterministic tie-break the
config-negotiation initial proposal uses (`CONFIG_CONTRACT.md` R12-FIX-I) — and the other
peer **adopts that exact string verbatim**, never re-deriving it from its own clock and
never normalising it. A differing value is a core difference and therefore
`E-REPORT-DISAGREE`. This removes the race without adding a field, a message or a clock
dependency in the hashed bytes.

### R13-10 — six sub-games (frozen)

`num_games = 6` is **FIXED** (App F Table 18 #1; C-05), so a counted series' `sub_games[]`
carries **exactly six** entries with `sub_game` covering **1…6, each exactly once** — no
duplicate, no gap, no seventh. Each entry carries exactly
`{sub_game, cop_score, thief_score, outcome, github_commit, tokens}`; nothing is added.
**Validation ownership:** score and outcome legality against Appendix F + the Ch 3/E-48
technical-loss 0/0 belongs to `domain.scoring` / `domain.rules` (INV-07) — the result layer
**checks consistency, it does not recompute gameplay**. `cumulative.cop_total` and
`.thief_total` MUST equal the sums of the six `cop_score` / `thief_score` values, and
`cumulative.series_outcome` follows the frozen tie rule (LEAGUE-006).

### R13-11 — what R13 did not touch

The **four-artifact-set self-containment** decision (JDEC-014) is unchanged: static
identity, endpoints, hardware, `hardware_auth`, member lists, model, token cap and
start/end times stay **declaration-owned and are not duplicated here**. `result_sha256`
remains an **unkeyed content-agreement digest** — not producer authentication, not a token
metering proof, not a digital signature, not a Git SHA, not Step-0 auth — and **no
`result_signature`, `result_auth`, `result_nonce` or `result_ack_hash` was added**. The
lecturer attachment sample stays **REFERENCE/ATTACHMENT-COMPATIBILITY** and is not a
parser-exact schema; no compatibility profile may weaken a mandatory result semantic.
Gmail, OAuth, recipients, attachment transport and quota handling remain **strictly
downstream** and untouched. **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`
is not solved here** — the core may carry final token totals, and that still does not
discharge the runtime cryptographic-locking MUST.

## Stage 4E-R13-R1 — joint derivability of the approval core (blocker resolved)

### R13-R1-1 — the ruling

**Wherever a result semantic is participant-owned, the shared
`RESULT_APPROVAL_CORE` carries the value for BOTH participants.** A scalar whose
meaning changes according to which peer emitted the report is **forbidden inside
the shared core** — that was the exact defect §R13-2 recorded. Three members are
therefore **participant-scoped two-value objects**, keyed by the canonical
participant keys this project already uses everywhere (`teams.group_a` /
`teams.group_b` in both the declaration and the result, and
`github_links.group_a_police` …):

```
sub_games[].github_commit : { "group_a": <40-hex commit>, "group_b": <40-hex commit> }
sub_games[].tokens        : { "group_a": <int >= 0>,      "group_b": <int >= 0> }
total_tokens              : { "group_a": <int >= 0>,      "group_b": <int >= 0> }
```

Exactly two keys, `group_a` and `group_b`, always both present, never a dynamic
group-id key and never a role name. **This nesting is PROJECT-CONTRACT** — the
book requires the values and the mutual agreement, and prints no nested shape;
the lecturer attachment example does **not** require it either.

**Per-group, not combined** *(supervising rationale, recorded)*: the token
**cap** is defined per group (App F Table 18 #4, and the declaration's
`token_budget_per_series`), so a single combined actual-token count would destroy
the ability to associate reported usage with the participant whose cap applies.
**No combined-total field is added** in this stage; the authoritative
`total_tokens` semantic *is* the two-group value, and a display total may be
derived downstream if ever useful.

### R13-R1-2 — participant commit lifecycle (audited, unchanged)

Ch 5 p.56 permits code to change **between games**, and the declaration is
per-game — so a participant's played commit is **fixed across the six sub-games**
of one game. Ch 9 p.79's *"the commit id of each sub-game"* is satisfied by
restating that value in each entry. **INV-05 is refined to say this explicitly
and per participant; the lifecycle itself is unchanged**, and no contradiction
between live contracts was found.

### R13-R1-3 — `ResultContribution` (supporting value, not a family)

The sender-owned values that are otherwise not jointly derivable travel in one
supporting semantic value nested inside the existing family:

```
ResultContribution(
    group_id: str,
    entries: tuple[ResultContributionEntry, ...],
)

ResultContributionEntry(
    sub_game: int,
    github_commit: GitCommitSha,
    tokens: int,
)
```

**Structural validation:** exactly **six** entries; `sub_game` covering **1…6,
each exactly once**, in ascending order; `tokens` an exact `int >= 0` with `bool`
rejected; `github_commit` a `GitCommitSha` (40 lowercase hex, the existing
40-hex representation given a name — it is **not** `Sha256Digest`, which is 64
hex over an unkeyed SHA-256); `group_id` a non-empty exact `str`.

**It carries only sender-owned, not-jointly-derivable values.** Scores, outcomes,
`cumulative`, `timestamp`, `github_links` and `declaration_ref` are **excluded** —
they are already jointly derivable or already carried by the `ResultAgreement`
identity.

### R13-R1-4 — `ResultAgreement` request (supersedes the R13 digest-only shape)

§R13-4's digest-only request is **superseded**: a peer cannot compute the common
digest until it holds the opponent's contribution, so the digest cannot be in the
request.

```
ResultAgreement(
    game_id: str,
    game_uid: str,
    declaration_ref: str,
    contribution: ResultContribution,
)
```

Field order exactly `(game_id, game_uid, declaration_ref, contribution)` —
identity first, sender contribution last. **`result_sha256` is NOT in the
request.** Nor is `accepted`, `ok`, `mutual_agreement`, `reported_by`, any score,
or the full result core. No `TurnCursor`, `step`, `phase` or `sub_game`
sentinel — this stays game-final control scope.

> **AMENDED at Stage 4E-R13-R2 — one field added: `timestamp`.** Excluding it
> here left the non-proposer with **no frozen channel** by which to learn the
> exact timestamp string it must place in the common core, while §R13-9 requires
> a single agreed value inside the hashed core. The final shape is
> `ResultAgreement(game_id, game_uid, declaration_ref, timestamp, contribution)`
> — see **§R13-R2**. `timestamp` is a **jointly approved core value**, not
> participant-owned evidence, so it sits beside the identity and **not** inside
> `ResultContribution`, which is unchanged.

### R13-R1-5 — the operation response

Per **O1/O2**, the operation-specific successful response to a valid request is a
single **`Sha256Digest`**: the receiver's **locally computed** `result_sha256`,
formed after combining the received contribution, its own contribution and all
jointly known core values. It is **not** wrapped in `accepted: true`, is **not**
a `ResultAck`/`ResultAgreementAck`, and is **not a ninth family** — an operation
result is never a semantic family (**O1**). Transport, parse, authentication and
protocol failures stay with their owning layers and never reach this result.

### R13-R1-6 — multiplicity and the two-direction completion gate

**Each peer sends exactly one `ResultAgreement` request**, and returns exactly
one response to the request it receives — so per series A→B and B→A, two
requests and two responses. Transport retries are a lower-layer policy and are
**not** semantic multiplicity. No unbounded negotiation, no first-sender winner,
no score bargaining.

A peer may set `mutual_agreement = true` **only when both directions have
completed**:

1. it has successfully processed the **opponent's** request, so it holds both
   contributions and has computed its own `RESULT_APPROVAL_CORE` and
   `result_sha256`; **and**
2. its **own outgoing** request completed successfully and the opponent's
   returned `Sha256Digest` **exactly equals** that locally computed value.

Sending its own request, receiving the other contribution, or returning its own
digest are each **insufficient alone**. If the opposite request never arrives, or
the opposite digest response never arrives, there is **no mutual agreement**, and
the reporting deadline layer applies C-09 / `E-REPORT-DELIVERY` at the proper
time.

### R13-R1-7 — deterministic joint construction, and the derivability proof

With both contributions available, both peers build the same values by the same
rule — for every sub-game `i` and each participant `g`:

- `sub_games[i].github_commit.<g>` = `g`'s contributed commit for `i`
- `sub_games[i].tokens.<g>` = `g`'s contributed token count for `i`
- `total_tokens.<g>` = **sum of `g`'s six contributed sub-game token values** —
  derived, never separately transmitted, so one semantic fact has one
  representation. **Invariant:** `total_tokens.<g> == Σ sub_games[i].tokens.<g>`.

Every other core member continues to come from its already-frozen joint source:
`game_id`, `game_uid`, `declaration_ref`, the two `group_id`s and `github_links`
(declaration-joined), scores/outcomes/`cumulative` (locally computed from the
played sub-games and identical on both sides by construction, INV-07), and
`timestamp` (the §R13-9 deterministic proposer rule, jointly known **before**
digest construction).

**Proof.** After step 6's completion gate, each peer holds: its own contribution
(local), the opponent's contribution (received verbatim), and every jointly
derived member. Each participant-scoped object is assembled from exactly those
two contributions by a fixed rule that does **not** depend on who is assembling
it — the previous defect was precisely that dependence. Canonicalization is Layer 1
(sorted keys, `(",",":")`, UTF-8, NFC, LF, no trailing newline), which is
order-independent of construction. Therefore **both peers produce identical
canonical bytes**, hence
`result_sha256 = SHA256(canonical_bytes(RESULT_APPROVAL_CORE))` is identical, and
step 6's digest equality is achievable by two honest peers rather than
unreachable.

### R13-R1-8 — trust boundary

Incoming contribution data is **untrusted**. **Structural**: types, exactly six
entries, `sub_game` 1…6 each once, `tokens` `int >= 0` (`bool` rejected), exact
`GitCommitSha` syntax. **LIVE**: the authenticated sender identity equals
`contribution.group_id`; that group is one of the two declared participants;
`game_id`/`game_uid`/`declaration_ref` match locally held values; each
contributed commit equals the participant's declared commit (**INV-05**); no
duplicate contribution from the same peer; phase is `REPORT_READY`; local
`FINAL_AUDIT` passed; the reporting window is open.

**Peer-contributed token counts are NOT independently verified actual provider
usage.** They are what the peers agree was **reported**. Establishing that every
actual LLM call was metered remains
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`**, untouched here —
no token evidence, provider receipt, hash chain, signature, ledger or root is
added to `ResultContribution`.

### R13-R1-9 — C-09 boundary

C-09 (**invalid game, 0 to both**) applies to a **required report missing** or to
**contradictory approved result evidence**. It is **not** invoked merely because
an initial, not-yet-approved peer contribution differs from a local expectation
about a value the sender legitimately owns — that is what the exchange is for.
But an **identity or commit inconsistency**, or a **final digest mismatch**, fails
agreement, and there is **no retroactive repair after final submission**.

### R13-R1-10 — reporter-local metadata and the equality boundary

What must match between peers is the **`RESULT_APPROVAL_CORE`**, semantically and
in canonical bytes. **The two physical result files need not be byte-identical**,
because `reported_by` — and any other reporter-local presentation metadata — is
excluded from the core by design and legitimately differs per sender. No live
document claims whole-file byte identity, and none may: adding reporter-local
data to the core would make agreement impossible for the same reason the
participant-owned scalars did.

### R13-R1-11 — error ownership and module identity

Existing IDs only; **error IDs remain 20**: malformed contribution ⇒
`E-PROTO-MALFORMED`; wrong phase/duplicate/stale ⇒ `E-PROTO-STALE`; wrong
game/declaration/group, commit-or-core inconsistency, or returned-digest mismatch
⇒ `E-REPORT-DISAGREE`; missing delivery ⇒ `E-REPORT-DELIVERY`; own-side fault ⇒
`E-LOCAL-DEFECT`.

`ResultAgreement` belongs in **`app.peer_final_messages`** (currently 71 of its
150 permitted lines), re-exported identity-equal through the **`app.peer_messages`**
façade per **D32**. `ResultContribution`, `ResultContributionEntry` and
`GitCommitSha` belong in a sibling **`app.result_values`** module — the same
pattern as `app.sealed_record_values` and `app.auth_values` — because the three
values plus their validation will not fit beside the existing final-message
classes within the 150-line rule. `Sha256Digest` is reused unchanged from
`app.protocol_values`. Final file split is confirmed by measured LOC at
implementation time (**D32**).

### R13-R1-12 — status

**`RESULT-APPROVAL-CORE-JOINT-DERIVABILITY: RESOLVED-PROJECT`.** The core is
jointly derivable, `ResultAgreement` is **READY-TO-IMPLEMENT**, and the
peer-family inventory is unchanged at **8** — `ResultContribution` is a supporting
value nested inside the family, and the `Sha256Digest` response is an operation
result, so neither is a ninth family. **No `FIELD_MATRIX` row was added or
removed**: the three refinements are nested-shape changes to existing rows, and
the total stays **74 = 15 / 39 / 9 / 11**.

## Stage 4E-R13-R2 — timestamp carriage and deterministic agreement cadence

### R13-R2-1 — the gap this closes

§R13-9 froze a single agreed `timestamp` **inside** `RESULT_APPROVAL_CORE`, with
the deterministic proposer being the participant whose `group_id` is byte-wise
lower. §R13-R1-4 then replaced the digest-only request with one carrying
`ResultContribution` — and explicitly **excluded** `timestamp` from both the
request and the contribution. The result was a real hole: **the non-proposer had
no frozen semantic channel by which to learn the exact timestamp string it must
place in the common core.** Each side generating its own clock value is
forbidden, so the cores could not match.

**Resolution: carry the common timestamp in the `ResultAgreement` request.**
`timestamp` is **not** removed from the core — R13 froze it there and no live
contradiction requires moving it — and it is **not** added to
`ResultContribution`, which stays exactly as R13-R1 froze it, because a jointly
approved core value is not participant-owned evidence.

### R13-R2-2 — final `ResultAgreement` request shape

```
ResultAgreement(
    game_id: str,
    game_uid: str,
    declaration_ref: str,
    timestamp: UtcTimestamp,
    contribution: ResultContribution,
)
```

Field order exactly `(game_id, game_uid, declaration_ref, timestamp,
contribution)` — **identity first, shared agreement context next, sender-owned
contribution last**. Still absent: `result_sha256`, `accepted`, `ok`,
`mutual_agreement`, `reported_by`, scores, the full result core, `TurnCursor`,
`step`, `phase` and any `sub_game` sentinel.

### R13-R2-3 — `UtcTimestamp` exact representation

No timestamp value type existed, so one is named. **`UtcTimestamp`** is a
representation-only immutable value wrapping the frozen JDEC-011 form:

- exactly **`YYYY-MM-DDTHH:MM:SSZ`** — **20 characters**, second precision;
- **no fractional seconds**, no offset other than the literal `Z`, no whitespace,
  no alternative separator;
- ASCII-only and therefore NFC-invariant, so it is stable under the canonical
  NFC step and safe inside hashed bytes;
- matching every live example in the declaration and result contracts
  (`"2026-08-07T00:00:00Z"`, `"2026-08-07T01:00:00Z"`).

The exact lexical form must be pinned **because the value is hashed and echoed
verbatim**: two representations of the same instant would produce different
canonical bytes. `UtcTimestamp` computes nothing and reads no clock — obtaining
the instant is a runtime duty of the proposer.

### R13-R2-4 — the timestamp proposer, named correctly

The proposer is **the participant whose `group_id` is byte-wise lower** under
exact ascending comparison of the two ids — the same deterministic tie-break used
for the config-negotiation initial proposal.

**It is NOT "`group_a`".** Audited: `group_a` / `group_b` are canonical
participant **slots**, not an ordering — the live result example places
`group_id = "MaRs-777"` in `group_a` and `"GROUP-XY"` in `group_b`, and
`"GROUP-XY"` is byte-wise **lower**, so in that example the proposer occupies the
`group_b` slot. The rule is stated on the **value**, and **the canonical group
ordering is not changed**.

### R13-R2-5 — deterministic request order

Exactly **two** `ResultAgreement` requests per series, one per peer — multiplicity
is unchanged — but their **order is deterministic**:

| # | Actor | Action |
|---|---|---|
| 1 | **proposer** | sends its single request: proposed `timestamp` + own `ResultContribution` |
| 2 | **non-proposer** | adopts the timestamp **verbatim**; now holds both contributions, the common timestamp and every other joint member; builds its local core and returns its **`Sha256Digest`** as that operation's response |
| 3 | **non-proposer** | sends its **own single** request, echoing the identical `timestamp` and carrying its own `ResultContribution` |
| 4 | **proposer** | verifies the echoed timestamp equals the one it proposed, builds the identical core, returns its **`Sha256Digest`** |
| 5 | **both** | the frozen two-direction completion gate decides `mutual_agreement` |

**No simultaneous timestamp race. No first-arrival winner.** The ordering is
application-protocol semantics, not transport behaviour.

### R13-R2-6 — digest timing, stated explicitly

The **non-proposer can** return a digest to the very first request, because at
that moment it already holds its own contribution, the proposer's contribution,
the common timestamp and every other joint core value.

The **proposer cannot** construct its digest until the non-proposer's request
arrives. It therefore **retains the digest returned to it in step 2** and compares
it once its own local core becomes derivable at step 4. **It is explicitly NOT
required that both peers hold a local digest before the first response may be
sent** — requiring that would deadlock the exchange.

### R13-R2-7 — completion gates, ordered

**Proposer** — `mutual_agreement = true` only after: it received the
non-proposer's request/contribution; it computed its local digest; the digest
returned earlier by the non-proposer **equals** that local digest; and its own
response to the non-proposer's request was successfully produced.

**Non-proposer** — only after: it processed the proposer's first request; it
computed its local digest; it sent its own request echoing the timestamp; and the
proposer returned a digest **equal** to its local digest.

**Neither direction alone is enough**, and there is no `accepted` bool anywhere.

### R13-R2-8 — retry immutability

A **transport retry re-sends the identical semantic request** — same `timestamp`,
same `contribution`, same identity. It **never** regenerates the timestamp, never
rebuilds the contribution, and is **not** an additional semantic request.
Multiplicity remains exactly two semantic requests per series; retry/backoff stays
a lower-layer Gatekeeper policy.

### R13-R2-9 — validation and error ownership

**Structural:** exact `UtcTimestamp` type and lexical form (20 characters, second
precision, literal `Z`).

**LIVE:** the proposer generates the value **once per agreement attempt** and it
is immutable thereafter; the non-proposer treats the received value as **the**
agreement timestamp and echoes it byte-for-byte; on receiving the second request
the proposer compares it with the one it proposed. **No trimming, no timezone
conversion, no reformatting, no re-precision, no local-clock replacement, no
silent normalization.**

Existing IDs only — **error IDs remain 20**: malformed timestamp ⇒
`E-PROTO-MALFORMED`; unexpected request order, duplicate or stale ⇒
`E-PROTO-STALE`; **timestamp disagreement** ⇒ `E-REPORT-DISAGREE`; digest mismatch
⇒ `E-REPORT-DISAGREE`; delivery failure ⇒ `E-REPORT-DELIVERY`; own-side fault ⇒
`E-LOCAL-DEFECT`.

### R13-R2-10 — module ownership and what is unchanged

`UtcTimestamp` joins `ResultContribution`, `ResultContributionEntry` and
`GitCommitSha` in **`app.result_values`**; `ResultAgreement` stays in
**`app.peer_final_messages`**, re-exported identity-equal through the
**`app.peer_messages`** façade per **D32**. `Sha256Digest` is reused unchanged.

Unchanged by this stage: `ResultContribution` and `ResultContributionEntry`; the
three participant-scoped core members and the `total_tokens` derivation;
`RESULT_APPROVAL_CORE` membership and its non-self-reference; one
`ResultAgreement` family, no ack family, **no ninth family**; the `FINAL_AUDIT`
precondition and LOCAL `FinalAuditVerdict`; the `reported_by` boundary — the two
physical result files may still differ only in explicitly excluded reporter-local
metadata, while the **approval-core timestamp MUST match**; **C-09** — a timestamp
disagreement prevents agreement, and a missing required exchange/report or
contradictory approved evidence still triggers the frozen sanction at its own
layer, with no retroactive repair after final submission; **no new artifact
field** and **no `FIELD_MATRIX` change** (`timestamp` is already an existing
result row); and
**`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`**, to which nothing
was added.

### R13-R2-11 — joint-derivability regression

The §R13-R1-7 proof still holds and is now complete: after step 3 both peers hold
both contributions, **the same timestamp obtained through a frozen channel rather
than assumed**, and every other joint member. Each participant-scoped object is
assembled by a rule independent of who assembles it, canonicalization is Layer 1,
so both peers produce identical canonical bytes and therefore an identical
`result_sha256`. **`RESULT-APPROVAL-CORE-JOINT-DERIVABILITY` remains
RESOLVED-PROJECT**, now without the timestamp hole.
