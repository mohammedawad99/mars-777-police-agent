# Declaration Contract — `declaration_<game_id>.json` — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Contract
specification only — no JSON file, no schema, no code.**

Pre-game declaration fixing everything constant across the whole game (all
sub-games): both teams' identities and members, police & thief repo addresses,
MCP server addresses, hardware, LLM model, agreed token cap, times — and the
**Step-0** hardware declaration + the per-game **GitHub commit hash**, signed so
it cannot be forged after the fact. Primary sources: **Ch 9 §9.3.3 (PDF p.94)**
and **Ch 5 §5.5 (PDF p.55–56)**; naming via App F Table 20 (PDF p.157).

**Provenance note:** the book requires this *information* but prints almost no
JSON keys for it (exception: `github_commit`, Ch 5 p.56). So most fields are
**SOURCE-SEMANTIC** (meaning required) with a **PROJECT-CONTRACT** key (JDEC-006).
Proposed keys below are **not** claimed to be lecturer-specified.

## Field inventory

| Semantic field | Proposed key | Provenance | Required? | Type | Constraints | Source | Notes |
|---|---|---|---|---|---|---|---|
| game id | `game_id` | SOURCE-SEMANTIC + PC key | Required | string | unique per game | Ch 9 p.94; App F Tbl 20 | format = JDEC-005 |
| shared uid | `game_uid` | SOURCE-SEMANTIC + PC key | Required | string | shared by all 4 files | Ch 9 p.95 | cross-artifact invariant INV-01 |
| ~~declaration version~~ | ~~`schema_version`~~ | **REMOVED (Stage 1D, D4: REMOVE-REDUNDANT)** | — | — | — | — | dropped: not source-required; would complicate the Step-0 hash |
| team A identity | `teams.group_a.group_id` / `.group_name` | SOURCE-SEMANTIC + PC | Required | string | 8-char id, no spaces | Ch 9 p.94; SUB-003 | group_id ↔ SUB-003 |
| team A members | `teams.group_a.members[]` | SOURCE-SEMANTIC + PC | Required | array[string] | member ids | Ch 9 p.94 | Moodle per-member (SUB-002) |
| team B identity/members | `teams.group_b.*` | SOURCE-SEMANTIC + PC | Required | object | as team A | Ch 9 p.94 | — |
| police repo (per team) | `teams.<g>.repos.police` | SOURCE-SEMANTIC + PC | Required | string(url) | GitHub URL | Ch 9 p.94,96; SUB-004 | 2 per team → 4 links |
| thief repo (per team) | `teams.<g>.repos.thief` | SOURCE-SEMANTIC + PC | Required | string(url) | GitHub URL | Ch 9 p.94,96; SUB-004 | — |
| MCP endpoint (per team) | `teams.<g>.mcp_endpoint` | SOURCE-SEMANTIC + PC | Required | string(url) | public tunnel URL | Ch 9 p.94; NET-001 | no secret in URL |
| hardware: OS | `teams.<g>.hardware.os` | SOURCE-SEMANTIC + PC | Required | string | — | Ch 5 p.55 | Step-0 |
| hardware: CPU cores | `…hardware.cpu_cores` | SOURCE-SEMANTIC + PC | Required | int | — | Ch 5 p.55 | Step-0 |
| hardware: CPU freq | `…hardware.cpu_freq_ghz` | SOURCE-SEMANTIC + PC | Required | number | GHz | Ch 5 p.55 | Step-0 |
| hardware: RAM | `…hardware.ram_gb` | SOURCE-SEMANTIC + PC | Required | number | GB | Ch 5 p.55 | Step-0 |
| hardware: GPU present | `…hardware.gpu` | SOURCE-SEMANTIC + PC | Required | string/bool | model or false | Ch 5 p.55 | Step-0 |
| hardware: VRAM | `…hardware.vram_gb` | SOURCE-SEMANTIC + PC | Optional | number | GB | Ch 5 p.55 | if GPU present |
| LLM model | `teams.<g>.llm_model` | SOURCE-SEMANTIC + PC | Required | string | model name | Ch 5 p.55; Ch 9 p.94 | e.g., provider/model |
| code version | `teams.<g>.code_version` | SOURCE-SEMANTIC + PC | Required | string | — | Ch 5 p.55 | — |
| played commit hash | `teams.<g>.github_commit` | **SOURCE-EXPLICIT** (field named `github_commit`, Ch 5 p.56) | Required | string(sha) | 40-hex | Ch 5 p.56; GIT-003 | updated per game |
| agreed token cap | `token_budget_per_series` | SOURCE-SEMANTIC | Required | int | ≥ App F floor? (NEGOTIABLE) | Ch 9 p.94; App F Tbl 18 #4 | mirrors config |
| game start time | `times.game_start` | SOURCE-SEMANTIC + PC | Required | string(ISO-8601 UTC) | JDEC-011 | Ch 9 p.94 | — |
| game end time | `times.game_end` | SOURCE-SEMANTIC + PC | Optional | string(ISO-8601 UTC) | JDEC-011 | Ch 9 p.94 | may be set at close |
| Step-0 keyed-auth algorithm | `step0_auth.auth_alg` | SOURCE-SEMANTIC (keyed auth REQUIRED, K1); algorithm = PC (JDEC-013) | Required | string | e.g. `"HMAC-SHA256"` | Ch 5 p.55–56 | keyed authentication, **not** a bare hash |
| Step-0 key reference | `step0_auth.key_id` | SOURCE-SEMANTIC (pre-supplied key, K1) | Required | string | **non-secret id only** | Ch 5 p.55–56 | **key material NEVER stored** |
| Step-0 authentication tag | `step0_auth.auth_tag` | SOURCE-SEMANTIC (signed w/ pre-supplied key, K1); primitive = PC | Required | string(hex) | over `"step0" ‖ canonical(Step-0 core)` | Ch 5 p.55–56 | **non-self-referential** (excludes the envelope); NDEC-005 |

## Classification totals

- **SOURCE-EXPLICIT: 1** (`github_commit`).
- **SOURCE-SEMANTIC: ~18** (identities, repos, MCP, hardware set, model, code version, token cap, times). *(Stage 4E-R12-R1 removed the `token_usage_locked` row — see §R12-R1.)*
- **PROJECT-CONTRACT (key choice): all SOURCE-SEMANTIC keys** (JDEC-006 naming).
- **EXAMPLE-ONLY: 0** adopted (none promoted).
- **PROJECT-CONTRACT primitive: 1** (`step0_auth` = keyed authentication envelope; algorithm HMAC-SHA256 default — JDEC-013).

**Step-0 is KEYED authentication, not a bare hash (K1, corrected Stage 1D.1).**
The book **requires** the Step-0 declaration to be **cryptographically signed with
a pre-supplied key** so it cannot be forged retroactively (Ch 5 p.55–56 — SOURCE-
REQUIRED). The exact **primitive** is source-unspecified → project default
**HMAC-SHA256** (JDEC-013), carried as the `step0_auth` envelope `{auth_alg,
key_id, auth_tag}`. The **key** is pre-supplied out-of-band and **never** appears
in any artifact; only the non-secret `key_id` is stored. The `auth_tag` is
**non-self-referential** (computed over `"step0" ‖ core`, excluding the envelope).
Do **not** downgrade this to an unkeyed SHA-256 digest, and do **not** call it an
asymmetric digital signature. See `SIGNATURE_AND_HASH_PROVENANCE.md`, NDEC-005.

## Illustrative example (Markdown only; identifiers are placeholders, not real match data)

Fields marked **[PC]** are PROJECT-CONTRACT keys. The `step0_auth` envelope
(`auth_alg`/`key_id`/`auth_tag`) is intentionally **omitted** below — its `auth_tag`
value depends on the pre-supplied key (never shown) and the canonical Step-0 core.

```json
{
  "game_id": "mars777-vs-groupx-2026w1-uid0001",
  "game_uid": "uid0001",
  "token_budget_per_series": 200000,
  "times": { "game_start": "2026-08-07T00:00:00Z", "game_end": null },
  "teams": {
    "group_a": {
      "group_id": "MaRs-777",
      "group_name": "MaRs-777",
      "members": ["id-1001", "id-1002"],
      "repos": {
        "police": "https://github.com/mohammedawad99/mars-777-police-agent",
        "thief": "https://github.com/mohammedawad99/mars-777-thief-agent"
      },
      "mcp_endpoint": "https://example-tunnel.invalid/mcp",
      "hardware": { "os": "Linux", "cpu_cores": 8, "cpu_freq_ghz": 3.2, "ram_gb": 16, "gpu": false },
      "llm_model": "template",
      "code_version": "0.0.0",
      "github_commit": "0000000000000000000000000000000000000000"
    },
    "group_b": {
      "group_id": "GROUP-XY",
      "group_name": "Group X",
      "members": ["id-2001", "id-2002"],
      "repos": { "police": "https://github.com/other/pol", "thief": "https://github.com/other/thf" },
      "mcp_endpoint": "https://other-tunnel.invalid/mcp",
      "hardware": { "os": "Windows", "cpu_cores": 4, "cpu_freq_ghz": 2.6, "ram_gb": 8, "gpu": false },
      "llm_model": "template",
      "code_version": "0.0.0",
      "github_commit": "1111111111111111111111111111111111111111"
    }
  }
}
```

- `github_commit` is the **only SOURCE-EXPLICIT** key here; all other keys are **[PC]** naming choices for SOURCE-SEMANTIC requirements (JDEC-006).
- `game_id`/`game_uid` are **source-named** (Ch 9 p.95); only their formats are **[PC]** (JDEC-005). `schema_version` is **removed** (D4).
- `step0_auth` keyed-authentication envelope intentionally **omitted** — its `auth_tag`
  depends on the pre-supplied key (never shown). It is **keyed** authentication (K1,
  JDEC-013/NDEC-005), not a bare hash and not a PKI signature.
- No secrets, no tokens, no real member data; placeholder repos/endpoints use `.invalid`.

## Stage 4E-R12 — the STEP-0 AUTHENTICATED CORE (frozen)

`PRD06-FR-023`, `INV-14`, `NDEC-005` and `DATA_FLOW.md` all authenticate
`"step0" ‖ canonical(step0_core)`, but **no document defined `step0_core` as a
field list**. `DATA_FLOW.md` sketched it in prose ("hardware, OS/CPU/RAM/GPU,
model, code version, `github_commit`, token cap, identities, times") — a sketch,
not a boundary, and two peers cannot recompute a tag from a sketch. This section
freezes it. It **adds no field**: every member is an existing declaration row, and
`FIELD_MATRIX.md` was then **75 = 16/39/9/11** with **16** declaration rows; **Stage 4E-R12-R1 removed the `token_usage_locked` row, so the current baseline is 74 = 15/39/9/11 with 15 declaration rows** — the statement that this section adds no field is unaffected.

### Own-subtree, and why the event ordering forces it

The declaration file carries **both** teams (`teams.group_a`, `teams.group_b`),
but each team produces its **own** Step-0 tag at **timeline event 1**, before it
has received the opponent's subtree. A core spanning both teams could not be
computed by either side at the moment the message is sent, and would make each
team vouch for data it cannot observe. The core is therefore **the producing
team's own subtree plus the shared game identity** — a consequence of the
chronology, not a preference.

### Members (exact)

| In the core | Member |
|---|---|
| ✅ | `game_id`, `game_uid` — bind the tag to one game; without them a valid tag replays into a different game |
| ✅ | `times.game_start` |
| ✅ | own `teams.<g>.group_id`, `.group_name`, `.members[]` |
| ✅ | own `teams.<g>.repos.police`, `.repos.thief` |
| ✅ | own `teams.<g>.mcp_endpoint` — `PRD05-FR-013` requires the endpoint to be verified before counted play, which is meaningless if the endpoint is unauthenticated |
| ✅ | own `teams.<g>.hardware.{os,cpu_cores,cpu_freq_ghz,ram_gb,gpu}` (+ `vram_gb` when present) |
| ✅ | own `teams.<g>.llm_model`, `.code_version`, `.github_commit` |
| ✅ | `token_budget_per_series` — the **agreed token cap**, which Ch 9 §9.3.3 lists among the declaration's constant data and whose signing is that artifact's stated role. A cap is knowable before play; **actual** consumption is not, and is not here *(Stage 4E-R12-R1)* |
| ❌ | **`step0_auth` itself** — non-self-reference (`PRD06-FR-025`); the envelope is never part of the bytes it authenticates |
| ❌ | **the opponent's `teams.<g>` subtree** — not observable at event 1 |
| ❌ | **actual consumed tokens** — a runtime quantity that does not exist before the first move; App E #54 and Ch 9 §9.3.3 place it in the **result** *(Stage 4E-R12-R1; this row previously excluded `token_budget_per_series`, which is now correctly **included** above)* |
| ❌ | **`times.game_end`** — explicitly "may be set at close", so it is mutable after the tag exists |

Serialization is **Layer 1** canonical JSON (`sort_keys`, `(",",":")`, UTF-8,
NFC, LF, no trailing newline) over the core object; the framing of
`context ‖ core` is the fixed pre-match framing of `CANONICALIZATION_CONTRACT.md`
Layer 4. **Absent optional members are omitted, never emitted as `null`**
(`PRD06-FR-008`); both peers must therefore agree presence, not just value.

### Cadence

The Step-0 declaration and its `AuthProof` are produced **once per game
(series)** — matching `declaration_<game_id>.json`, one file per game, with
`github_commit` "updated per game". This is deliberately **not** the config
cadence: `config_<game_id>_g<NN>.json` and its `config_auth` are produced **once
per sub-game**. A single Step-0 tag therefore covers all sub-games of the series,
while `INV-15`'s config verification recurs for each. `INV-14` is read
accordingly — the per-sub-game obligation it states is satisfied by the
series-level tag remaining valid, not by re-signing Step-0 per sub-game.

If the declared public ingress must be replaced mid-series, `PRD05-FR-015b`
already forbids silent mutation; because `mcp_endpoint` is inside the core, such a
replacement necessarily produces a **new declaration and a new `AuthProof`**,
which is the intended and now-explicit consequence.

### Family readiness

With the core, the profile provisioning (`SIGNATURE_AND_HASH_PROVENANCE.md`
R12-A), the vocabulary (R12-B) and the encodings (R12-C) frozen, the Step-0
peer-visible family carries exactly the declaration content above plus the
`{auth_alg, key_id, auth_tag}` envelope, and nothing else. Concrete tool
signatures remain deferred to Stage 2B-2C (`PRD02-FR-035`), as for every family.

**Readiness withheld at R12-FIX, restored at Stage 4E-R12-R1.** The single
unmapped member was `token_usage_locked`; the primary-source audit in §R12-R1 shows
it never belonged in this artifact. With it removed the core is exact, and
**`STEP0-TOKEN-LOCK-PLACEMENT` is CLOSED**.

## Stage 4E-R12-FIX — exact Step-0 readiness proof

### R12-FIX-1 — `token_usage_locked` cannot be mapped exactly (BLOCKER)

> **SUPERSEDED at Stage 4E-R12-R1 — retained as the reasoning trail.** The two
> contradictions below were real, and the primary-source audit in §R12-R1 explains
> why: the field itself did not belong in this artifact. It is now **removed**, so
> neither contradiction survives and **`STEP0-TOKEN-LOCK-PLACEMENT` is CLOSED**.
> Read the rest of this subsection as history, not as a live blocker.

`PRD06-FR-029` states the LLM token-consumption record **MUST be inside the
authenticated Step-0 core**, classified **SOURCE-MANDATORY** through **CRYPTO-011**
("Lock LLM token record at Step-0", Mandatory, Both) and **PERF-002**
("Monitor/lock tokens at Step-0", Mandatory, Both). Two live statements contradict
that, and both sit in documents this stage may not edit:

1. **Optionality.** The declaration field inventory above marks
   `token_usage_locked` **Optional**, and `FIELD_MATRIX.md` row `D` records it
   `Opt`. A member that a conforming declaration may omit cannot also be a
   mandatory member of an authenticated core — a verifier cannot know whether an
   absent member means "omitted" or "stripped", and `PRD06-FR-008` forbids
   emitting `null` inside a hashed payload, so absence is not distinguishable
   from removal.
2. **Placement and cardinality.** `FIELD_MATRIX.md` gives the row cardinality
   **1** with the unqualified key `token_usage_locked`, exactly like the genuinely
   shared `token_budget_per_series` — while every per-team datum in the same
   table is written `teams.<g>.…` with cardinality **1/team** (`hardware`,
   `llm_model`, `code_version`, `github_commit`). Yet the same row's status reads
   **"own reported datum"**, and CRYPTO-011/PERF-002 make the locked token count
   each team's own. **A single top-level integer cannot carry two teams' own
   locked token counts** in the one merged `declaration_<game_id>.json` that
   `INV-01` requires.

**Why this is not resolved here.** Fixing (1) means changing a field's
Required/Optional status; fixing (2) means editing `FIELD_MATRIX.md`'s key path
and cardinality. Stage 4E-R12-FIX forbids both, and neither is a Step-0 *core
definition* question — both are declaration-contract questions that happen to be
exposed by defining the core. Guessing either way would silently reclassify a
SOURCE-MANDATORY requirement.

**Recorded blocker:
`STEP0-TOKEN-LOCK-PLACEMENT: BLOCKED-BY-FIELD-PLACEMENT`.** Everything else about
Step-0 is exact and is frozen below, so this is a **narrow, single-field**
blocker, not a re-opening of the family. It does **not** affect Config negotiation
or Config lock, which carry no declaration field.

### R12-FIX-2 — the authenticated core, enumerated member by member

No `teams.<g>` shorthand. Every participating member of the producing team's
subtree, exactly as the live field inventory above names it:

| # | Member | Live row |
|---|---|---|
| 1 | `game_id` | game id |
| 2 | `game_uid` | shared uid |
| 3 | `times.game_start` | game start time |
| 4 | `teams.<g>.group_id` | team identity |
| 5 | `teams.<g>.group_name` | team identity |
| 6 | `teams.<g>.members[]` | team members |
| 7 | `teams.<g>.repos.police` | police repo |
| 8 | `teams.<g>.repos.thief` | thief repo |
| 9 | `teams.<g>.mcp_endpoint` | MCP endpoint |
| 10 | `teams.<g>.hardware.os` | hardware: OS |
| 11 | `teams.<g>.hardware.cpu_cores` | hardware: CPU cores |
| 12 | `teams.<g>.hardware.cpu_freq_ghz` | hardware: CPU freq |
| 13 | `teams.<g>.hardware.ram_gb` | hardware: RAM |
| 14 | `teams.<g>.hardware.gpu` | hardware: GPU present |
| 15 | `teams.<g>.hardware.vram_gb` | hardware: VRAM — **conditional**: present exactly when `hardware.gpu` is not `false`, so presence is derivable and not a free option |
| 16 | `teams.<g>.llm_model` | LLM model |
| 17 | `teams.<g>.code_version` | code version |
| 18 | `teams.<g>.github_commit` | played commit hash |
| 19 | `token_budget_per_series` | agreed token cap *(added Stage 4E-R12-R1)* |

`Σ` = **19 exact members, none blocked** *(Stage 4E-R12-R1)*. `mcp_endpoint` (#9) is **inside** so
`PRD05-FR-013`'s pre-play endpoint verification authenticates something;
`github_commit` (#18) is inside as source identity evidence, and **`PRD06-FR-030`
still applies — being inside an authenticated core does not make a Git hash
authentication**; the six hardware members (#10–#15) and `llm_model`/`code_version`
(#16–#17) are the CRYPTO-006 signed hardware declaration.

**Canonical construction.** `AuthProof.value = KEYED_AUTH_key("step0" ‖
canonical(step0_core))`, where `canonical` is Layer 1 of
`CANONICALIZATION_CONTRACT.md` (sorted keys, `(",",":")`, UTF-8, NFC, LF, no
trailing newline) and `‖` is the fixed pre-match Layer-4 framing. Absent
conditional members are **omitted, never `null`** (`PRD06-FR-008`). The core is a
nested object mirroring the declaration paths above; it is **not** flattened and
**not** a second copy of the declaration.

### R12-FIX-3 — exclusions, each with its reason

| Excluded | Reason |
|---|---|
| `step0_auth.auth_alg`, `.key_id`, `.auth_tag` | **Non-self-reference** (`PRD06-FR-025`) — the envelope is never inside the bytes it authenticates. Substitution is defeated by **comparison** (R12-A), not by inclusion, and the `AuthProfile` is additionally bound inside the config lock context |
| the **opponent's** `teams.<g>` subtree | Not observable at timeline event 1; a team cannot authenticate data it has not received |
| **actual consumed tokens** | A runtime quantity that does not exist before the first move. App E #54 and Ch 9 §9.3.3 place it in the **result**; the declaration's source-stated role is "everything that does not change during the game" *(Stage 4E-R12-R1)*. The **cap** `token_budget_per_series` **is** in the core |
| `times.game_end` | The live row says "may be set at close" — mutable after the tag exists |
| local-only metadata (logger mechanics, artifact paths, GUI state, private timeouts) | Never declaration content at all (`JDEC-007` as amended; `PRD02-FR-056`) |
| **all key material** | `PRD06-FR-026`/`SEC-003` — only the non-secret `key_id` is ever serialized, and it is in the envelope, not the core |

### R12-FIX-4 — exact future semantic shape

The exchange carries the **single authoritative declaration semantic value**, not
a flattened second copy:

```
Step0DeclarationExchange(
    declaration: Declaration,
    auth: AuthProof,
)
```

Field order is exactly `(declaration, auth)` — subject first, evidence second, the
same ordering discipline the turn families use. `Declaration` is the one semantic
value owning the members enumerated in R12-FIX-2; `AuthProof` is the
profile-tagged value frozen in `SIGNATURE_AND_HASH_PROVENANCE.md` R12-FIX-A.
**Series-control scope only**: no `TurnCursor`, no `sub_game`, no `step`, no
`phase`, no score, no timestamp beyond the declared `times`, and no secret.

### R12-FIX-5 — cadence and success semantics

**One authenticated Step-0 declaration exchange per peer per series.** The single
admitted re-issue is a **genuinely changed declaration** — the
`PRD05-FR-015b` public-ingress replacement being the contracted case — which
produces a new declaration and therefore new authentication evidence; it is never
a silent mutation and never a second exchange over the same declaration.

**Success is ordinary operation completion**, following `API_BOUNDARIES.md` O2/O6.
There is **no `Step0Ack` family, no `accepted` bool, no verdict and no ninth
family**; failure is raised by the layer that owns it.

### R12-FIX-6 — structural vs LIVE split, and error ownership

**Structural (constructor / value level):** exact member types; `members[]`
non-empty; `github_commit` exactly 40 lowercase hex; URLs non-empty strings;
`cpu_cores`/`ram_gb` exact `int` (never `bool`); `cpu_freq_ghz` a `Decimal` under
the existing `require_decimal` policy; `AuthProof` well-formed per its profile.
Composition only — no key, no network, no clock.

**LIVE (runtime layer):** `auth_alg`/`key_id` equal to the locally provisioned
expectation; `AuthProof` cryptographic verification; peer identity matching the
negotiated `group_id` (`PRD02-FR-061`); endpoint publicity and reachability
(`PRD05-FR-002/013/021`); replay/staleness; the negotiation window.

**Error ownership — existing IDs only, none created:** malformed member or
malformed proof representation ⇒ **`E-PROTO-MALFORMED`**; well-formed proof that
fails verification, or an `auth_alg`/`key_id` difference ⇒ **`E-AUTH-FAILURE`**
(⇒ refuse counted play, `PRD06-FR-027`); out-of-phase or stale exchange ⇒
**`E-PROTO-STALE`**; delivery failure ⇒ **`E-TRANSPORT`** / **`E-RETRY-EXHAUSTED`**;
own-side construction fault ⇒ **`E-LOCAL-DEFECT`**. **No technical-loss score is
invented for a pre-game failure.**

### R12-FIX-7 — future module and façade identity

`Step0DeclarationExchange` is **`app.peer_pregame_messages`**
*(narrowed Stage 4E-R14-R1-FIX: this sentence also named `Declaration`, which
§R14-R1-8 subsequently placed in **`app.declaration_values`** — `Declaration` is
declaration **subject data**, not a peer-message family, and there is exactly one
definition of it)*
— the fourth defining peer-message module, sibling to the frozen
`app.peer_turn_messages` and `app.peer_final_messages`, re-exported as
identity-equal classes through the **`app.peer_messages`** façade exactly as
**D32** fixed the organization. `AuthProfile`/`KeyId`/`AuthProof` are
**`app.auth_values`** — a new module rather than `app.protocol_values`, which is
already **137** of its **150** permitted lines. Assembly and the keyed computation
stay outside the semantic layer in `protocol.declaration` and
`protocol.keyed_auth`, which `MODULE_BOUNDARIES.md` already owns. Final file
splits are confirmed by measured LOC at implementation time, per **D32**.

## Stage 4E-R12-R1 — token accounting: the source, and why this artifact holds a cap

### R12-R1-1 — what the source actually says

**Ch 5 §5.5** (the Step-0 section, PDF p.55–56):

> "The whole spec is packed into a JSON string and **cryptographically signed
> using a pre-supplied key**, so it cannot be forged retroactively. **In parallel
> (`במקביל`), all of the language model's token consumption is monitored
> (`מנוטרת`) and is also cryptographically locked, in order to prevent denial of
> the computational resources that were actually consumed (`שנצרכו בפועל`)."

Two obligations, joined by `במקביל` — "in parallel". The **spec JSON** is what is
signed. Token consumption is a **separate, continuously monitored** quantity that
is "**also**" locked. The source never says the consumed quantity is a member of
that JSON, and "monitored" is inherently a runtime activity.

**Ch 9 §9.3.3** defines this artifact directly:

> "**[the declaration file]** — a pre-game declaration. It concentrates all the
> **constant** data of the whole game (all sub-games): identity of both groups and
> their members, police and thief repository addresses, MCP server addresses,
> hardware specs, language model, **the agreed token ceiling
> (`תקרת הטוקנים המוסכמת`)**, and game start and end times. **Its role: to fix,
> cryptographically signed, everything that does not change during the game.**"

The one token datum the source puts in this artifact is the **agreed ceiling** —
a cap — and the artifact's stated role is *everything that does not change*.
Actual consumption changes continuously by definition.

**App E #54** (`חובה` — MUST): *"Report in the final JSON file the total tokens
consumed in the sub-game (and in the series)."*
**App F Table 18 #4** (`~200000`, NEGOTIABLE): *"the total tokens for the language
model that each group **is permitted to consume**; **the actual consumption is
reported by email**."*

Both place **actual** consumption in the **result**, and both label the ~200000
value a **permission**, not a measurement.

### R12-R1-2 — consequence for this contract

The `token_usage_locked` field is **removed**. It was a repository construction,
not a source field: no binding passage names it, none places actual usage in
`declaration_<game_id>.json`, and none defines its cardinality or cryptographic
representation. Its obligation was never lost — it is carried by
`sub_games[].tokens` and `total_tokens` in `RESULT_CONTRACT.md`, both already
**Required** and both already inside the **RESULT APPROVAL CORE** covered by
`result_sha256` (NDEC-006), with both peers' reports required to match or **0 to
both** (C-09, App E #35).

**That covers the reporting duty only, and this contract does not claim more**
*(corrected Stage 4E-R12-R2)*. `result_sha256` gives the **finally reported**
totals integrity and mutual agreement. It does **not** prove that every actual
LLM call was metered, that none was omitted, that the reported totals equal
provider- or runtime-observed consumption, that either peer independently
observed the other's LLM usage, or that usage was locked at the instant it
occurred. Ch 5 §5.5's separate requirement — that actual consumption be
**monitored** and **cryptographically locked** — therefore remains a **mandatory
runtime obligation whose construction is SOURCE-UNSPECIFIED and not yet frozen**
(`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`, owned by PRD-06).
Removing `token_usage_locked` neither created that gap nor closed it: a
self-declared pre-game integer could never have satisfied a runtime metering
duty either.

**`token_budget_per_series` stays**, and is now correctly **inside** the Step-0
authenticated core. Stage 4E-R12 had excluded it as "bilateral, agreed at event
2" — reasoning from this project's own state ordering rather than from the book.
Ch 9 §9.3.3 lists the agreed ceiling among the declaration's signed constant data;
a **cap is knowable before play**, unlike a consumption total, so no temporal rule
is broken. `DATA_FLOW.md` already listed "token cap" in the Step-0 core, so this
also removes a live inconsistency the R12 exclusion had introduced.

**Consistency obligation:** the declared cap MUST equal the locked config's
`network_and_league.token_budget_per_series` — already implied by this contract's
"mirrors config" note, and now enforced by both being under authentication. Its
exact chronology — agreed **before `BOOT`**, authenticated once at event 1,
equality-only at event 2, immutable for the series — is frozen in **§R12-R3**.

### R12-R1-3 — the three token concepts, kept apart

| Concept | Value | Where | Class |
|---|---|---|---|
| **A — budget / cap** | agreed ceiling, default ~200000 | declaration `token_budget_per_series` **and** config `network_and_league.token_budget_per_series` | SOURCE-EXPLICIT (App F T18 #4; Ch 9 §9.3.3) |
| **B — actual consumption** | metered per call, per sub-game, per series | result `sub_games[].tokens`, `total_tokens` | SOURCE-EXPLICIT (App E #54; Ch 9 §9.3.3) |
| **C — cryptographic accounting evidence** | that B, **as actually consumed**, cannot be denied or retroactively altered | **not yet frozen** — `TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`, owned by PRD-06. `result_sha256` is a **different layer**: it protects the integrity and mutual agreement of the **finally reported** values in B, not the fidelity of the metering that produced them | requirement SOURCE-REQUIRED (Ch 5 §5.5); **construction SOURCE-UNSPECIFIED** *(row corrected Stage 4E-R12-R2)* |

None of these is the **token-bucket rate limiter** of Ch 9 (`rate_limiter_gatekeeper`,
outgoing Gmail pacing) or an **OAuth access/refresh token** (`token.json`,
never an artifact field). Those three words share a name and nothing else.

### R12-R1-4 — what remains SOURCE-UNSPECIFIED

Ch 5 §5.5 fixes **no** algorithm, **no** keyed/unkeyed choice, **no** per-call
chaining, **no** cumulative digest, **no** log placement and **no** disclosure
cadence for the token-accounting evidence. Only the *existence* of cryptographic
locking is required — and **it is not yet satisfied** *(corrected Stage
4E-R12-R2; an earlier draft of this section wrongly said `result_sha256`
satisfied it)*. The construction — whether a per-call record, a chain, a
cumulative digest, a keyed or unkeyed form, and where it is persisted or
disclosed — is a **future PROJECT-CONTRACT decision** recorded as
`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION` and owned by PRD-06.
**No construction is invented here**: no `TokenUsageRecord`, `TokenLedger`,
`token_usage_root`, `token_usage_digest`, provider-receipt schema, per-call MAC
or signature, hash chain, Merkle tree, new result field, new log field, new peer
message or new artifact. It is **not** a Step-0 blocker: the
Step-0 payload now contains no actual-consumption value at all, so its
representation cannot depend on that decision. **No field named `reserved_tokens`,
`predicted_tokens`, `estimated_tokens`, `token_commitment`, `token_nonce`,
`token_ledger_hash` or `token_usage_root` is created, and no baseline
`token_usage_locked = 0` is invented.**

### R12-R1-5 — Step-0 readiness

Every member of the authenticated core now satisfies all four temporal tests: it
exists when the producer authenticates Step-0, is known to that producer, must be
protected from later unilateral mutation, and is required by the source or a
current project contract. **`STEP0-TOKEN-LOCK-PLACEMENT` is CLOSED** and the
Step-0 family is **READY-TO-IMPLEMENT**.

### R12-R1-6 — one observation deliberately NOT acted on

Ch 5 §5.5 also says the Step-0 declaration documents *"the code version, the group
name, and **the sub-game number** (`מספר המשחקון`)"*. This contract has no
sub-game field, and Ch 9 §9.3.3 defines the same artifact as holding only what is
**constant across all sub-games** — so either `משחקון` here means the game
instance (already carried by `game_id`/`game_uid`), or the Step-0 *act* is
per-sub-game while the artifact is per-game. **Both readings are recorded; neither
is adopted.** This stage is chartered to the token question, the declaration's
16-row inventory was reviewed and locked at Stage 1, and resolving this would
change Step-0 cadence. **REPORT-ONLY — it requires a supervising decision in a
declaration-scoped stage, and it does not affect the token reconciliation or the
exactness of the members enumerated above.**

## Stage 4E-R12-R3 — the token cap's exact temporal law

### R12-R3-1 — the contradiction this section closes

Stage 4E-R12-R1 moved `token_budget_per_series` **into** the Step-0 authenticated
core. Stage 4E-R12's own text had excluded it as *"bilateral — agreed at config
negotiation (event 2)"*. Both statements could not stand: event 1 would have been
authenticating a value that event 2 had not yet agreed. That is not a drafting
slip — it is implementation-impossible, and it had to be resolved rather than
narrated.

### R12-R3-2 — what the committed contracts already said

The repository had already answered this, in two places written long before R12:

- **`PROTOCOL_TIMELINE.md` event 1**, "Known before" column: *"hardware,
  OS/CPU/RAM/GPU, model, code version, `github_commit`, **token cap**, identities,
  times; pre-supplied key (out-of-band)"*. The cap is listed as **known before
  event 1**.
- **`DATA_FLOW.md`**, first Step-0 step: *"Build Step-0 core (hardware,
  OS/CPU/RAM/GPU, model, code version, `github_commit`, **token cap**, identities,
  times)"*. The cap is **inside the core**.
- **`PROTOCOL_TIMELINE.md` event 2**, "Known before": *"App F floors,
  board/scent/scoring"* — the cap is **not** among what event 2 negotiates.

And the source agrees: Ch 9 §9.3.3 lists *"the agreed token ceiling"* among the
declaration's constant data and gives that artifact the role of fixing,
cryptographically signed, *"everything that does not change during the game"*.

So the outlier was Stage 4E-R12's exclusion, not R12-R1's inclusion. **MODEL A —
pre-Step-0 agreement — is adopted**, because it is what the live contracts and the
source already say; the alternatives were rejected on evidence, not on convenience.

### R12-R3-3 — the temporal law (PROJECT-CONTRACT)

> **`token_budget_per_series` is agreed before `BOOT`, authenticated once at
> event 1, and immutable for the whole series. Step-0 never authenticates a value
> that is only agreed later.**

| Property | Value |
|---|---|
| **Appendix-F status** | **NEGOTIABLE** — unchanged (App F Table 18 #4). **It is not relabelled FIXED.** |
| **Project lifecycle** | **PRE-STEP0-AGREED · SERIES-WIDE · IMMUTABLE-AFTER-STEP0** |
| **Agreed** | before `BOOT`, out of band, as local pre-match configuration |
| **Authenticated** | inside the Step-0 core at event 1, once per series |
| **At event 2** | present in every complete proposal, **equality-checked only, never counter-proposable** |
| **At event 3** | bound again transitively through `config_sha256` inside `ConfigLockContext` |
| **Across the six sub-games** | one value, unchanged |

**NEGOTIABLE is source provenance; PRE-STEP0-FROZEN is project lifecycle.** The
two are different axes and neither overrides the other: the book permits the value
to be agreed, and this project fixes *when*.

### R12-R3-4 — the agreement mechanism, and mismatch detection without a new family

The cap is **operator/pre-configured project state**, provisioned in the same
pre-match arrangement that already provisions `AuthProfile` and `KeyId`
(`SIGNATURE_AND_HASH_PROVENANCE.md` R12-FIX-C). `BOOT`'s entry condition is
already *"process start, secrets present"* and `SettingsPort` already loads local
settings before start, so the provisioning moment exists and needs no new
mechanism. The cap is **not** a secret — it is serialized in both the declaration
and the config — it merely shares that moment.

Mismatch is detected **twice, on messages that already exist**:

1. **At event 1** — each peer receives the opponent's Step-0 declaration, whose
   authenticated core contains the opponent's `token_budget_per_series`. Comparing
   it against the locally provisioned value is a plain field comparison on an
   already-frozen message.
2. **At events 2 and 3** — the value reappears in every `ConfigProposal` for
   equality, and is bound by `config_sha256` inside `ConfigLockContext`.

Either way the outcome is **`E-CONFIG-MISMATCH` ⇒ refuse counted play** — no
repair, no silent renegotiation, no preference for either side's value, and **no
technical-loss score before counted play**. **No `TokenBudgetAgreement`,
`BudgetProposal` or `BudgetAck` family is created; the peer-family inventory stays
at 8.**

### R12-R3-5 — the config-lock equality invariant

The locked config's **`network_and_league.token_budget_per_series` MUST equal the
declaration's authenticated `token_budget_per_series`.** This was already implied
by the declaration row's "mirrors config" note; it is now an explicit
pre-counted-play check owned by `E-CONFIG-MISMATCH`, verified before the
`CONFIG_LOCKED` transition. Config lock remains READY precisely because this
equality is exact and checkable from values both peers already hold.

### R12-R3-6 — what did not change

`FIELD_MATRIX.md` is untouched at **74 = 15/39/9/11**: the cap already has exactly
two rows — declaration `token_budget_per_series` and config
`network_and_league.token_budget_per_series` — and R12-R3 adds no field and
removes none. No requirement, JDEC, NDEC, INV or Conflict-Register entry was
created. `TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION` is untouched
and still visible for later Stage-4 completion, and `ResultAgreement` remains
`BLOCKED-BY-PAYLOAD-SHAPE`.

## Stage 4E-R14-R1 — the `Declaration` semantic model (implementation dependency frozen)

Stage 4E-R14 stopped **BLOCKED-BEFORE-CODE** because
`Step0DeclarationExchange(declaration, auth)` names a `Declaration` type that has
never existed in `src`. This section freezes it. **No Python is written here.**

### R14-R1-1 — the lifecycle contradiction, and why one type still suffices

Five committed facts had to become one implementable lifecycle: the Step-0 core
covers only the **producer's own** subtree plus shared identity, `game_start` and
the token cap (§R12-FIX-2); the **opponent's subtree is excluded** because it is
not observable before the event-1 exchange; **`times.game_end` is excluded**
because it may be set at close; the persisted `declaration_<game_id>.json` is a
**whole-game artifact carrying both participants**; and there is **one
authoritative `Declaration` value** that `Step0DeclarationExchange` must not
flatten into a second schema.

**Resolution (PROJECT-CONTRACT).** One immutable `Declaration` type whose
*instances* represent different lifecycle moments. Nothing is mutated in place;
each later moment constructs a **new** immutable value:

| Lifecycle moment | Content |
|---|---|
| **PARTIAL PRE-GAME SNAPSHOT** | exactly one participant subtree — the producer's own; no fabricated opponent subtree; no `game_end` |
| **MERGED PRE-GAME SNAPSHOT** | both participant subtrees, after both Step-0 exchanges; still no `game_end` |
| **FINAL ARTIFACT SNAPSHOT** | both subtrees plus the final `game_end` |

These are **lifecycle descriptions, not three classes, three wire schemas, three
peer families or a phase field**. **No `declaration_state` member is added**, and
`ProtocolPhase` does not appear in `Declaration`. Which completeness level an
operation requires is an application-level decision.

### R14-R1-2 — the 15 rows split 12 + 3

`FIELD_MATRIX.md` carries **15** declaration rows. They are **not** 15 members of
one semantic value:

- **12 subject rows** — `game_id`, `game_uid`, team identity, members, repos,
  `mcp_endpoint`, hardware, `llm_model`, `code_version`, `github_commit`,
  `token_budget_per_series`, `times` — are the **`Declaration` subject data**.
- **3 envelope rows** — `step0_auth.auth_alg`, `.key_id`, `.auth_tag` — are the
  **artifact serialization of the separately-carried `AuthProof`**.

`Declaration` therefore does **not** own an auth value: `Step0DeclarationExchange`
carries `AuthProof` beside it, the Step-0 core **excludes** the envelope for
non-self-reference (§R12-FIX-3), and a later artifact writer persists the proof
into the three envelope keys. **There is exactly one authoritative auth value and
no duplication**, and `FIELD_MATRIX` is unchanged at **74 = 15/39/9/11**.

### R14-R1-3 — exact type decomposition

```
Declaration(
    game_id:  str,
    game_uid: str,
    token_budget_per_series: int,
    times: DeclarationTimes,
    teams: DeclarationTeams,
)

DeclarationTeams(group_a: TeamDeclaration | None, group_b: TeamDeclaration | None)

DeclarationTimes(game_start: UtcTimestamp, game_end: UtcTimestamp | None)

TeamDeclaration(
    group_id: str,
    group_name: str,
    members: tuple[str, ...],
    repos: RepositoryLinks,
    mcp_endpoint: str,
    hardware: HardwareDeclaration,
    llm_model: str,
    code_version: str,
    github_commit: GitCommitSha,
)

RepositoryLinks(police: str, thief: str)

HardwareDeclaration(
    os: str,
    cpu_cores: int,
    cpu_freq_ghz: Decimal,
    ram_gb: int,
    gpu: str | Literal[False],
    vram_gb: int | None,
)
```

**No `dict[str, object]`, `Mapping[str, object]`, `Any` or free-form nested
dict.** `cpu_cores` and `ram_gb` are **exact `int`** (`bool` rejected) and
`cpu_freq_ghz` is a **`Decimal`** under the existing `require_decimal` policy —
never `float` *(corrected Stage 4E-R14-R1-FIX; an earlier draft of this block
typed `ram_gb` as `Decimal`)*. **Hash membership does not determine a semantic
numeric type**: every one of these values is inside the hashed Step-0 core, and
that fact alone says nothing about whether the quantity is integral. `gpu` is the
frozen `string/bool` union: a model name, or exactly `False` for "no GPU".
`members` is a non-empty immutable tuple. `vram_gb` is **`int | None`** under the
conditional rule frozen in **R14-R1-FIX-2**.

### R14-R1-4 — optionality matrix (every `None` has a frozen rule)

| Member | Optional? | Frozen rule |
|---|---|---|
| `teams.group_a` | yes | absent in a partial snapshot when the producer occupies the `group_b` slot |
| `teams.group_b` | yes | absent in a partial snapshot when the producer occupies the `group_a` slot |
| **at least one of the two** | **required** | a `Declaration` with neither subtree is rejected — it declares nothing |
| both present | permitted | the merged and final snapshots |
| `times.game_end` | yes | absent until close; present only in the final artifact snapshot |
| `hardware.vram_gb` | conditional | present **exactly when** `gpu is not False` — derivable, **not a free option** (§R12-FIX-2 member 15). Type **`int | None`**, with the exact conditional rule in **R14-R1-FIX-2** |

**No placeholder empty strings, no zero-as-unknown, no dummy `TeamDeclaration`.**
Absence is `None` in the semantic value; how absence is (or is not) serialized is
a later artifact concern, and **absence never becomes JSON `null` inside a hashed
Step-0 core** — the projection simply omits non-members.

### R14-R1-5 — participant-slot ownership is a LIVE rule

**Structural:** the value may hold a valid partial or merged snapshot; it infers
nothing about who sent it.
**LIVE (Step-0 validation):** the authenticated sender identity must correspond
to the participant subtree that sender is entitled to contribute; a hostile
sender may not populate or overwrite the opponent's subtree as its own
authoritative contribution. **No `sender_id` is added to `Declaration`** —
authenticated operation direction and the declared participant mapping own that
check.

### R14-R1-6 — the Step-0 core projection

`Declaration` → *deterministic producer-scoped projection* → `step0_core`. The
projection emits **only the 19 frozen members of §R12-FIX-2** and hashes neither
the whole snapshot, the opponent subtree, `times.game_end`, the `AuthProof`, nor
any artifact-local metadata. **No second semantic record type is created for the
projection**; the future `protocol.declaration` builder performs it, and
**R14-R1 does not implement that mapper.**

### R14-R1-7 — shared cross-artifact primitives

Two primitives are needed by `Declaration` now and by `ResultAgreement` later, so
they are **cross-artifact application values, not result-only values**:

- **`GitCommitSha`** — exactly 40 lowercase hex characters. The declaration row
  states "40-hex" and every live example is lowercase; `RESULT_CONTRACT.md`
  §R13-R1-3 already froze the lowercase form, so the two agree and one type
  serves `teams.<g>.github_commit` and `sub_games[].github_commit` alike.
- **`UtcTimestamp`** — exactly `YYYY-MM-DDTHH:MM:SSZ`, 20 ASCII characters,
  second precision. `times.game_start`/`game_end` use JDEC-011 ISO-8601 UTC `Z`,
  the same representation §R13-R2-3 froze for the result timestamp, and every
  live example matches. They are **unified because the contracts already agree**,
  not cosmetically.

Their module home is **`app.artifact_values`** (§R14-R1-8). *(Stage
4E-R14-R1-FIX: `RESULT_CONTRACT.md` §R13-R1-11 and §R13-R2-10 previously assigned
both to `app.result_values`, which was correct when only the result needed them.
That amendment is now authorized and applied there, so every current-live contract
agrees: `app.artifact_values` owns `GitCommitSha` and `UtcTimestamp`, while
`app.result_values` keeps `ResultContribution` and `ResultContributionEntry`.)*

### R14-R1-8 — module ownership and the R14-R2 layout

Every planned production module stays **≤150 lines**; `domain/config_model.py` is
already **150/150** and `app/protocol_values.py` **137/150**, so neither may
absorb new types.

| Module | Owns |
|---|---|
| `app.artifact_values` | `GitCommitSha`, `UtcTimestamp` |
| `app.auth_values` | `AuthProfile`, `KeyId`, `AuthProof` |
| `app.declaration_values` | `Declaration`, `DeclarationTeams`, `DeclarationTimes` |
| `app.team_declaration_values` | `TeamDeclaration`, `RepositoryLinks`, `HardwareDeclaration` |
| `app.interop_profiles` | the nine profile enums + `InteropProfileSet` |
| `app.peer_pregame_messages` | `Step0DeclarationExchange`, `ConfigProposal`, `ConfigLockContext`, `ConfigLockEvidence` |
| `domain.config_sections` (+ measured-LOC sibling) | the seven `NegotiatedConfig` section values |
| `domain.negotiated_config` | `NegotiatedConfig` |
| `app.peer_messages` | façade re-exports only — identity-equal, no duplicated classes |

**Import DAG (inward-only, D1 respected — no `domain` imports `app`):**

```
domain.board · domain.config_model · domain.actions   (existing)
        ^
domain.config_sections  ->  domain.negotiated_config
                                      ^
app.artifact_values                   |
   ^          ^                       |
app.auth_values   app.declaration_values <- app.team_declaration_values
        ^                 ^           |
        +--- app.interop_profiles ----+
                     ^
        app.peer_pregame_messages
                     ^
        app.peer_messages  (façade)
```

No cycle; no reusable value module depends on transport or protocol runtime.
`Step0DeclarationExchange` stays in `app.peer_pregame_messages` per §R12-FIX-7.

### R14-R1-9 — status

**`DECLARATION-SEMANTIC-DEPENDENCY: RESOLVED-PROJECT`.**

## Stage 4E-R14-R1-FIX — hardware types and shared-primitive ownership

### R14-R1-FIX-1 — `ram_gb` is a strict `int`, not `Decimal`

§R14-R1-3 typed `ram_gb` as `Decimal`. That contradicted the already-frozen
§R12-FIX-6 structural sentence — *"`cpu_cores`/`ram_gb` exact `int` (never
`bool`); `cpu_freq_ghz` a `Decimal` under the existing `require_decimal`
policy"* — and the live example, which prints `"ram_gb": 16` beside
`"cpu_freq_ghz": 3.2`. **Repaired to `int`.**

The reasoning that produced the error is worth naming: *"it is inside the hashed
core, therefore `Decimal`"*. **Hash membership does not determine a semantic
numeric type.** `Decimal` exists here to keep a *fractional* quantity exact under
canonical serialization; an integral quantity is already exact as an `int`, and
widening it would change the canonical bytes for no reason. This is a
derived-contract correction — **no JDEC, NDEC or Conflict-Register entry.**

### R14-R1-FIX-2 — `vram_gb` numeric type: **`int | None`** (frozen)

*(Stage 4E-R14-R1 recorded this as `BLOCKED-BY-UNFROZEN-TYPE`; the supervising
ruling at Stage 4E-R14-R1-FIX2 resolves it. The audit that produced the block is
kept below because it explains why the representation is a project decision.)*

**Why it needed a ruling.** `vram_gb` was typed **nowhere**: the live field row
says only `Optional | number | GB` — the same `number` expression that proved
ambiguous enough to cause FIX-1; §R12-FIX-6's structural sentence names
`cpu_cores`, `ram_gb` and `cpu_freq_ghz` and is **silent** on `vram_gb`;
§R12-FIX-2 member 15 freezes only its **presence** rule; and both live examples
declare `"gpu": false`, so **neither prints a `vram_gb` literal**. It was
deliberately **not inferred from a neighbouring field**.

**Ruling.** `HardwareDeclaration.vram_gb` is **`int | None`**.

**Provenance, stated exactly.** The **presence** of VRAM in the hardware
declaration is the existing SOURCE-SEMANTIC requirement (Ch 5 p.55 lists
`GPU/VRAM` among the Step-0 machine spec). The **exact numeric representation is
PROJECT-CONTRACT** — the book fixes no JSON or Python numeric subtype, and
**`int` is not source-mandated.**

**Exact conditional rule (structural):**

| `gpu` | `vram_gb` |
|---|---|
| exactly `False` | **MUST be `None`** |
| a non-empty `str` (model name) | **MUST be present**, `type(vram_gb) is int`, and `vram_gb > 0` |

**Rejected, with no coercion of any kind:** `True` · `False` as a numeric VRAM ·
`0` · a negative `int` · `float` · `Decimal` · `str` · `bytes` · `None` while
`gpu` is a model string. **No `int(value)`, no rounding, no float or Decimal
conversion, no string parsing.** The value is declared in **whole GB** under the
project semantic contract, so an integral type is exact by construction.

**The type was chosen semantically, not by hash membership.** `vram_gb` sits
inside the hashed Step-0 core, and that fact is irrelevant to the choice —
exactly the error FIX-1 corrected. The semantic type is selected by
PROJECT-CONTRACT first; canonical serialization then serializes that already-typed
value deterministically. **Hashing never determines whether a numeric field is
`int` or `Decimal`.**

**`DECLARATION-HARDWARE-VRAM-TYPE: RESOLVED-PROJECT`.** All six
`HardwareDeclaration` members now have exact implementable types, so **no R14
implementation dependency remains open.**

### R14-R1-FIX-3 — complete hardware type matrix

| Field | Frozen type | Structural validation | Provenance | Changed by R14-R1? |
|---|---|---|---|---|
| `os` | `str` | non-empty exact `str` | SOURCE-SEMANTIC + PC | no |
| `cpu_cores` | `int` | exact `int`, `bool` rejected, `> 0` | SOURCE-SEMANTIC + PC; §R12-FIX-6 | no |
| `cpu_freq_ghz` | `Decimal` | `require_decimal` policy, never `float` | SOURCE-SEMANTIC + PC; §R12-FIX-6 | no |
| `ram_gb` | **`int`** | exact `int`, `bool` rejected, `> 0` | SOURCE-SEMANTIC + PC; §R12-FIX-6 | **yes — wrongly typed `Decimal`, repaired by FIX-1** |
| `gpu` | `str \| Literal[False]` | a non-empty model name, or exactly `False` | SOURCE-SEMANTIC + PC | no |
| `vram_gb` | **`int \| None`** | conditional on `gpu`; when present, exact `int`, `bool` rejected, `> 0` | presence SOURCE-SEMANTIC + PC; **numeric representation PROJECT-CONTRACT** | no — frozen by R14-R1-FIX2 |

**All six are exact and implementable** *(Stage 4E-R14-R1-FIX2 closed the last one)*.

### R14-R1-FIX-4 — what this FIX did not touch

The Declaration lifecycle, optionality matrix, the 19-member Step-0 core
projection, the Declaration/`AuthProof` separation, `AuthProof`, `KeyId`, every
profile token, `NegotiatedConfig`, `ConfigProposal`, `ConfigLockContext`,
`ConfigLockEvidence` and its structural equality invariant, the token-budget
lifecycle, `ResultAgreement` and `FIELD_MATRIX` are all **unchanged**. Both
original blockers remain **RESOLVED-PROJECT**.
