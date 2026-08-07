# Error Model — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

**Sanction rule.** Only sanctions present in the **locked** Stage-1 specification are
used (Appendix E, Ch 3, C-07, C-09). No sanction is invented here. Where the spec is
silent about a score consequence, the column reads *none (spec silent)*.

## Taxonomy

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
| `E-AUTH-FAILURE` | Keyed-auth tag invalid / unknown `key_id` / no compatible mechanism | no | yes | yes | **refuse counted play** (INV-14/15) | yes | possibly | **critical** | `key_id`, alg, verdict — **never key bytes** |
| `E-HASH-MISMATCH` | `H_commit` recompute mismatch | no | yes | yes | **TAMPERED ⇒ match void, no appeal** (PDF p.75, REPLAY-002) | yes | yes | **critical** | sealed record + expected/actual digest |
| `E-NONCE-MISMATCH` | Revealed nonce inconsistent with commitment | no | yes | yes | TAMPERED | yes | yes | **critical** | commitment + reveal pair |
| `E-REPLAY-MISMATCH` | Independent replay disagrees with the log | no | no (post-hoc) | yes | TAMPERED | — | yes | **critical** | replay report |
| `E-TAMPERED` | Terminal integrity verdict | no | yes | yes | **game void; no appeal** (PDF p.75, REPLAY-002) | yes | yes | **critical** | full audit bundle |
| `E-TECHNICAL-LOSS` | Technical-loss condition per spec | no | yes | yes | **0 / 0** (C-07; Ch 3 + E-48, not an App F row) | yes | no | medium | condition + timestamps |
| `E-REPORT-DELIVERY` | Gmail/report delivery failure | **yes** | no | yes | none if eventually delivered; if a required report is missing ⇒ **0 to both** (C-09) | no | no | medium | send attempts (no credentials) |
| `E-REPORT-DISAGREE` | `result_sha256` differs / contradictory reports | no | yes | yes | **0 to both** (E-35, C-09, INV-11) | — | yes | high | both result cores |
| `E-LLM-UNAVAILABLE` | Advisor failure/timeout/over-budget | yes then fallback | no | yes | none — deterministic fallback | no | no | low | fallback-used metric |
| `E-LOCAL-DEFECT` | Programming defect / invariant violation | no | no | yes | none (fail fast) | yes | possibly | high | stack context (no secrets) |

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
