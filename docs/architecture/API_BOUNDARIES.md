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
| **CommitmentPort** | app turn service | `protocol.commitment` | sealed record fields (8) — already-valid semantic values, never strings or dicts | `H_commit`; later a recompute **comparison result** | **port outcome** on a false comparison ⇒ `E-HASH-MISMATCH` (terminal). *Layer note (4E-R9-R1): this describes what the **consumer** sees. The underlying pure comparison primitive returns `False` and does **not** raise — a digest that differs is its correct successful result, not an error.* | sync | **deterministic** (canonical bytes) | hash only |
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
## Peer operation contract (Stage 4E-R11)

Two integration blockers — the move-rejection response and the audit-material
exchange — were both waiting on the same missing thing: a peer **operation**
contract. This section freezes that layer. It defines *logical operations and
their result/error separation*; it does **not** define FastMCP decorators,
signatures or JSON schema, which stay deferred to Stage 2B-2C.

**O1 — Peer operations are logically request → response.** `async` is an I/O
implementation property, **not** a message-shape property, and the two were being
conflated. `CONCURRENCY_MODEL.md` already settles it: outgoing peer calls are
*"**per request**, `async`, bounded … **never fire-and-forget for state-changing
calls**"*, inbound *"**requests** do not mutate directly"*, and *"two concurrent
peer **requests** must never mutate the same turn state"*. So: **each peer
operation is one request whose caller awaits exactly one operation-specific
result, or a typed transport/protocol failure.** No independent asynchronous
response message exists merely because the implementation is `async`, and an
operation result is **never** a peer-message semantic family. **PROJECT-CONTRACT**,
consistent with the committed concurrency model; the book specifies no transport.

**O2 — An operation's success result is not a failure channel.** A successful
operation-specific result is semantically distinct from transport failure,
parse/schema failure, authentication failure and protocol phase/order/cursor
failure. Each failure is raised by the layer that owns it and keeps its existing
error identity — `E-TRANSPORT`, `E-PROTO-MALFORMED`, `E-AUTH-FAILURE`,
`E-PROTO-STALE` — reinforced by the Gatekeeper rule that retries cover
*"transport-class errors only; never integrity errors"*. **No generic `accepted`
flag spanning layers may be introduced**, and a lower-layer failure must never be
encoded as a semantic `False` (nor semantic rejection as a transport failure).

**O3 — Logical operations, with the reference names as compatibility aliases.**
`PRD02-FR-033` already enumerates the semantic operations the runtime needs;
`PRD02-FR-034` marks the four reference tool names **REFERENCE-COMPATIBILITY
DEFAULT — NOT BOOK-MANDATED**. R11 keeps exactly that split and adds only the
routing:

| Logical operation (PRD02-FR-033) | Carries | Compatibility alias (PRD02-FR-034) |
|---|---|---|
| (a) Step-0 declaration + auth envelope | Step-0 family *(payload blocked)* | `negotiate` |
| (b) exchange / lock config | Config negotiation, Config lock *(payloads blocked)* | `negotiate` |
| (c)(d)(e) commitment · acknowledgement · reveal | `Commitment`, `Acknowledgement`, `Reveal` | `receive_turn` |
| (f) exchange final-audit material | `FinalNonceReveal`, then the audit material *(representation blocked)* | `submit_audit` |
| (g) exchange result approval | `ResultAgreement` *(payload frozen 4E-R13/R13-R1; carries the sender's `ResultContribution`, returns the receiver's `Sha256Digest`)* | `receive_control` |
| (h) optional control / heartbeat | — | `receive_control` |

The **internal** semantic architecture depends on the logical operation identity,
never on a tool-name string. Routing a family to an operation does **not** define
that family's payload, and the four blocked families stay blocked. **No fifth
validation operation exists** — the move-rejection outcome is a *result* of
(c)(d)(e), not an operation of its own.

**O4 — Stable ingress, local role routing.** One stable group-level ingress
endpoint per team for the series (declaration rule, NET-001), carrying no secret.
Behind it, `SeriesLauncher` may dispatch to the role-specific local backend for
the current sub-game. `SeriesLauncher` remains **operational routing only** —
never a referee, never shared truth, never shared game state (PRD02-FR-010,
PRD02-AC-018). **No separate public Police/Thief URLs** for alternating roles, and
the declaration is never silently mutated when the local role backend changes.

**O5 — Game-legality result of the turn operation** *(closes
`MOVE-REJECTION-TRANSPORT-SHAPE`)*. The operation carrying a **Reveal** returns
exactly one **`bool`** game-legality result:

- `True` — the already-authenticated, protocol-valid revealed `PhysicalAction`
  was locally validated as **game-legal** for the currently expected turn and
  accepted for the local application path.
- `False` — the same, validated as **game-illegal** and rejected (App E #14).

It **never** means network delivered, JSON parsed, signature valid, sender valid,
phase valid, cursor valid, commitment valid or reveal-hash valid — those failures
are raised by O2's owning layers and **never reach this result**. Exactly one
result per invocation that reaches the legality layer; if authentication or
protocol validation fails first, **no game-legality result exists at all**.
Correlation is the awaited invocation itself, so **no `TurnCursor` echo** and no
duplication of `action`, `hint`, `nonce`, `digest` or `state`. **No free-text
reason crosses the boundary** — `GameRulesPort`'s reason stays a local diagnostic
and log evidence, and no Python exception string is ever transported. Legality is
decided only by `domain.rules` / `LocalTurnService` via `GameRulesPort`;
`PeerServerPort` exposes the already-computed outcome and `PeerTransportPort`
returns it to the caller. `False` is a result, not a sanction: interpretation
belongs to the protocol runtime and `E-PROTO-ILLEGAL-MOVE`. This is
**PROJECT-CONTRACT** (C-12); the source requires the rejection, not this shape.

**O6 — Audit-material submission operation.** Operation (f), alias `submit_audit`
— **PROJECT-CONTRACT / REFERENCE-COMPATIBILITY, not book-mandated**. Cadence is
**one submission per completed sub-game**, following the existing per-sub-game log
artifact ownership (`log_<game_id>_g<NN>.json`); whole-series batching is *not*
assumed. Producer `infra.logger` (finalized material), storage `infra.artifacts`,
transport `PeerTransportPort`/`PeerServerPort`, consumer the replay/audit
verifier which persists what it receives. **No `FinalAuditVerdict`, expected
digest, recomputed digest or TAMPERED reason is transmitted, and no audit
verdict ACK is invented** — successful submission is represented by ordinary
operation completion, failure by the owning typed failure, so the operation needs
**no additional semantic result**. **No second audit schema** (`AuditEntry`,
`AuditBundle`, `AuditEvidenceMessage`) is created. **The payload representation was
frozen at Stage 4E-R11-R1**: the operation carries the exact **JSON-native
audit-disclosure document** — dict/list/str/int/bool material as `LOG_CONTRACT.md`
freezes it — and **never** a filesystem path, artifact URL, base64, pickle, raw
bytes or Python object. Whole-log byte identity between peers is **not** required
(semantic equality of the disclosure core is), and no log-level hash exists. The
verdict and the other locally-derived annotations are **not** transmitted; the
receiver recomputes them. Both former integration blockers are now resolved in
`INTEROPERABILITY_BLOCKERS.md`.

**O7 — Binding boundary.** An operation contract is not a FastMCP binding. R11
defines logical operations and their semantic request/result contracts; a later
implementation stage maps them to FastMCP tools. No decorator, signature or JSON
schema is defined here, and `PRD02-FR-035` still governs concrete signatures.

- **P2b — Four acceptances stay distinct** *(Stage 4E-R10-R3, C-12)*. A received turn passes
  through **delivery/parsing** (`PeerServerPort`), **authentication** (`KeyedAuthPort` where
  applicable), **protocol phase/cursor/order** (`app.state_machine`) and finally **game legality**
  (`GameRulesPort` → `domain.rules`). Appendix E #14's "rejection of a move by the opponent"
  concerns **only the last**, and its peer-facing outcome is a transport/port **response**, not a
  peer-message family. These must never collapse into one `accepted` flag — the reference FastMCP
  `receive_move` returns `{"accepted": is_valid, …}` where `is_valid = verify_signature(...)`,
  which is the *authentication* acceptance and is **not** a legality verdict. The exact response
  shape is deferred with every other concrete signature to Stage 2B-2C and is tracked as
  `MOVE-REJECTION-TRANSPORT-SHAPE` in `INTEROPERABILITY_BLOCKERS.md`. Transport never re-derives
  legality, applies a move, mutates `LocalTruth`, computes scoring or chooses technical loss.
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

## Signature-freeze policy (Stage 4D-R1)

This table is **architecture-level**: it fixes each port's caller, owner, semantic
operands, failure contract, sync/async mode and trust class. It fixes **no Python
signature**, and no other frozen document supplies one — a repository-wide search of
`docs/architecture/` and `docs/prd/` finds no `def`, no `Protocol` and no return
annotation. That is a deliberate deferral, not an omission.

Consequences, recorded so no later stage mistakes one for the other:

- **Any Python method name, parameter list or return type chosen later is a
  PROJECT-CONTRACT**, decided by this project — never `SOURCE-MANDATED`,
  `LECTURER-EXACT` or `REFERENCE-EXACT`. It must be recorded as such when frozen.
- The reference-compatible FastMCP tool names `negotiate`, `receive_turn`,
  `submit_audit`, `receive_control` are **LECTURER_REFERENCE_COMPATIBILITY** only
  (PRD02-FR-034 labels them a MAY). They are adapter-surface names and must never
  become `app.ports` method names.
- A port row is **not** an instruction to create a Python `Protocol` immediately. A
  row whose implementation owner is a pure, deterministic, in-process `domain`
  service that `app` may already call directly (`ScoringPort`, `GameRulesPort`,
  `BeliefPort`) documents the call boundary; wrapping it in a Protocol adds
  indirection without substitutability. Injection is required for the
  non-deterministic ports named in **P3**.
- **20 ports** are frozen here: the original 18 plus `SeriesLauncherPort` and
  `CompatibilityProfilePort`, both added at Stage 2A-R2.

**O-note (Stage 4E-R12) — profile provisioning is not an operation.** No `O8` is
created and **O1-O7 are unchanged**. Two clarifications to the existing text:
`CompatibilityProfilePort` is listed above as accepting "negotiated profile ids
(`AuthProfile`, `CommitmentCodec`, `ResultProfile`)" — for `AuthProfile` and its
`KeyId` this is now read as **provisioned out of band before `BOOT`**, not
negotiated in band, because verifying the Step-0 `AuthProof` in
`STEP0_NEGOTIATION` cannot depend on a profile chosen by an unauthenticated
message (`SIGNATURE_AND_HASH_PROVENANCE.md` R12-A). The port's read-only-at-match-
time contract and its "unknown/weakening profile ⇒ refuse counted play" failure
contract are unchanged, and `KeyedAuthPort` still **never returns key material**
(**P2**). Operations **(a)** and **(b)** in O3 keep the `negotiate` compatibility
alias; R12 freezes what those operations *carry* — the Step-0 authenticated core
and envelope for (a), a complete `NegotiatedConfig` core plus the echo set and
then the four config-lock layers for (b) — without defining any FastMCP
signature, which stays deferred to Stage 2B-2C (**PRD02-FR-035**).

**O-note (Stage 4E-R13-R2) — the result-agreement operation.** **O1-O7 are
unchanged and no `O8` is created.** Operation **(g)** is one request → one awaited
response, exactly as O1 requires: the request is the **`ResultAgreement` semantic
value** (`game_id`, `game_uid`, `declaration_ref`, `timestamp`, `contribution`),
and the operation-specific successful response is a single **`Sha256Digest`** —
the receiver's locally computed `result_sha256`. Per **O1** an operation result is
never a peer-message semantic family, so the digest response is **not** a family
and **no ninth family exists**; per **O2** it is not a failure channel, and
transport, parse, authentication and protocol failures keep their own identities
(`E-TRANSPORT`, `E-PROTO-MALFORMED`, `E-AUTH-FAILURE`, `E-PROTO-STALE`) and never
reach it. The **deterministic proposer/non-proposer ordering** of the two calls is
**application-protocol semantics recorded in `RESULT_CONTRACT.md` §R13-R2** — it is
not transport magic, not a retry policy and not a race resolution; the transport
layer is unaware of it and merely delivers each request.
