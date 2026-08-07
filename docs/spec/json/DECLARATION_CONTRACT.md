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
| token consumption lock | `token_usage_locked` | SOURCE-SEMANTIC | Optional | int | tokens; crypto-locked | Ch 5 p.56; PERF-002 | may live in log/result too |

## Classification totals

- **SOURCE-EXPLICIT: 1** (`github_commit`).
- **SOURCE-SEMANTIC: ~19** (identities, repos, MCP, hardware set, model, code version, token cap, times, token lock).
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
