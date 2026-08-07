# API / Port Boundaries — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — architecture-level ports only.**
**No Python signatures are fixed here.** Concrete FastMCP tool signatures are **not**
locked at this stage; they are negotiated/derived in Stage 2B–2C except where the
locked source already forces a field (e.g. `github_commit`, the four artifact names).

Ports are declared in `app.ports`; adapters live in `infra`/`protocol`; the
composition root wires them (`DEPENDENCY_RULES.md` D3/D4).

| Port | Caller | Implementation owner | Accepts | Returns | Failure contract | Sync/async | Determinism | Externally exposed |
|---|---|---|---|---|---|---|---|---|
| **GameRulesPort** | app (turn service, validator) | `domain.rules` | board state, proposed action, config | legal / illegal + reason | never raises for legality — returns a verdict | sync | **fully deterministic** | no |
| **ScoringPort** | app orchestrator | `domain.scoring` | outcome, config | per-role scores | pure | sync | **fully deterministic** | no |
| **StrategyPort** | app turn service | strategy plug-in | `Observation` (role-legal only) | `ProposedAction` (+ optional hint/intent, confidence) | must always yield a legal fallback; timeout ⇒ deterministic default | sync (bounded) | deterministic **given seed** | no |
| **BeliefPort** | app turn service | `domain.belief` | permitted observations | belief estimate | pure | sync | deterministic | no |
| **CommitmentPort** | app turn service | `protocol.commitment` | sealed record fields (8) | `H_commit`; later verify verdict | mismatch ⇒ `E-HASH-MISMATCH` (terminal) | sync | **deterministic** (canonical bytes) | hash only |
| **KeyedAuthPort** | config lock, declaration | `protocol.keyed_auth` | `context`, canonical core, `key_id` | auth tag / verify verdict | invalid ⇒ `E-AUTH-FAILURE`; **never returns key material** | sync | deterministic | tag only |
| **ConfigLockPort** | orchestrator | `protocol.config_lock` | proposed config | immutable locked config + `config_sha256` + tag | mismatch ⇒ refuse counted play | sync | deterministic | hash/tag |
| **PeerTransportPort** | app (via orchestrator) | `infra.mcp_client` + `infra.gatekeeper` | protocol message | peer response or typed transport error | retry/backoff per Gatekeeper; then `E-RETRY-EXHAUSTED` | **async** | **non-deterministic** (isolated) | yes (egress) |
| **PeerServerPort** | external peer | `infra.mcp_server` | inbound protocol message | protocol response | strict validation; reject malformed/stale | **async** | non-deterministic | **yes (ingress, untrusted)** |
| **ClockPort** | state machine, orchestrator, gatekeeper | `infra.clock` | — | monotonic now, deadlines, timers | timeout events | sync + callback | **injected** (fakeable in tests) | no |
| **LoggerPort** | all layers (via app) | `infra.logger` | structured evidence record | append confirmation | write failure ⇒ `E-LOCAL-DEFECT` (fail fast) | sync | append-only | no |
| **ArtifactStorePort** | orchestrator, reporter, replay | `infra.artifacts` | canonical artifact bytes | path + digest | I/O error | sync | canonical bytes | no |
| **ReplayPort** | audit / CI | `infra.replay` | artifact paths **only** | verification report | mismatch ⇒ `E-REPLAY-MISMATCH` | sync | **fully deterministic** | no |
| **ReportPort** | reporter | `infra.reporter` | finalized result artifact | delivery receipt | delivery failure retryable | async | — | yes (egress) |
| **TokenAccountingPort** | LLM adapter, reporter | `infra.metrics` | call cost/tokens | running totals | — | sync | monotonic counters | no |
| **GuiProjectionPort** | GUI | `infra.gui` consumer of app events | **projection events only** | — | render error is non-fatal | async (subscribe) | — | local UI only |
| **LlmAdvisorPort** | language/hint subsystem | `infra.llm` | bounded prompt context (no secrets, no forbidden truth) | suggested text/tag | failure ⇒ deterministic fallback | async (bounded) | **non-deterministic** (must not affect legality) | yes (egress, optional) |
| **SeriesLauncherPort** *(2A-R2)* | match operator | `app`/local launcher | series plan (sub-game index → role) | which independent role process to activate | refuses to launch if the role process is unavailable | sync | deterministic | no |
| **CompatibilityProfilePort** *(2A-R2)* | config lock, commitment, reporter | `protocol`/`infra` | negotiated profile ids (`AuthProfile`, `CommitmentCodec`, `ResultProfile`) | active profile set (read-only at match time) | unknown/weakening profile ⇒ refuse counted play | sync | deterministic | no |
| **SettingsPort** | infra composition root | `infra.settings` | — | local settings; secrets from env | missing secret ⇒ refuse start | sync | — | no |

## Port design rules

- **P1 — Observation is a wall.** `StrategyPort` accepts only an `Observation` built by
  `domain.observation`; there is no field on it that could carry opponent truth.
- **P2 — No port returns key material.** `KeyedAuthPort` returns tags/verdicts only.
- **P3 — Non-determinism is isolated.** Only `PeerTransportPort`, `PeerServerPort`,
  `ClockPort`, `ReportPort`, `LlmAdvisorPort` are non-deterministic; all are injected so
  tests can substitute deterministic fakes.
- **P4 — Ingress is untrusted.** `PeerServerPort` validates schema, ordering, identity,
  and freshness before anything reaches `app`.
- **P5 — Replay is offline-capable.** `ReplayPort` takes file paths and needs no network,
  no clock, and no live state.
- **P6 — Egress cannot mutate.** `ReportPort` has no write path back into domain/app.
- **P8 — Profiles are read-only at match time.** `CompatibilityProfilePort` is resolved
  during negotiation and frozen with the config lock; it can never be switched mid-series.
- **P9 — `KeyedAuthPort` is profile-driven.** It implements `AuthProfile ∈ {HMAC_SHA256
  (default), ED25519 (attachment-compatibility)}`. **Plain unkeyed SHA-256 is not a valid
  Step-0 producer-authentication profile.**
- **P7 — Ports are stable, adapters are not.** Swapping FastMCP transport or LLM provider
  must not change any port contract.
