# Security Architecture — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — threat model and design only.**
**No secret value, key, credential, or endpoint token appears in this document or in
any repository artifact.**

## 1. Security posture

The opponent peer is **untrusted by design** (honest-but-verified at best, hostile at
worst). The architecture assumes every inbound byte may be malformed, replayed,
forged, or adversarially timed. Safety comes from **deterministic verification**, not
from trust — and the correct response to a failed verification is to **refuse counted
play**, not to degrade.

Trust boundaries: **TB-1** peer · **TB-2** process · **TB-3** repository ·
**TB-4** LLM advisor · **TB-5** evidence · **TB-6** secret (`SYSTEM_ARCHITECTURE.md` §3).

## 2. Threat table

| # | Threat | Boundary | Prevention | Detection | Failure mode | Evidence |
|---|---|---|---|---|---|---|
| T1 | **Malicious opponent input** (illegal move/barrier, contradictory claim) | TB-1 | deterministic validator before any effect; strict schema | validator verdict | reject; possible technical loss per spec | received message + verdict |
| T2 | **Malformed MCP request** (bad types, extra/missing keys, oversized, deeply nested) | TB-1 | strict schema validation, size/depth caps, no dynamic eval | parse/validate failure | `E-PROTO-MALFORMED`, reject | truncated escaped payload |
| T3 | **Replayed request** (old commit/reveal re-sent) | TB-1 | turn-cursor guard `(sub_game, step)` + receiver-side phase admissibility; idempotency | cursor mismatch | `E-PROTO-STALE`, ignore | rejected id + cursor |
| T4 | **Nonce attack** (guessing, reuse, forced early disclosure) | TB-1/TB-6 | CSPRNG (`secrets`) fresh per commit; single custodian; release only at final audit | nonce/commit recompute | `E-NONCE-MISMATCH` ⇒ TAMPERED | commitment/reveal pair |
| T5 | **Config substitution** (peer plays a different config) | TB-1 | byte-identical canonical config; `config_sha256` equality **plus** keyed auth tag | hash or tag mismatch | `E-CONFIG-MISMATCH`/`E-AUTH-FAILURE` ⇒ **refuse counted play** | both digests, `key_id` |
| T6 | **Authentication failure / forged Step-0** | TB-1/TB-6 | keyed authentication with pre-supplied key; domain separation `step0`/`config`; non-self-referential tags | tag verify fails | refuse counted play | `key_id`, alg, verdict (**never key bytes**) |
| T7 | **Hash mismatch / log tampering** | TB-5 | canonical bytes; append-only log; commit-reveal | recompute at audit + independent replay | **TAMPERED — void, no appeal** (PDF p.75; REPLAY-002) | full audit bundle |
| T8 | **Resource exhaustion / DoS** (flood, huge payloads, slowloris) | TB-1 | token bucket, concurrency cap, bounded queue, size/time limits, backpressure | queue/limiter metrics, 429 counts | reject with backpressure; never unbounded growth | limiter counters |
| T9 | **Secret leakage** (key, credential, API key) | TB-6 | secrets only in environment; never persisted/logged/e-mailed; only `key_id` serialized | repository + artifact secret scans in CI | refuse to start if misconfigured | scan result (no values) |
| T10 | **Private-state leakage** (opponent truth or nonce reaching strategy/GUI/log/report) | TB-1/TB-5 | forbidden data never received; `Observation` wall; projection-only GUI; logger whitelist | leak-scan tests asserting absent keys | test failure blocks the gate | leak-test report |
| T11 | **Report tampering / one-sided reporting** | TB-5 | `result_sha256` over agreed core (stored outside it); dual matching reports required | digest comparison | **0 to both** (C-09, E-35, INV-11) | both result cores |
| T12 | **Prompt injection via peer text into the LLM** | TB-4 | peer text is data, never instruction; bounded sanitized context; output is advisory only and must pass the validator | validator rejection; anomaly metrics | fallback to deterministic path | sanitized advisor record |
| T13 | **Cross-repository contamination** (police↔thief) | TB-3 | separate processes, packages, venvs, repos; no cross-import; no shared runtime state | import/dependency tests; isolation audit | build/test failure | isolation audit output |
| T14 | **Supply-chain / dependency risk** | local | minimal pinned dependencies (`uv.lock`, `--frozen`); justify every addition | lockfile diff review | dependency change is reviewed | lock diff |
| T15 | **Endpoint exposure** (public tunnel abuse) | TB-1 | endpoint carries no secret; assume observable; all authority comes from keyed auth + hashes, not from URL secrecy | inbound reject metrics | rate-limit / reject | ingress metrics |

## 3. Cryptographic discipline (locked taxonomy — never conflated)

| Object | Exactly what it is |
|---|---|
| `H_commit` | **Unkeyed SHA-256 commitment** over the canonical sealed record |
| Step-0 authentication | **Source-required keyed authentication** with a pre-supplied key. `AuthProfile ∈ {HMAC_SHA256 (project default), ED25519 (attachment-example compatibility — AE-02, *not* SOURCE-MANDATORY)}`. **Plain unkeyed SHA-256 does NOT satisfy strict Step-0 producer authentication** |
| HMAC-SHA256 | **Project default / negotiated** primitive — **not lecturer-specified** |
| `config_sha256` | **Unkeyed** equality/integrity digest |
| Config authentication | **Distinct** auth/signature exchange, separate from `config_sha256`. Byte-identity + exchange semantic **SOURCE-REQUIRED**; **exact primitive SOURCE-UNSPECIFIED** — Step-0's explicit "pre-supplied key" wording is *not* transferred onto the looser config wording |
| `result_sha256` | **Result-content agreement digest** (mutual acknowledgement) |
| Git commit SHA | **Source-code identity**, not message authentication |

Rules: a bare hash never authenticates a producer; HMAC is never called an asymmetric
signature; SHA-256 is never called a signature; tags and digests are **never
self-referential**; `context ∈ {"step0","config"}` provides domain separation so a tag
cannot be replayed across object types.

## 4. Secure defaults

- **Fail closed**: integrity/auth failure ⇒ refuse counted play.
- **Least data**: never request what we are not permitted to know.
- **No secret in Git, JSON, logs, docs, e-mail, errors, or runtime evidence.**
- **Constant-time comparison** for digests/tags where the language provides it.
- **Bounded everything**: payload size, queue depth, retries, decision time, log size.
- **Deterministic verification** over trust, always.

## Stage 5-R8 — what protects the two facts SHA-256 cannot

The commit-reveal scheme protects everything inside `H_commit`. Two facts of a
real game sit outside it and needed their own protection.

**A capture claim and its answer are unsealed.** They are live interaction
facts: the claim is a question about a cell only the opponent knows, and the
answer is computed by the opponent from state nobody else can see. Neither can
be committed to in advance. The protection is **mutual retention**: both sides
keep the row they really saw, each discloses its own half at the final audit,
and each compares the other's half against its own. A peer that rewrites,
adds, drops, duplicates or reorders a row is refused before any verdict is
derived — not because the row is signed, but because two independent records of
the same event exist and must agree.

**A disclosed log can be internally consistent and still be fiction.** A peer
can seal a game it never played: a piece that teleports, a move through a
barrier, a snapshot listing a barrier nobody placed. Every one of those hashes
correctly. The protection is the **semantic replay**, which rebuilds the
sub-game from the config-locked start cells and the placements both sides
actually revealed, and judges each action with the same `domain.rules` /
`domain.barriers` code the mover was required to obey locally.

Neither mechanism transmits a position, a nonce or a verdict, and neither adds a
message, a tool, a port or an error identity. The one asymmetry worth stating
plainly: a false capture **declaration** is a legal move played badly and is
scored (technical loss, 0/0), while a false **answer** is a forgery and is
treated exactly as a failed digest is.
