# Interoperability Blockers — group MaRs-777

**Status: REVIEWED — Stage-1 supervising review PASS; baseline LOCKED. Specification only; no code/schema/JSON artifact.**

Every former Stage-1C REVIEW-REQUIRED item, resolved. Classes: **RESOLVED-SOURCE**,
**RESOLVED-PROJECT**, **RESOLVED-NEGOTIATION**, **BLOCKING**. PASS is forbidden if
any BLOCKING item prevents config agreement, Commit-Reveal verification, replay
verification, result agreement, or mandatory reporting.

| Former REVIEW-REQUIRED item | Resolution | Class | Basis |
|---|---|---|---|
| Exact `state` representation in the sealed payload | Defined: `{config_sha256, self_pos, barriers(sorted), step, role}`, own-known only; PROJECT-LOCKED default + pre-match confirm | **RESOLVED-PROJECT** (+ NDEC-002) | JDEC-012 |
| Sealed-record composition (verdict vs intent) | `verdict` = `intent` classification (C-08); 8-field payload fixed | **RESOLVED-SOURCE** (semantics) + **RESOLVED-NEGOTIATION** (exact list) | D1; NDEC-001 |
| Canonicalization params / `ensure_ascii` | PROJECT-LOCKED default; pre-match confirm | **RESOLVED-PROJECT** (+ NDEC-003) | JDEC-002 |
| `config_sha256` storage (self-reference risk) | Hashed over config **without** any embedded hash; stored **outside** (declaration/sidecar); both compute + compare | **RESOLVED-PROJECT** | JDEC-010; §I |
| Step-0 authentication scheme/key/storage (K1) | **Keyed authentication with a pre-supplied key is SOURCE-REQUIRED** (Ch 5 p.55–56) — **not** a bare SHA-256 digest. Envelope `{auth_alg,key_id,auth_tag}`; default **HMAC-SHA256** (JDEC-013, PROJECT-CONTRACT, not lecturer-specified); asymmetric signature allowed if both agree; key out-of-band (`key_id` only). No compatible key ⇒ refuse counted play. | **RESOLVED-SOURCE** (requirement) + **RESOLVED-PROJECT** (primitive) | §G; K1; NDEC-005 |
| Config signature exchange scheme/key/storage (K2) | **Signature exchange is SOURCE-REQUIRED** (App B p.128) beyond `config_sha256` equality. Keyed `auth_tag` over `"config"‖core` (HMAC-SHA256 default); verify tag **and** hash before play. | **RESOLVED-SOURCE** (requirement) + **RESOLVED-PROJECT** (primitive) | §D; K2; NDEC-007 |
| Result approval hash/signature scheme/storage | SHA-256 over agreed result core → `result_sha256`; **both** reports must be present and match or **0 to both** (C-09); no PKI invented | **RESOLVED-NEGOTIATION** | §H; NDEC-006; C-09 |
| Result self-containment (FastMCP + signed hardware, K3) | Result MUST carry FastMCP endpoints, hardware declarations, and keyed `hardware_auth` evidence (Ch 9 p.94) — mandatory, not optional | **RESOLVED-SOURCE** (requirement) + **RESOLVED-PROJECT** (keys) | K3; INV-10/12/13 |
| ack/reveal structural representation | Persistent log = LOCAL-ONLY; only the sealed payload + hash are interop | **RESOLVED-PROJECT** (LOCAL-ONLY) | D4; JDEC-007 |
| `game_uid` (thought project-invented) | **Source-named** (Ch 9 p.95); kept, reclassified SOURCE-EXPLICIT | **RESOLVED-SOURCE** | D3 |
| `schema_version` value in signed config | NEGOTIATED value (part of the byte-identical config) | **RESOLVED-NEGOTIATION** | D4; NDEC-004 |
| **Actual token-consumption accounting** *(row relabelled Stage 4E-R12-R2; the former `token_usage_locked` declaration field no longer exists — Stage 4E-R12-R1 proved it a misplaced runtime datum)* | **Reporting: resolved.** The consumed totals are `sub_games[].tokens` and `total_tokens` in the result (**App E #54**, MUST), and `result_sha256` gives those **finally reported** values integrity and mutual agreement (NDEC-006; C-09). **Runtime locking: separate and still open.** Ch 5 §5.5 also requires actual consumption to be **monitored** and **cryptographically locked**; `result_sha256` does **not** prove that every LLM call was metered, that none was omitted, or that the reported totals equal runtime/provider-observed consumption. That construction is **SOURCE-UNSPECIFIED** and not yet frozen — **`TOKEN-ACCOUNTING-CRYPTO-EVIDENCE: BLOCKED-BY-CONSTRUCTION`**, owned by **PRD-06**. **It is deliberately not listed as a blocking item below**, because it is a **LOCAL/runtime security obligation**: no peer message, artifact field, wire format or byte-level agreement depends on it today, so it prevents neither config agreement, Commit-Reveal verification, replay verification, result agreement nor mandatory reporting. If a future design makes token evidence peer-visible, it must be reclassified here at that time. | **RESOLVED-SOURCE** (reporting); the runtime mechanism is tracked in **PRD-06**, not in this register | App E #54; Ch 5 §5.5; PERF-001/002; CRYPTO-011 |

## Blocking items

**None.** Stage 4E-R11 resolved the move-rejection shape and Stage 4E-R11-R1 resolved the audit-exchange payload; both former blockers are recorded below as resolved.

| Item | Status | Class | Basis |
|---|---|---|---|
| **`AUDIT-EXCHANGE-PAYLOAD`** | **RESOLVED (Stage 4E-R11-R1).** **JDEC-007 amended in place**: internal logger mechanics and locally-derived verification annotations stay LOCAL, while the finalized per-sub-game log's **audit-disclosure core** is interoperable at final audit — one schema, no `AuditBundle`/`AuditProjection`. The `submit_audit` operation carries the exact **JSON-native audit-disclosure document** (dict/list/str/int/bool material as the log contract freezes it) — **not** a filesystem path, artifact URL, base64, pickle or Python object. Every audited commitment is reconstructible: the seven non-secret sealed members from the per-turn sealed record, `nonce` from `audit.final_reveal[]`, and `H_commit` from `entries[].commit`, all under the frozen Stage 4E-R9 canonical mapping. `entries[].verified`, `audit.result` and `audit.tampered_step` are **not transmitted** and never trusted; the receiver recomputes. Whole-log byte identity is **not** required and **no log-level hash** was added. | **RESOLVED-PROJECT** (PROJECT-CONTRACT; the source requires the disclosure, not this representation) | Ch 5 §5.4; App E mutual-log-audit row; PRD06-FR-100/101/104; `LOG_CONTRACT.md` (4E-R11-R1 section); amended **JDEC-007**; **C-11** |

Three things this blocker is **not**. It is **not a peer-message-family blocker**:
the exchange is an artifact/transport obligation and is **not** counted as an
`app.peer_messages` semantic family, so the family inventory is unaffected. It is
**not** satisfied by `FinalNonceReveal`, which carries the nonce batch only — see
the note below. And it does **not** re-open the sealed-record, canonicalization or
commitment contracts, which are frozen and implemented.

| **`MOVE-REJECTION-TRANSPORT-SHAPE`** | **RESOLVED (Stage 4E-R11).** The peer operation contract is frozen in `API_BOUNDARIES.md` **O1-O5**: peer operations are logically request → response (`async` is I/O, not message shape — `CONCURRENCY_MODEL.md` already had peer calls *"per request… never fire-and-forget for state-changing calls"*), an operation's success result is separate from transport/parse/auth/protocol failures which keep their own error identities, and the operation carrying a **Reveal** returns exactly one **`bool`** game-legality result. Correlation is the awaited invocation, so no `TurnCursor` echo and no duplication; no free-text reason crosses the boundary; legality stays with `domain.rules`/`GameRulesPort`. | **RESOLVED-PROJECT** (PROJECT-CONTRACT; the source requires the rejection, not this shape) | App E #14; `API_BOUNDARIES.md` O1-O5; `CONCURRENCY_MODEL.md`; PRD02-FR-032/033/034/035; **C-12** |

**The preferred shape, evaluated and deliberately not frozen.** A single exact
`bool` — `True` = the locally validated revealed `PhysicalAction` is game-legal
and accepted for application at the currently expected turn, `False` = it is
game-illegal and rejected — is the minimal candidate and duplicates no `action`,
`hint`, `nonce`, `digest` or `state`. It is **not** adopted yet for one reason:
with an async port whose declared return is a generic *"protocol response"*, a
bare `bool` cannot preserve the four-way separation the same contract requires —
**delivery/parsing**, **authentication**, **protocol phase/cursor/order** and
**game legality** — and would collapse into exactly the conflated `accepted` flag
that the FastMCP example's signature-only `is_valid` shows is easy to reach for.
Freezing it before the Stage 2B-2C operation contract exists would decide the
separation by accident.

**What is already settled and is not blocked.** Legality itself is owned by
`domain.rules` via **`GameRulesPort`**, which *"never raises for legality —
returns a verdict"*; the rejection outcome is already owned by
**`E-PROTO-ILLEGAL-MOVE`** ("opponent sent an illegal move", protocol-visible,
evidence "received message + validator verdict"); and no reason text crosses the
boundary — rejection diagnostics stay local/log, never a Python exception string.
**No new port, semantic concept or error ID was created**, and this blocker is
**not** a peer-message-family blocker: the family inventory is settled at **8**.

**Why it was invisible until now.** The obligation was hidden behind the assumption
that a `FinalAudit` message would carry it. Once Stage 4E-R10-R1 established there is
no such family (**C-11**), the underlying source requirement became visible on its
own terms: the audit is only performable if the material actually reaches the peer.

**Candidate ownership to reconcile later** (audited, none frozen): the **producer**
(`infra.logger` / the finalized per-sub-game log material), **storage**
(`infra.artifacts` / ArtifactStore), **transport** (`PeerTransportPort` / a future
FastMCP submission operation) and the **consumer** (the audit verifier /
`infra.replay` verification path). The reference implementation's `submit_audit`
tool name remains a **REFERENCE-CONVENTION** and is deliberately **not**
project-locked here.

Every **other** interoperability dependency required for config agreement,
Commit-Reveal verification, replay verification, result agreement and mandatory
reporting remains SOURCE-LOCKED, PROJECT-LOCKED, or NEGOTIATED-PRE-MATCH with a
defined default, exchange, lock, detection (hash comparison), and failure behaviour.

## Genuinely still REVIEW-REQUIRED (non-blocking — no interop dependency)

- **Corrected (Stage 1D.1, K1):** keyed authentication with a pre-supplied key is
  **already SOURCE-REQUIRED** for Step-0 (Ch 5 p.55–56) and config (App B p.128) — it
  is **not** merely a possible future lecturer add-on, and Step-0 is **not** a bare
  SHA-256 digest. What remains REVIEW-REQUIRED is only the **exact primitive** the
  opponent/lecturer will use (HMAC-SHA256 vs an asymmetric signature) and the
  **key-provisioning channel**. Both are negotiated pre-match (NDEC-005/007) with a
  labelled HMAC-SHA256 default; if no mutually compatible mechanism/key is
  established, **counted play is refused** (so this is a *pre-match negotiation*, not
  a silent blocker). Nothing about the primitive choice restructures the contracts.
- The **key material itself** is provisioned out-of-band and never stored; its
  provenance is intentionally outside every artifact (JDEC-013 security block).
