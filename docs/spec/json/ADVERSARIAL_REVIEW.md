# Adversarial Contract Review — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Deliberate adversarial pass over the four contracts, asking the required probe
questions for each field class. Findings are risks to resolve in Stage 1D /
implementation — not defects in the source.

| # | Risk | Affected fields | Probe answered | Severity | Mitigation / status |
|---|---|---|---|---|---|
| AR-01 | **Two teams implement SOURCE-SEMANTIC keys differently and both believe they complied.** | all declaration/log/result keys (JDEC-006/07/08/09) | "Could two teams comply differently?" → **Yes** | High | Shared files (config, and any exchanged log/result fields) must be **agreed at negotiation**; our PC keys are proposals, not mandates. Interop keys → confirm with opponent. |
| AR-02 | **Canonical-serialization divergence changes SHA-256 bytes** (separators, `ensure_ascii`, float/number formatting, key order, line endings) → false TAMPERED or a real tamper slipping. | log sealed record, `config_sha256`, `approval_sha256` | "Can this change the hash bytes?" → **Yes** | **Critical** | JDEC-002 fixes the canonical params; both peers MUST use identical serialization. Non-ASCII hints make `ensure_ascii` decisive. Cross-OS (Win/Linux) LF+UTF-8 required. |
| AR-03 | **Source-explicit vs pretending.** Are we claiming keys the book didn't print? | declaration/log/result keys | "Is the source explicit or are we pretending?" → mostly **SEMANTIC** | Medium | Every non-App-B key is labelled SOURCE-SEMANTIC + PROJECT-CONTRACT (JDEC), never SOURCE-EXPLICIT. `github_commit` is the only cross-artifact SOURCE-EXPLICIT key. |
| AR-04 | **Omitted log field makes replay impossible** (e.g., missing `state`, `nonce`, or a step's commit). | log sealed record / entries | "Could an omitted field break replay?" → **Yes** | High | LOG_CONTRACT mandates the full Ch-5 record (state, move, intent, hint, step, role, sub_game, nonce) — not the simplified 4-field example. INV-06. |
| AR-05 | **Extra field leaks private opponent state** (e.g., logging the opponent's hidden position or full objective board in a shared artifact). | log, live GUI-adjacent data | "Could an extra field leak private state?" → **Yes** | High | Artifacts carry only own-side truth + committed/revealed data; **no full objective board** (GUI-001/002); nonces withheld until audit. |
| AR-06 | **Two peers produce non-identical config** (a MINIMUM lowered, a NEGOTIABLE mismatched, key spelling drift). | config sub-keys | "Could this make peers' config non-identical?" → **Yes** | **Critical** | Byte-identical load + `config_sha256` equality before play (GAME-001); floors enforced (GAME-002); SOURCE-EXPLICIT App B keys used verbatim. |
| AR-07 | **Type ambiguity breaks Win/Linux interop** (float `0.10` vs `0.1`, int vs string, coord array vs object). | pheromone floats, coords, scores | "Could type ambiguity break OS interop?" → **Yes** | High | CANONICALIZATION fixes number formatting; values copied verbatim from App F (`0.9`, `0.10`); coords are arrays as in App B. |
| AR-08 | **Reporting rejects the document** (non-JSON, wrong attachment, missing four links, missing tokens/commit). | result | "Could reporting reject it?" → **Yes** | High | RESULT_CONTRACT lists all mandatory fields; JSON-001/002; four links (INV-04); tokens (PERF-001); per-game commit (GIT-003). |
| AR-09 | **A future grader says a key was invented and presented as mandatory.** | any PROJECT-CONTRACT key | "Could a grader call this invented-as-mandatory?" → guard | Medium | All PC keys are explicitly labelled PROJECT-CONTRACT with a JDEC + academic-freedom basis; none is presented as lecturer-required. |
| AR-10 | **Signature scheme/storage invented.** | `step0_auth`, `result_sha256`, `config` auth, `config_sha256` storage | "Are we inventing a crypto scheme?" → avoided | Medium | **Updated Stage 1D.1:** the source **requires keyed authentication** for Step-0/config (K1/K2) — that is not invented. Only the **primitive** is our choice: HMAC-SHA256 is labelled **PROJECT-CONTRACT (JDEC-013)**, never lecturer-specified; an asymmetric signature is an allowed alternative if both agree. SHA-256 is never called a signature; HMAC is never called asymmetric. Key storage = out-of-band (`key_id` only). |
| AR-11 | **Simplified example mistaken for the real format** (Ch 5 4-field / Ch 7 `nonce|move`). | log payload | "Could the example be treated as complete?" → guarded | Medium | Both examples explicitly marked EXAMPLE-ONLY and NOT adopted; the fuller Ch-5 record governs. |
| AR-12 | **`num_games`/`technical_loss` regression** (illustrative `1` treated as binding; fake App F technical_loss row). | config | source-fidelity | Medium | Contract fixes `num_games=6 FIXED` (C-05 closed) and keeps `technical_loss` provenance = Ch3/E-48, C-07; no App F row invented. |

## Stage 1D additions

| # | Risk | Resolution |
|---|---|---|
| AR-13 | **`verdict` treated as a separate hashed field** → double-count → hash divergence | Resolved: `verdict` = `intent` classification (C-08); 8-field sealed set; no separate field (D1, NDEC-001). |
| AR-14 | **`state` under-specified** → peers hash different bytes → false TAMPERED | Resolved: PROJECT-LOCKED `state` (own-known only; sorted barriers) + pre-match confirm (JDEC-012, NDEC-002). |
| AR-15 | **`config_sha256` self-reference** → undefined hash | Resolved: hash over config **without** the field; stored outside (JDEC-010). |
| AR-16 | **`game_uid` presumed invented** and removed | Resolved: `game_uid` is **source-named** (Ch 9 p.95); kept (D3). |
| AR-17 | **Project field inside signed config** → breaks byte-identity | Resolved: signed config = App B keys only; `schema_version` value NEGOTIATED; no project additions (D4). |

## Stage 1D.1 additions (keyed authentication K1/K2/K3; reporting sanction C-09)

| # | Adversarial scenario | Probe | Resolution |
|---|---|---|---|
| AR-18 | **Step-0 tampered, but the attacker recomputes a valid plain SHA-256** and the game accepts it. | Does a bare hash authenticate the producer? → **No** | Step-0 requires **keyed** authentication with a pre-supplied key (K1): recomputing an unkeyed digest proves nothing without the key. A plain SHA-256 over Step-0 is **rejected** as the authenticator (NDEC-005, INV-14). |
| AR-19 | **Wrong / unshared key** — a peer signs Step-0 with a key the other side doesn't hold. | Verify fails on `key_id`/tag? → **Yes** | `key_id` mismatch or tag-verify failure ⇒ **refuse counted play** pre-game (NDEC-005). No compatible key ⇒ no counted match. |
| AR-20 | **Primitive mismatch** — one side computes HMAC-SHA256, the other treats the tag as a plain hash. | Detected before play? → **Yes** | `auth_alg` is exchanged and must match; mismatch ⇒ refuse play (JDEC-013, NDEC-005/007). HMAC ≠ plain hash ≠ PKI signature — never conflated. |
| AR-21 | **Self-referential tag** — the `auth_tag` is (wrongly) computed over bytes that include the envelope carrying it → undefined/forgeable. | Is the tag inside its own input? → **must be No** | Tag is over `context ‖ core` **only**, excluding `{auth_alg,key_id,auth_tag}` (non-self-referential, mirrors JDEC-010 for `config_sha256`). |
| AR-22 | **Cross-context replay** — a valid Step-0 tag is replayed as a config tag. | Blocked? → **Yes** | Domain separation: `context ∈ {"step0","config"}` is authenticated with the payload; a `"step0"` tag cannot validate a `"config"` verification (NDEC-005/007). |
| AR-23 | **Config hash matches but authentication is absent** — peers agree on `config_sha256` yet never prove they signed it with the pre-supplied key. | Is hash equality sufficient? → **No** (K2) | App B p.128 requires a **signature exchange**, not only equality. Missing/invalid config `auth_tag` ⇒ refuse play even if `config_sha256` matches (NDEC-007, INV-15). |
| AR-24 | **Result omits FastMCP endpoint or signed hardware declaration** → not self-contained / unverifiable. | Reporting complete? → **must be Yes** (K3) | RESULT_CONTRACT now marks FastMCP endpoints, hardware declaration, and `hardware_auth` evidence **Required** (INV-10/12/13). Omission ⇒ incomplete report ⇒ not credited. |
| AR-25 | **One-sided or contradictory report** — one team reports, the other doesn't, or they disagree. | Credit anyone? → **No** | Strictest rule (C-09): missing-from-either-side **or** contradictory ⇒ **game invalid, 0 to both** (E-35), never the milder Ch 9 per-side non-credit alone (INV-11, NDEC-006). |
| AR-26 | **Key material leaks into an artifact** (Git, JSON, log, email, error, runtime evidence). | Any secret stored? → **must be No** | Only the non-secret `key_id` is ever stored; the pre-shared key is out-of-band. Contracts state key material MUST NOT appear anywhere (JDEC-013 security block). |
| AR-27 | **Strict parser rejection** — a required keyed-auth or reporting field is missing and a strict grader parser rejects the artifact. | Could reporting reject it? → **Yes** | All new fields (`step0_auth.*`, config `auth_tag`, result FastMCP/hardware/`hardware_auth`) are specified as Required with fixed keys; FIELD_MATRIX counts updated so nothing is silently optional. |

## Material risks carried to Stage 1D / implementation

- **AR-02 / AR-06 (Critical):** canonical serialization + config byte-identity are
  the two things that can silently invalidate a match; both need a cross-peer
  byte-identity test and a config-hash handshake.
- **AR-04 / AR-05:** log completeness (replayability) vs leakage — the log must be
  complete enough to replay but must not expose private state.
- **AR-10 / AR-18–AR-23 (keyed authentication):** the source **requires** keyed
  Step-0/config authentication (K1/K2); the primitive (HMAC-SHA256) is a labelled
  PROJECT-CONTRACT default, negotiable to an asymmetric signature. A bare hash is
  **not** an acceptable authenticator; the key is out-of-band and never stored.
- **AR-24 / AR-25 (reporting, C-09):** the result must be self-contained (FastMCP +
  signed hardware, K3) and both-sided; any missing/contradictory report ⇒ 0 to both
  (strictest E-35 rule).
