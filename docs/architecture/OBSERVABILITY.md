# Observability and Metrics — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only. No metrics implemented.**

Owner: `infra.metrics` (+ `infra.logger` for evidence). Metrics are **read-only with
respect to the game**: no metric may influence a decision, a score, or a transition.

## 1. Protocol metrics

| Metric | Type | Purpose | Threshold signal |
|---|---|---|---|
| peer request latency (p50/p95/max) | histogram | detect slow peer / tunnel | approaching response timeout (30s) |
| retry count (per call, per sub-game) | counter | transport instability | nearing `max_retries` (3 MIN) |
| timeout count (step / watchdog) | counter | deadline pressure | any watchdog hit is notable |
| HTTP 429 count | counter | rate-limit health | >0 ⇒ tune token bucket |
| queue depth (current/max) | gauge | backpressure | approaching bound (100 MIN) |
| token-bucket level | gauge | send pacing | sustained 0 ⇒ throttled |
| inbound rejects by reason | counter by `E-*` | hostile/buggy peer detection | spike ⇒ investigate |

## 2. Game metrics

| Metric | Type | Purpose |
|---|---|---|
| outcome per sub-game (capture / survival / tie / technical_loss) | counter | series tracking |
| moves used vs `max_moves` | gauge | pacing |
| barriers used vs quota | gauge | police resource use |
| hint usage / length distribution | histogram | language behaviour within `hint_max_words` |
| scent observations per sub-game | counter | sensing activity |
| capture step (when captured) | value | efficiency |
| survival steps reached | value | thief efficiency |

## 3. Strategy metrics

| Metric | Type | Purpose |
|---|---|---|
| decision latency (p50/p95) | histogram | ensure inside step budget |
| fallback usage rate | counter | how often the deterministic default fired |
| proposal rejection rate (by validator) | counter | strategy legality quality |
| action confidence distribution | histogram | calibration |
| belief quality **where measurable** | value | only measurable **post-hoc**, after legitimate disclosure (final audit/replay) — never live |

**Note.** Belief quality must never be computed live, because that would require
opponent truth. It is a replay-time analysis over already-disclosed data.

## 4. LLM metrics

| Metric | Type | Purpose |
|---|---|---|
| tokens (prompt/completion, per call, per sub-game, series total) | counter | PERF-001/002, E-54 reporting |
| estimated cost | counter | budget control |
| call count | counter | usage profile |
| latency | histogram | budget adherence |
| failures / timeouts / budget-exhausted | counter | fallback health |
| tier in use (T0/T1/T2) | gauge | proves zero-token viability |

## 5. Security metrics

| Metric | Type | Purpose |
|---|---|---|
| keyed-auth failures (by `key_id`, never key bytes) | counter | attack/misconfig detection |
| hash mismatch count (`H_commit`, `config_sha256`, `result_sha256`) | counter | integrity |
| replay verification result | status | TAMPERED detection |
| nonce-mismatch events | counter | commit-reveal integrity |
| stale/duplicate message rejects | counter | replay-attack signal |
| malformed-input rejects | counter | fuzzing/hostility signal |

## 6. Logging rules

- **Structured, append-only, canonical** records; one schema per event type.
- **Never logged:** key material, credentials, API keys, nonce before final audit,
  opponent forbidden truth, full LLM prompts/responses containing any of the above.
- Malformed peer input is logged **truncated and escaped**, bounded in size.
- Log level affects verbosity only — never game behaviour.
- Every `E-*` from `ERROR_MODEL.md` maps to exactly one log event type carrying the
  evidence that error requires.
- Metrics are exported locally (and to the GUI projection); nothing is sent to a third
  party.
