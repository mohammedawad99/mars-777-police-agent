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
| `token_usage_locked` representation | Reported in result `tokens`/`total_tokens` (SOURCE E-54); Step-0 lock authenticated **within** the keyed Step-0 auth (NDEC-005) | **RESOLVED-NEGOTIATION** | PERF-001/002 |

## Blocking items

**One, opened at Stage 4E-R10-R1.**

| Item | Status | Class | Basis |
|---|---|---|---|
| **`AUDIT-EXCHANGE-PAYLOAD` — the interchange representation of the end-of-game audit material** | **Unresolved.** Ch 5 §5.4 requires each side to disclose its **full log including every nonce reveal** so the opponent can recompute independently, but no source fixes *how that material crosses the boundary*. Deliberately **not** decided here: not raw log-file bytes, not the whole local JSON log object, not a tuple of sealed records, not "only the missing `state`/`intent`/`nonce` values", not an artifact URL and not a filesystem path. | **BLOCKING** (artifact/transport interoperability) | Ch 5 §5.4; App E mutual-log-audit row; PRD06-FR-100/101; **C-11** |

Three things this blocker is **not**. It is **not a peer-message-family blocker**:
the exchange is an artifact/transport obligation and is **not** counted as an
`app.peer_messages` semantic family, so the family inventory is unaffected. It is
**not** satisfied by `FinalNonceReveal`, which carries the nonce batch only — see
the note below. And it does **not** re-open the sealed-record, canonicalization or
commitment contracts, which are frozen and implemented.

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
