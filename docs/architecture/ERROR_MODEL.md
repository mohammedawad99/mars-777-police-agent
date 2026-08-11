# Error Model — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

**Sanction rule.** Only sanctions present in the **locked** Stage-1 specification are
used (Appendix E, Ch 3, C-07, C-09). No sanction is invented here. Where the spec is
silent about a score consequence, the column reads *none (spec silent)*.

## Taxonomy

**Registered error identities: 22.** The table below **is** the register — this
document is the canonical enumeration, and no other file owns a competing list.
An earlier bookkeeping count of "20" was carried in tracking prose without ever
being backed by an enumeration; it matched no subset of this table and is
withdrawn as stale.

**Membership is not a property claim.** Being registered here says only that the
identity exists in the project's error model. Whether an identity is
peer-visible, crosses `ToolError`, is retryable, is implemented yet, or is
source-mandated are **independent** columns and facts - a local or offline-only
identity is still a registered identity. The register is therefore deliberately
*not* "the peer-visible identities".

**Not members.** The public-readiness reason codes `E-NET-NOT-PUBLIC`,
`E-NET-STALE-ENDPOINT` and `E-NET-CONVENTION-UNSET` (`PRD05-FR-004`/`013`/`032`)
are **local** verdicts of the readiness gate. They are not `PeerProtocolError`
subclasses, never cross `ToolError`, and are not listed below.

| Code | Category | Retryable | Protocol-visible | Logged | Score consequence | Abort sub-game | Abort series | Security severity | Evidence required |
|---|---|---|---|---|---|---|---|---|---|
| `E-LOCAL-VALIDATION` | Local validation error (our own proposal illegal) | no (re-decide) | no | yes | none — caught before send | no | no | low | rejected-proposal record |
| `E-PROTO-ILLEGAL-MOVE` | Opponent sent an illegal move | no | yes (reject) | yes | per spec: illegal action is not applied; may lead to technical loss | possibly | no | medium | received message + validator verdict |
| `E-PROTO-BARRIER` | Invalid/undeclared barrier | no | yes | yes | audit-loss risk for the declaring side (BAR-001/002) | possibly | no | high | placement record |
| `E-PROTO-MALFORMED` | Malformed / schema-invalid JSON | no | yes (reject) | yes | none directly | no | no | medium | raw message (bounded) + reason |
| `E-PROTO-STALE` | Duplicate / stale / out-of-order message | no (ignore) | yes (reject) | yes | none | no | no | medium | step cursor + rejected id |
| `E-TRANSPORT` | Connection/DNS/tunnel/5xx error | **yes** (Gatekeeper) | yes | yes | none until exhaustion | no | no | low | attempt counters |
| `E-TIMEOUT-STEP` | Step deadline exceeded | limited | yes | yes | per spec deadline handling | possibly | no | medium | deadline record |
| `E-TIMEOUT-WATCHDOG` | Watchdog threshold exceeded | no | yes | yes | escalates toward technical loss | yes | no | medium | watchdog record |
| `E-RETRY-EXHAUSTED` | Retry budget exhausted | no | yes | yes | escalates per spec | yes | no | medium | full attempt history |
| `E-RATE-429` | Rate-limit rejection (ours or remote) | **yes** (backoff) | yes | yes | none if respected | no | no | medium (abuse risk) | limiter + backoff record |
| `E-CONFIG-MISMATCH` | `config_sha256` inequality / value outside Appendix F status | no | yes | yes | **refuse counted play** (GAME-001/002) | yes (never starts) | no | high | both hashes + diff summary |
| `E-NET-CONVENTION-MISMATCH` | Each peer echoing a **different** series convention (`PRD05-FR-033`) | no | yes | yes | **refuse counted play**; never resolved by preferring either side | yes (never starts) | no | high | both echoed convention values |
| `E-AUTH-FAILURE` | Keyed-auth tag invalid / unknown `key_id` / no compatible mechanism | no | yes | yes | **refuse counted play** (INV-14/15) | yes | possibly | **critical** | `key_id`, alg, verdict — **never key bytes** |
| `E-HASH-MISMATCH` | `H_commit` recompute mismatch | no | yes | yes | **TAMPERED ⇒ match void, no appeal** (PDF p.75, REPLAY-002) | yes | yes | **critical** | sealed record + expected/actual digest |
| `E-NONCE-MISMATCH` | Revealed nonce inconsistent with commitment | no | yes | yes | TAMPERED | yes | yes | **critical** | commitment + reveal pair |
| `E-REPLAY-MISMATCH` | Independent replay disagrees with the log | no | no (post-hoc) | yes | TAMPERED | — | yes | **critical** | replay report |
| `E-TAMPERED` | Terminal integrity verdict | no | yes | yes | **game void; no appeal** (PDF p.75, REPLAY-002) | yes | yes | **critical** | full audit bundle |
| `E-TECHNICAL-LOSS` | Technical-loss condition per spec | no | yes | yes | **0 / 0** (C-07; Ch 3 + E-48, not an App F row) | yes | no | medium | condition + timestamps |
| `E-REPORT-DELIVERY` | Gmail/report delivery failure | **yes** | no | yes | none if eventually delivered; if a required report is missing ⇒ **0 to both** (C-09) | no | no | medium | send attempts (no credentials) |
| `E-REPORT-DISAGREE` | `result_sha256` differs / contradictory reports | no | yes | yes | **0 to both** (E-35, C-09, INV-11) | — | yes | high | both result cores |
| `E-LLM-UNAVAILABLE` | Advisor failure/timeout/over-budget | yes then fallback | no | yes | none — deterministic fallback | no | no | low | fallback-used metric |
| `E-LOCAL-DEFECT` | Programming defect / invariant violation | no | **yes** (the outer wire boundary maps any unknown server failure to this identity, and the caller reconstructs it) | yes | none (fail fast) | yes | possibly | high | stack context (no secrets) |

## Layer ownership of `E-HASH-MISMATCH` (Stage 4E-R9-R1)

`E-HASH-MISMATCH` is unchanged — same code, same category, same terminal TAMPERED
consequence. What Stage 4E-R9-R1 fixes is *who raises it*, because the commitment path
spans three layers and an audit sanction must not end up inside a hash function:

| Layer | Owner | On a digest that differs |
|---|---|---|
| Pure codec / recompute | `protocol.canonical`, `protocol.commitment` | returns **comparison material** (a plain `bool`) — **no exception**; a `False` is a correct, successful result |
| Audit / consumer | the audit consumer over the persisted log (Ch 7 §7.5 Replay Viewer path) | interprets `False` as an integrity failure ⇒ **`E-HASH-MISMATCH`** and/or `FinalAuditVerdict.TAMPERED` |
| Protocol / sanction | protocol + scoring | applies match-void / no-appeal per the locked spec |

`API_BOUNDARIES.md`'s `CommitmentPort` "mismatch ⇒ `E-HASH-MISMATCH` (terminal)" is the
**port outcome** of the middle layer, not a claim about the raw comparison primitive.
`E-NONCE-MISMATCH` and `E-REPLAY-MISMATCH` follow the same split. **No error ID is
added, removed, renamed or re-classified by this clarification.**

## Handling principles

1. **Fail closed on integrity.** Any `E-AUTH-*`, `E-HASH-*`, `E-NONCE-*`, `E-REPLAY-*`
   stops counted play immediately; never "continue and hope".
2. **Retry only transport-class errors.** Integrity and legality errors are never retried.
3. **Refuse rather than degrade.** If the pre-match gates (auth, config) fail, the
   architecture refuses a counted match instead of playing under an unverified contract.
4. **Errors are evidence.** Every error above produces a log record adequate for replay
   and for the final report.
5. **No secret in any error.** Error payloads carry `key_id`/algorithm/verdict, never key
   bytes, credentials, or tokens (SEC-003/004).
6. **Bounded raw capture.** Malformed input is logged truncated and escaped, never
   executed or echoed verbatim to the peer.
7. **Distinguish ours vs theirs.** Local defects (`E-LOCAL-*`) never become protocol
   accusations; opponent faults are recorded with the received evidence.
