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
| **NonceSourcePort** *(5-R4P)* | app (outbound evidence runtime) | `protocol.secure_nonce` | — | a fresh `NonceValue` | a source that yields a value outside the frozen profile fails value construction; there is no fallback and no retry | sync | **non-deterministic by requirement** (CSPRNG, CRYPTO-010) | no — the nonce stays secret until `FinalNonceReveal` |
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

**O5 — Turn outcome of the operation carrying a Reveal** *(amended at Stage
5-R8; supersedes the legality-`bool` form of C-12, see **C-13**)*. The operation
carrying a **Reveal** returns exactly one **`TurnOutcome`**:

- **`accepted: bool`** — whether the reveal is acceptable on the facts the
  receiver can actually check: a well-formed action from a role permitted to
  take it, and for a `BarrierAction` a target that is on the board and not
  already blocked. It is **not** remote spatial legality. The mover's
  pre-action cell is sealed until the final audit, so bounds, blocked
  destinations and the resulting cell are **not knowable live** and are never
  asserted here.
- **`capture: CaptureAnswer`** — `NO_QUESTION`, `NOT_CAUGHT` or `CAUGHT`,
  computed by the receiver from its **own** `LocalTruth` and public facts. Same
  cell answers a `capture_claim`; a barrier answers by its own public target and
  by the trapped rule. No position is ever returned.

**Local legality is unchanged and still mandatory**: the sender validates its
own action in full through `domain.rules` / `LocalTurnService` **before**
committing, so an illegal action never produces an `H_commit` and never leaves.

**Hidden-state-dependent legality is a final-audit responsibility.** From the
disclosed sealed record the verifier reconstructs the mover's pre-action cell
and proves or disproves the action and any capture declaration. *(Implemented
at the Stage 5-R8 semantic-audit checkpoint: `app.semantic_review` replays the
sub-game from the two disclosed logs — see **C-13** and **JDEC-016**.)*

It never means network delivered, JSON parsed, signature valid, sender valid,
phase valid, cursor valid, commitment valid or reveal-hash valid — those
failures are raised by O2's owning layers and **never reach this result**.
Exactly one result per invocation that reaches this layer. Correlation is the
awaited invocation itself, so **no `TurnCursor` echo** and no duplication of
`action`, `hint`, `nonce`, `digest` or `state`. **No free text crosses the
boundary.** This is **PROJECT-CONTRACT** (C-12 as amended by C-13); the source
requires the capture resolution and the rejection, not this exact shape.

**O6 payload gained one member at Stage 5-R8**: the audit-disclosure document
carries `capture[]` — `{step, claim, answer}` rows for the reveals this side
made — beside `entries[]`. Still one schema, one operation, no new tool: the
transcript is part of the same document the peer already parses, and the
receiver refuses a document that omits it (`LOG_CONTRACT.md`).

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
- **`StrategyPort` is wired into production at Stage 6C-B.** `AgentComposition`
  carries one, typed as the port, and `compose_agent` constructs the repository's
  `BaselineStrategy` directly - no dotted-path loader, because App F Table 22 is
  *"a reference table only"* and there is one strategy to choose between. The
  register is **still 21**: the row was already there.
- **`StrategyPort` gained a Python `Protocol` at Stage 6B** (`app.strategy_api`),
  and the register is **still 21** — an existing row acquiring a callable form is
  not a new port identity. It is also the one row this section's rule *positively*
  justifies wrapping: a `Protocol` earns its indirection when implementations are
  genuinely interchangeable, which is exactly what a baseline that must later be
  replaced by a competitive policy means. `BeliefPort`, `ScoringPort` and
  `GameRulesPort` remain correctly unwrapped. The Stage-6B signature is
  `choose_action(observation: Observation) -> PhysicalAction`; the row's
  `ProposedAction` (with hint/intent/confidence) is **reserved for PRD-04**,
  which owns the language half of a turn.
- **21 ports** are registered here: the original 18, plus `SeriesLauncherPort`
  and `CompatibilityProfilePort` at Stage 2A-R2, plus `NonceSourcePort` at Stage
  5-R4P. The last is an authorized architecture evolution rather than a new
  source requirement: `NonceValue` is representation-only by contract, so
  CSPRNG production (CRYPTO-010) needed a provider, and hiding that capability
  behind an unregistered callable would have kept the count honest while making
  the architecture less so.
- **Superseded for the four peer tools at Stage 4E-R17-R1** *(see below)*. The
  deferral above was correct while no transport existed; Stage 4E-R17 proved it
  had become the blocker — three semantic variants share `negotiate`, three share
  `receive_turn`, two share `submit_audit`, and nothing frozen told a receiver
  which had arrived. The binding is now fixed. Everything else in this section
  stands, including that the chosen names are **PROJECT-CONTRACT**.
- **`StrategyPort` reaches a whole series at Stage 6C-C1.** `series_driver.SeriesDriver`
  builds one `SubGameDriver` per sub-game and hands each the same composed strategy, so
  the port is called exactly once per own turn across all six sub-games. **The register
  stays 21** - the series driver introduces no port, and every collaborator it uses is an
  existing runtime owner.
- **The permanent CLI reaches the same port at Stage 6C-C2.** `AutonomousBoot`
  builds the one `SeriesDriver` a process runs, so a real `uv run python -m …` process calls
  `StrategyPort` once per own turn for six sub-games. **The register stays 21**: boot
  adds no port, and `ArtifactStorePort` and `TokenAccountingPort` were already
  registered - it merely supplies their production implementations.

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

## Stage 4E-R17-R1 — the frozen peer-tool wire binding

`PRD02-FR-035` and **O7** deliberately deferred every concrete signature and JSON
schema to Stage 2B-2C. Stage 4E-R17 stopped `BLOCKED-BEFORE-CODE` on exactly that
gap: with the payload shape unfrozen, a conforming adapter could only have
dispatched by guessing which keys happened to be present, and two independent
implementations would have guessed differently. This section supplies the missing
binding. It is **PROJECT-CONTRACT** throughout — the book names no tools, no
envelope and no encoding — and it adds **no** requirement, error id, port, peer
family or `FIELD_MATRIX` row.

**Dependency.** The transport is **`fastmcp==3.4.6`** (exact pin, resolving
`mcp==1.29.0` and `pydantic==2.13.4`), over **Streamable HTTP**. STDIO is
permitted only for isolated framework probes and is never the counted-match
transport; SSE is not used. `PRD02-FR-037`'s "no FastMCP dependency at this
stage" described Stage 2; the dependency is authorized and pinned at Stage
4E-R17-R1.

### The request envelope

Every one of the four public tools takes **exactly one argument named
`request`**, whose JSON value is an object with **exactly two members**:

```
request = { "kind": <closed token>, "payload": { … } }
```

Both are **required**. No `type`, `message_type`, `msg_type`, `operation`, `op`,
`version`, `accepted`, `request_id`, `timestamp`, `sender` or `role` exists at
envelope level, and **no additional member is accepted** — the generated schema
carries `additionalProperties: false` at both levels and `required: ["kind",
"payload"]`, verified against the installed framework.

### The closed `kind` vocabulary, per tool

| Tool | `kind` | Decodes to |
|---|---|---|
| `negotiate` | `step0` | `Step0DeclarationExchange` |
| `negotiate` | `config_proposal` | `ConfigProposal` |
| `negotiate` | `config_lock` | `ConfigLockEvidence` |
| `receive_turn` | `commitment` | `Commitment` |
| `receive_turn` | `acknowledgement` | `Acknowledgement` |
| `receive_turn` | `reveal` | `Reveal` |
| `submit_audit` | `final_nonce_reveal` | `FinalNonceReveal` |
| `submit_audit` | `audit_disclosure` | the frozen JSON-native audit-disclosure core |
| `receive_control` | `result_agreement` | `ResultAgreement` |

Tokens are **lowercase ASCII, compared exactly** — no alias, no case folding, no
normalization, no whitespace trimming. An unknown token, a token sent to the
**wrong** tool, a missing member, a wrong-typed member or an extra member is
**`E-PROTO-MALFORMED`**; there is no cross-tool redispatch. **No heartbeat kind
exists**: `receive_control` carries `result_agreement` only, and no speculative
surface is added ahead of a requirement.

**The envelope is transport, not semantics.** It creates no peer family — the
inventory stays **8** — and `payload` carries the DTO of an already-frozen
semantic value. No `Step0Ack`, `ConfigAck`, `ConfigLockAck`, `ResultAck`,
`AuditAck`, `AuditBundle` or `MoveValidation` is introduced.

### Decimal on the wire

Every semantic `Decimal` crosses as **canonical decimal TEXT**: `Decimal("0.9")`
→ `"0.9"`, `Decimal("0.10")` → `"0.10"`. The receiver requires a JSON string,
validates it against the canonical decimal grammar, and constructs
`Decimal(text)` **directly**. JSON floats and integers, scientific notation,
whitespace, a leading `+` and locale separators are all **refused**, and there is
no rounding and no `Decimal(str(float))` path.

This is not caution about a hypothetical: measured against the installed stack, a
`Decimal`-annotated parameter given the JSON **number** `0.10` arrives as
`Decimal('0.1')` — a silent lexical loss that changes `config_sha256` and would
make two honest peers refuse each other. The same parameter given the JSON
**string** `"0.10"` arrives as `Decimal('0.10')`. Text is therefore the contract,
and the direct-`Decimal` path is deliberately not relied upon.

**The semantic and canonical layers are unchanged.** `CONFIG_CONTRACT.md` still
types these members `Decimal`, the canonical config bytes still carry the bare
JSON number `0.10`, and `FIELD_MATRIX.md` is untouched. Only the transport DTO
uses text.

### Success responses

| Kinds | Successful result |
|---|---|
| `step0`, `config_proposal`, `config_lock`, `commitment`, `acknowledgement`, `final_nonce_reveal`, `audit_disclosure` | **ordinary completion, no semantic value** — Python `None` |
| `reveal` | **`TurnOutcome`** — public acceptance + `CaptureAnswer` (**O5**, amended) |
| `result_agreement` | **`Sha256Digest`**, as exactly 64 lowercase hex characters, reconstructed client-side as `Sha256Digest(text)` |

Ordinary completion is **not** `accepted=true`, `ok=true`, `success=true` or an
ack family. Where the framework wraps a primitive result in its own
`structuredContent` object, that is a **framework envelope** and is never copied
into project semantics.

### Errors

A known application failure crosses the framework error channel carrying
**exactly its existing error identity** and nothing else — `E-PROTO-MALFORMED`,
`E-PROTO-STALE`, `E-AUTH-FAILURE`, `E-CONFIG-MISMATCH`, `E-REPORT-DISAGREE`,
`E-LOCAL-DEFECT`. **No Python exception text, no stack trace, no free-text
reason and no secret**; `key_id` remains the only key-related value that may
appear anywhere. The client adapter maps a known identity back to the local typed
failure; an unknown or malformed remote identity is `E-PROTO-MALFORMED`;
unreachable, HTTP failure and timeout stay with **`E-TRANSPORT`**. **No failure
is ever encoded as `False`** — that value belongs to `reveal` legality alone.

Verified against the installed framework: a `ToolError("E-PROTO-STALE")` is
observed client-side with `str(exception) == "E-PROTO-STALE"` **exactly**, with
no prefix or suffix, and the same identity is recoverable from the raw MCP error
content. **No error id was added: the inventory stays 20.**

## 8. External interoperability — the KIT profile

**Status: TRANSPORT IMPLEMENTED (Stage 8A-1T). A pinned-KIT peer can reach our
four tools and be understood. It cannot yet play us — see *What still blocks a
sparring series*.**

Several groups on this course use a shared interoperability kit
(`Imreec/copthief-league-protocol`), pinned here at
**`ad6557626587e09146af4283a5e808e7001343c5`**. It is **interoperability
guidance, not project source**: where the course book binds a rule, the book
wins, and the kit never overrides it.

### What is implemented

| Surface | Authority |
|---|---|
| Compact canonical JSON | `protocol/kit_canonical.py` |
| Commitment, **nonce outside** after a single `\|` | `protocol/kit_commitment.py` |
| `game_id` / `game_uid` / terms digest | `protocol/kit_identity.py` |
| Settlement consensus (**spaced** encoding) | `protocol/kit_consensus.py` |
| Codec / result dispatch | `protocol/commitment_codec.py`, `protocol/result_profile.py` |
| Evidence model | `app/audit_status.py`, `app/audit_provenance.py`, `app/audit_policy.py` |
| External audit | `app/kit_payload.py`, `app/kit_audit.py` |
| External preset | `app/kit_preset.py` |
| Wire messages, as values | `app/kit_messages.py`, `app/kit_greeting.py` |
| Out-of-band session context | `app/kit_session.py` |
| Envelope profile (one per process) | `transport/transport_profiles.py` |
| The four pinned tool arguments | `transport/kit_envelopes.py` |
| Inbound/outbound codecs | `transport/codec_kit_turn.py`, `transport/codec_kit_pregame.py` |
| KIT tool registration | `transport/kit_server.py`, `transport/kit_router.py` |
| Outbound argument construction | `transport/call_arguments.py` |
| Mode → wire selection | `composition_inputs.py` |

### Two canonical authorities, on purpose

`protocol/canonical.py` serves the **strict project domain**: it refuses `None`
and binary `float` and carries decimals as exact text, because a float `0.10`
reaching a project hash changes `config_sha256` and makes two honest peers
refuse each other for a reason neither can see. `kit_canonical` serves the
JSON-native domain the kit actually uses. Where the domains overlap they emit
identical bytes; neither may drift into the other.

### Our sealed record is ours, not a universal schema

The eight-member sealed record is **strict/internal**. The kit is explicit that
payload key sets need not match across teams — each side seals its own record
and the opponent re-hashes what it revealed. Our outbound KIT payload is
deliberately *richer* than the kit minimum (step, sub-game, role, move, intent,
hint, position, barriers) because we already hold that evidence; we require
none of it back.

### Cryptographic proof is not semantic proof

Two gates. **Gate 1** recomputes the digest and interprets nothing — a
faithfully sealed illegal move passes it. **Gate 2** weighs semantic evidence
with four answers:

- `VERIFIED` — evidence exists and the check passed
- `FAILED` — evidence exists and proves a violation
- `NOT_APPLICABLE` — the check does not apply
- `NOT_CHECKABLE` — it applies, but this lawful profile cannot decide it

**Missing evidence is not tampering**, and **an undecidable binding check is not
clean**. What a gap costs depends on provenance: the book's gameplay rules
block a counted result when unsettled; our own enrichments (JDEC-018 scent
truthfulness, which needs a disclosed trajectory a KIT peer never promised) do
not. Blocking and violations are reported separately so a gap in what we can
prove is never printed as an accusation.

Role, sub-game and configuration come from the authenticated session, the
witnessed cursor and the verified lock — a payload carrying them is
cross-checked, one omitting them has withheld nothing. Intent is read only as
one of its two sealed words and is never inferred from hint language.

### Authentication is unchanged

The kit's `terms_signature` is an **unkeyed content-agreement digest** — anyone
holding the terms and nonce recomputes it. It proves both sides read the same
values and nothing about who is speaking. `AuthProfile.HMAC_SHA256` Step-0
authentication remains separately mandatory and nothing substitutes for it.

### The scent family is deliberately undeclared

The kit registers `multiplicative_book_v1` beside its own
`subtractive_chebyshev_v1` (which we refuse — our physics is App F T16 FIXED,
C-10, JDEC-018). Measured against our production physics at the pinned SHA:
kernel identical across all 25 weights, parameters identical, update rule,
cadence, order and clamp identical, both emit vectors and both scalar traces
exact. But **29 of 90 published field-walk cells differ** — replicating the
kit's own recurrence in binary floats reproduces its vectors exactly, so every
difference is one ULP of IEEE-754 accumulation against our exact `Decimal`.

Classification: **`MODEL_FORM_MATCH` + `NUMERIC_VECTOR_MISMATCH`**, not
vector-exact. No family hash is published on that basis.

### The transport surface, and how it is selected

The pinned wire is `vectors/turn_message.json` at `ad65576`, status **PROMOTED**:
de-facto interoperability practice between independently written peers, **not
book law**. Where the book binds a rule the book wins.

Four public tool names, and one argument each — the asymmetry is the kit's and
it is load-bearing:

| Tool | Argument | Carries |
|---|---|---|
| `negotiate` | `message` | flat signed `terms` + `nonce` + `signature` + `group_id`, with pairing and locked-model declarations **beside** the terms |
| `receive_turn` | `message` | `step`, `sender`, `hint`, `smell_grid`, `commit`, `timestamp` (all required) plus four optional members |
| `submit_audit` | **`payload`** | `sender`, `records` (payload + nonce + commit), `result_claim` |
| `receive_control` | `message` | `kind` ∈ {enable, status, restart, quit}, `sender` |

A missing required key is **refused, never defaulted** — a defaulted commit is a
move the sender never sealed. An unknown key **inside** a message is tolerated
and ignored: that is the kit's declared extension seam, and it reaches no
semantic value, so it can mutate nothing.

**Two surfaces, and a process registers exactly one.** `ExternalMode` is chosen
out of band — `uv run python -m mars777_police --external-mode KIT_CORE_V1` — before the
server is registered and before the client exists. There is no auto-detection,
no key sniffing, no "try strict then KIT", and no downgrade after a failure:
each of those would turn an integrity failure into a silent compatibility story.
The same selection drives the outbound arguments, so a process cannot serve one
wire and speak the other.

Our published schemas were compared mechanically against the pinned peer's own,
read out of a running pinned server on its own FastMCP major (2.14.7). Tool
names, argument names, requiredness and the free-form message object are
identical. The one difference is at the *tool argument* level: our
`strict_input_validation` closes the argument object, so an unknown second
argument is refused rather than ignored. The kit's extension seam is one level
down, inside the message, and stays open.

### What a KIT turn is not

A KIT turn carries the sealed `commit` **and** the unsealed adjuncts in one
message, and never the action — under that wire the action is disclosed only in
`submit_audit`. So the commitment half maps exactly onto our `Commitment` and is
delivered to the unchanged `on_commitment`; the adjuncts are held beside it.
**No `Reveal` is invented**, and no second state machine exists: our own
commit → acknowledge → reveal cadence has no counterpart on this wire.

The smell grid is retained as the peer's binary64, unconverted. Our physics is
exact `Decimal`, and converting the peer's cells would assert an equivalence
that is `MODEL_FORM_MATCH` and **not** vector-exact.

### Role alternation, and the correction that produced it

**Stage 8A-1T reported that the pinned harness supported a fixed-role six-game
series. That was wrong, and it is corrected here.** `--role` selects only the
side the harness takes in **sub-game 1**; `netplay.py` then calls
`role_for(natural, n)` inside its per-sub-game loop, so roles alternate every
sub-game and there is no fixed-role networked mode (and no `--sub-games` on
`serve`). Stage 8A-2 stopped on that blocker with zero repository changes.

Alternation is **reference/de-facto interoperability practice, not a binding
course-book requirement** - the book's body never states it. We implement it
because the pinned harness mandates it, under the project's own existing
`SeriesConvention.REFERENCE_ODD_EVEN_ALTERNATION`.

### One group, two role backends

`teams.<group>.mcp_endpoint` is **group-level**. `MaRs-777` is one identity with
one opponent, one `game_id`, one `game_uid` and one six-sub-game series; the
Police and Thief repositories are two **role backends** behind it, and neither
ever becomes a dual-role agent.

```
            one stable MaRs-777 MCP URL
                        |
                 group role gateway          transport + series routing only
                   /           \
            Police backend    Thief backend  separate processes, separate repos
```

The gateway owns the live sub-game, the frozen convention, the route lifecycle
and a bounded handoff gate - and no board, position, legality, strategy, scent,
digest, audit decision or score. Routing comes from the contract (convention +
sub-game number + agreed first assignment), never from a source port, a process
id, an arrival time or a strategy output, and every message goes to exactly one
backend. Private backend endpoints are never advertised and never appear in a
declaration artifact.

Handoff is three explicit states - `ACTIVE(n)`, `SETTLING(n)`, `READY(n)` -
because the middle one is real: the peer greets for `n+1` while `n` is still
draining its audits. A next-sub-game greeting waits, bounded, until it can
actually be assigned, so an `ok` means **assigned**. Settlement is *signalled* by
the backend that played it and never inferred from HTTP silence.

### The terminal-settlement rule, and the defect it fixed

The first live sub-game (2026-08-18) settled `CAPTURE` on our side and `timeout`
on the peer's - the contradictory-reports shape App. E rule 35 zeroes on both
teams. Two causes, both fixed:

* **self-capture is the thief's rule.** Rules 46/47 end the game at a position
  only the thief can see. `BAR-004` lets the police place a barrier on its own
  cell and legally stand on a blocked one, so applying self-capture to the
  police manufactured a capture out of a lawful placement.
* **a terminal answer must ride out before we stop talking.** The opponent
  cannot see the board; walking away holding the answer makes it wait out its
  budget. A side that owes nothing still sends nothing - a survival claim that
  already rode on the turn just sent is not repeated.

### The measured series

2026-08-19, four processes, real FastMCP HTTP, isolated KIT venv, no patched KIT
source. `serve --peer <group url> --role thief --scent-model
multiplicative_book_v1`:

| gNN | KIT role | MaRs-777 backend | Outcome, both sides | KIT audit of our chain |
|---|---|---|---|---|
| g01 | thief | Police | survival, 35 steps | Verified OK |
| g02 | police | Thief | survival, 34 steps | Verified OK |
| g03 | thief | Police | survival, 35 steps | Verified OK |
| g04 | police | Thief | survival, 34 steps | Verified OK |
| g05 | thief | Police | survival, 35 steps | Verified OK |
| g06 | police | Thief | survival, 34 steps | Verified OK |

One identity throughout: `game_id MaRs-777-vs-sparring-local`. **Every row agrees
on both sides** - no `CAPTURE`-vs-`timeout` divergence. Our crypto gate verified
the peer's chain in every sub-game. The pinned `tools/check_artifacts.py` passes
every check over the peer's 14-file set for this series.

### Still not counted, and why

A perfect friendly is `KIT_FRIENDLY_ONLY`, and `counted_capable` is **derived**
from the run class rather than stored, so nothing can set it. Two independent
reasons: the source requires keyed producer authentication at Step-0 and the
pinned peer offers only an unkeyed content agreement, and the sparring group is
synthetic rather than an enrolled opponent. `AuthProfile.HMAC_SHA256` is
untouched, there is no fallback from a failed HMAC into friendly mode, and a
friendly never reaches the counted runtime at all - the inbound KIT path
branches on the run class, decided before boot.

### Official counted artifacts vs development friendly evidence

Two different things, in two different places, written by two different owners.

The **official counted contract is unchanged**: 1 declaration + 6 configs + 6
logs + 1 result = 14 files, and every writer still refuses what it always
refused. A KIT friendly satisfies none of those preconditions, and the audit is
worth stating precisely:

| Artifact | Counted-only precondition | Can a friendly satisfy it? |
|---|---|---|
| `declaration_<id>.json` | an authenticated Step-0 peer, and a full peer subtree (hardware, `code_version`, `github_commit`, `mcp_endpoint`) | **No** — the pinned `identity` carries none of those |
| `config_<id>_gNN.json` | `pregame.locked_evidence` — a **keyed** config-lock proof, cross-checked against `config_sha256` and the model digest | **No** — no keyed lock occurs |
| `log_<id>_gNN.json` | the strict `OutboundEvidenceRuntime` + `AuditRuntime` (eight-member sealed records) | **No** — the KIT chain is `{payload, nonce, commit}` |
| `result_<id>.json` | `exchange.is_agreed`, and the document hard-codes `"mutual_agreement": true` | **No** — the pinned four-tool wire has no result-agreement operation at all |

So a friendly does not produce a fourteen-file set, and forcing one would have
meant fabricating exactly the facts those files exist to record. **Truth outranks
the file count.**

What a friendly *does* produce is a **development evidence bundle**: one series
document plus one document per sub-game, written under `friendly_*` names
through a `DevelopmentEvidenceStore` that **cannot** emit a counted filename.
Every document names itself `DEVELOPMENT_EVIDENCE`, and the series document
states the two absences out loud rather than leaving them to be inferred:

```
"keyed_step0_authentication": "ABSENT"
"mutual_result_agreement":    "ABSENT"
"counted_eligible":           false
```

**No second result engine.** Scores come from `outcome_line` and totals from
`cumulative_of` — the same authorities the counted path uses. A *group* total
under alternation is a number no contract fixes, so none is published: each row
records which side we played, and a reader derives whatever the pairing agrees.

**Two role backends, one series.** Each backend writes its own role contribution
(settled facts and immutable references only — never a board, a position, a
barrier set or a nonce), and a collector merges them. Contributions that disagree
on `game_id`, `game_uid`, group or opponent are refused: that would be two
series, not one.

The kit's own result artifact is **not** mutual approval and is never read as
such. Its unilateral write is exactly what its own banner says it is.

### Identifier compatibility (Stage 8A-2G)

`JDEC-005`'s `game_id` alphabet is now `[A-Za-z0-9-]`, amended from `[a-z0-9-]`.
The book names `game_id`/`game_uid` and does not fix their format, so the format
is the project's; `group_id` is source-explicit and ours is `MaRs-777`, and the
kit derives `game_id` as `"-vs-".join(sorted(pair))` — so the lowercase rule
refused a filename for a game we had played. Case is preserved end to end and an
identifier is never rewritten: folding it would make two peers hash and compare
different games. Every traversal refusal is unchanged, and `game_uid`, the terms,
the commitment bytes and the result consensus are untouched.

One consequence: the development bundle no longer needs its own id validator and
shares `require_game_id`. Only its **filenames** stay separate.

### The two counted blockers, classified

**Keyed Step-0 authentication.** Unchanged and still required. The exact
non-secret contract a partner would implement is in
`docs/reference/KIT_PAIRING_HANDOFF.md`: HMAC-SHA256, a declared non-secret
`key_id`, `b"step0"` followed immediately by the canonical JSON of the sender's
own Step-0 core, exchanged with the pre-game greeting, key coordinated out of
band. It rides the pinned `negotiate` **beside** `terms`, so it cannot invalidate
`terms_signature` and needs no tool-schema change — but an unmodified kit peer
drops unknown keys, so both sides must opt in.

**Result agreement — `PARTNER_EXTENSION_REQUIRED`.** `ResultExchange.is_agreed`
needs four facts: our digest, the peer's digest, our request sent, the peer's
request handled. In strict mode the peer's digest arrives as the **return value**
of `receive_control(kind=result_agreement)`. The pinned wire cannot carry that —
a closed four-word control vocabulary, every tool answering `{"ok": true}` so no
digest can ride the response, and a driver that never calls `receive_control` at
all. The seam is already input-driven (`accept_peer_request` → `_verify` closes
the gate the moment a peer digest arrives by any means), so what is missing is
transport, not logic.

### Public deployment (Stage 8B-P)

Two things existed with no production caller: the group gateway and the
provider-neutral `PublicIngressPort`. `KitPublicLauncher` is the seam, and it is
deliberately thin — what a public endpoint *is* stays with the existing policy
(HTTPS, no userinfo, no query or fragment, the exact FastMCP path, a globally
routable host), and the launcher owns only the order things happen in and the
guarantee that both are released.

```
   partner  ──HTTPS──▶  ngrok agent  ──▶  group gateway (public tools)
                                             │        └── admin surface, loopback only
                                             ├──▶ Police backend   (private, own repo/venv)
                                             └──▶ Thief  backend   (private, own repo/venv)
```

Operator commands — three processes, because the two role backends are separate
repositories and stay that way:

* `uv run python -m mars777_police.kit_backend_main …` — one per role, in its own repo
* `uv run python -m mars777_police.kit_gateway_main …` — the group's public front door

**One endpoint is advertised.** The banner prints the group URL and nothing
else: no private backend address, no admin port, no key, no token. The public
endpoint is discovered fresh every run and forgotten on close — a remembered
hostname is a route to somebody else's tunnel.

**Measured live**, through the real HTTPS URL: exactly the four pinned tools with
the correct argument names (`submit_audit` → `payload`), `g01` routed to the
police backend, settlement signalled, `g02` routed to the thief backend, the URL
unchanged throughout, and the real counted-readiness authority still refusing
while the tunnel was up.

**Overhead** (local, 200 calls each): 6.4 ms direct to a backend, 14.2 ms through
the gateway — about **7.8 ms** for the extra hop, against a 180 s turn budget.
Decode 3.1 µs, encode 0.3 µs per turn; ~80 MB peak RSS per gateway process.
Documented and left alone: optimising 0.004% of a turn budget would be premature.

### What is still missing

A real partner. Nothing in the public path is waiting on us: what remains is an
agreed keyed Step-0 proof and an agreed result-digest exchange, both of which
need a partner to opt in, and both of which are specified in
`docs/reference/KIT_PAIRING_HANDOFF.md`.

## 9. The public SDK facade (Stage 9A-1B1)

**Classification: PUBLIC OUTER FACADE / USER-PROGRAMMATIC API.** Not domain, not
application business logic, not infrastructure. `mars777_police.sdk` is the one
import path every consumer uses - the command lines shipped here, a future
graphical interface, a future replay viewer, and any third party who installed
the distribution. The excellence guideline §4.1 asks for exactly one such
boundary; before this stage there were four entrypoints each reaching into
`app`, `domain`, `protocol`, `transport` and `infra` directly.

### What it contains

```
sdk/__init__.py     the export list - the promise
sdk/agent_sdk.py    AgentSdk: five operations, each one forwarding call
sdk/errors.py       the failure identities a caller must be able to tell apart
```

**`AgentSdk` decides nothing.** Every method forwards to the composition module
that owns the work and returns what it answered:

| Operation | Forwards to | Returns |
|---|---|---|
| `run_strict_series` | `compose_series.run_strict_series` | the artifact root |
| `compose_role_backend` | `compose_backend.compose_role_backend` | `KitBackendBoot` |
| `write_contribution` | `compose_backend.write_contribution` | the written path |
| `compose_public_gateway` | `compose_gateway.compose_public_gateway` | `KitPublicLauncher` |
| `verify_config_artifact` | `compose_verify.verify_stored_config` | what the bytes prove |
| `open_replay` | `compose_replay.open_replay` | a navigable, already-verified `ReplaySession` |
| `verify_replay` | `compose_replay.open_replay` | that session's `ReplaySummary` alone |

The one thing the facade owns is the **local software integrity check**: building
an `AgentSdk` verifies that the installed distribution is the version this source
tree declares, so a stale wheel shadowing the tree is refused before any
operation can run. It is local by construction and involves no peer.

### What it must never contain

Move legality, scoring, capture truth, commitment construction, scent physics,
strategy, audit rules, FastMCP tool definitions, provider mechanics, or HTTP
retry logic. Two structural tests enforce this - one that the facade names no
business authority and no framework, one that the operator entrypoints reach
nothing but the standard library and `.sdk`.

### What moved, and what did not

The assembly the three command lines used to perform moved down into
`compose_series`, `compose_backend`, `compose_gateway` and `compose_verify`, and
the role constant into `identity`. **No behaviour moved**: every flag, default,
exit status, refusal message and banner line is what it was, and the same tests
that pinned them still pin them.

### The live-view seam, and why the GUI is not behind the facade

`LiveViewSink`, `LatestSnapshot` and `LiveViewSnapshot` are exported (Stage
9A-2B) because a viewer must be able to attach to a running series and name what
it receives; `StrictSeriesRequest` carries an optional `viewer`, defaulting to a
sink that discards.

**The drawing itself is deliberately not a facade operation.** `mars777_police.gui`
*consumes* this facade: a presentation package imported by the facade would point
the dependency the wrong way, and would make every command line load an imaging
library merely to parse an argument. `gui_main` is therefore held to its own
rule - the facade, the identity it prints, the drawing package and the live sink,
and nothing else - rather than to the counted entrypoints' "standard library and
`.sdk`" rule, and `tests/gui/test_gui_entrypoint.py` states which.

## 10. The API Gatekeeper (Stage 9A-1C)

**Classification: application policy controlling infrastructure provider calls.**
Not domain, not transport, not a provider adapter. `app/gatekeeper.py` is the one
place an external **provider** call passes through, as the excellence guideline
§5.1 asks.

### What it controls, and what it deliberately does not

| Surface | Classification | Why |
|---|---|---|
| `ngrok.discover_tunnels` — the local Agent API read | **GENERIC_GATEKEEPER** | a third-party service with its own failure modes; rate, concurrency and observation belong in one place |
| a future `reporting.send_report` | **GENERIC_GATEKEEPER** | the surface Appendix E rule 28 and `REPORT-003` actually govern |
| `receive_turn`, `submit_audit`, `receive_control` | **PROTOCOL_SPECIFIC_AUTHORITY** | a generic resend re-sends a turn the opponent already applied (App. E rule 35), and a queue would break lockstep |
| `negotiate` / Step-0 | **PROTOCOL_SPECIFIC_AUTHORITY** | `startup_budget` already retries exactly one condition — "the peer is not listening yet" — and nothing else |
| release and teardown | **NOT_APPLICABLE** | cleanup makes no provider HTTP call at all: it stops a child process, cancels a task and closes a socket |
| LLM provider | **NOT_APPLICABLE** | the shipped hint path is a deterministic template catalogue |

Two structural tests hold that boundary in both directions: no peer-transport or
gameplay module may import the gate, and the provider adapter must be composed
with a gated fetcher.

### What it is made of

```
shared/rate_limits.py        the policy value objects and the supported versions
infra/rate_limit_file.py     the one loader for config/rate_limits.json
app/gatekeeper_windows.py    rolling per-minute and per-hour windows, monotonic
app/gatekeeper_queue.py      the bounded FIFO a rate-limited caller waits in
app/gatekeeper_retry.py      which failures may be repeated, and for how long
app/gatekeeper_events.py     what is recorded about a call - shape, never payload
app/gatekeeper.py            admission, execution, retry, observation
```

Time is injected (`monotonic`, `sleeper`), so every interval is deterministic in
a test and no test sleeps for real.

### What it must never contain

Game state, board, strategy, scent, commitments, peer semantic state, a transport
framework, or a caller-chosen retry count. Every operation resolves a **named
policy** from the versioned configuration file; there is no "execute anything".

### Cleanup safety

Teardown was audited before anything was routed: `NgrokProcess.stop()` terminates
a child process, `release()` cancels a task and closes a listener, and
`close_session()` exits a peer session. **None of them is a provider HTTP call**,
so no rate limit, queue or backpressure can stand between this agent and putting
its tunnel away. That is the smallest safe design — the existing direct
idempotent path — rather than a reserved-capacity lane that would have to be
correct under cancellation.

## 11. The Replay Viewer (Stage 9A-2A)

**Classification: user-facing projection over existing authorities.** Not an
engine. `REPLAY-001` asks for a viewer that replays a game log and
cryptographically verifies it; Appendix E rule 20 makes it a threshold for
approving audits and for submission.

### What it is made of

```
app/replay_values.py     the public immutable projection, and the four statuses
app/replay_log.py        the strict inverse of `log_document.finalized_log`
app/replay_crypto.py     per-step digest correspondence, asked of the port
app/replay_board.py      the textual board a human reads
app/replay_session.py    the ordered, navigable sequence of whole steps
infra/replay_files.py    the defensive reader: containment, size, JSON only
transport/codec_replay.py a logged action back to its domain value
compose_replay.py        two files plus the commitment authority
replay_main.py           the operator command
```

### What it delegates, and to whom

| Question | Authority |
|---|---|
| could this turn have happened here? | `app/semantic_replay.Replay` — the engine the live audit used |
| is this move legal? | `domain.rules`, `domain.barriers` |
| does the digest correspond? | `CommitmentPort` → `protocol/audit_commitment` |
| is this configuration the logged one? | `protocol/config_lock.config_sha256` |
| what shape is a logged action? | `transport/codec_turn.decode_action` |

A structural test asserts the viewer computes no digest of its own (`hashlib`,
`hexdigest`, `sha256(` all absent), imports no rule module, and that the command
reaches nothing but the standard library and `.sdk`.

### The four statuses, and why there are four

`Verified OK` and `TAMPERED` are `REPLAY-002`'s own words and are used
literally. `NOT_CHECKABLE` exists because a commitment whose nonce was never
disclosed to this side is not verified and is not tampered — collapsing it into
either would be a false claim. `NOT_APPLICABLE` covers records that carry no
commitment at all.

### What it will not replay

Development (friendly) evidence, by construction: a contribution carries settled
facts only and its own contract states it *"deliberately cannot carry a board, a
position, a barrier set or a nonce"*. The viewer refuses it with that reason
rather than reconstructing a board it was never given.

### Audit completeness (Stage 9A-2AF)

A supervising question closed after the viewer shipped: could **incomplete**
source-required evidence produce a successful verification simply because
everything that happened to be checkable passed?

It could not return `0` — but it was reported with the same exit status as a real
mismatch, and a legitimately inapplicable record downgraded the whole summary.
Both were corrected.

| Situation | Per record | Summary | Exit |
|---|---|---|---|
| every required commitment present and matching | `Verified OK` | `Verified OK` | `0` |
| a recomputation performed and mismatched | `TAMPERED` | `TAMPERED` | `3` |
| a required nonce never disclosed | `NOT_CHECKABLE` | `NOT_CHECKABLE` | **`4`** |
| a record with no commitment to check | `NOT_APPLICABLE` | does not downgrade | — |
| a commit entry with no commitment at all | — | refused | `2` |

`worst_check` states the ordering as an invariant: a mismatch outranks an
absence, an absence outranks every verified record, and `NOT_APPLICABLE` outranks
nothing. So no later verified step can upgrade an earlier finding, and no absent
nonce is ever promoted to an accusation.

`audit_complete(summary)` is the programmatic form of the same rule, exported
from the SDK so a caller never parses human text. It is **derived**, not stored:
`Verified OK` already means every applicable record was recomputed and matched.


## 12. The graphical interface (Stage 9A-2B)

**Classification: presentation only.** Not domain, not application policy, not
transport. `mars777_police.gui` renders values other modules already decided, and
`app/live_view_*` projects and publishes them. Nothing here decides a move, a
barrier, a capture, a scent value, a commitment, a semantic verdict, a protocol
transition, a score or a result agreement.

### What it is made of

```
app/live_view_values.py  the lawful live projection, and what may be in it
app/live_view_sink.py    the one-slot lossy drop box, and its failure guard
app/live_view_feed.py    the single call the driver makes, once per round
app/action_words.py      one short human word for an action, shared by all views
gui/primitives.py        Rect, Text, Frame - what to draw, toolkit-free
gui/geometry.py          where a board of any size goes, deterministically
gui/palette.py           colour AND glyph AND word for every status
gui/live_layout.py       the live picture: local truth only
gui/replay_layout.py     the replay picture: both agents, after the audit point
gui/image_renderer.py    the offscreen raster (Pillow), for CI and screenshots
gui/window.py            the interactive window (tkinter) - the only toolkit user
gui/live_app.py          a window that polls the box on a timer
gui/replay_app.py        a window that navigates a finished ReplaySession
gui_main.py              the operator command, `replay` and `live`
```

### The two directions that matter

| Rule | How it is structural |
|---|---|
| the GUI cannot see more than the agent | the live snapshot is projected from `Observation`, whose four members have no field an opponent position could arrive in |
| the GUI cannot affect the game | the driver's only call is `feed.show(...)`, which returns nothing, is guarded, and reaches a one-slot box |
| the GUI cannot decide anything | `gui/` imports no strategy, turn service, protocol, transport or infrastructure module; no key is bound to anything but navigation |
| the GUI cannot leave this machine | no module in `gui/` imports `socket`, `http`, `urllib`, `httpx`, `requests`, `ssl`, `subprocess` or `pickle` |
| the toolkit cannot spread | `tkinter` appears in `gui/window.py` alone and Pillow in `gui/image_renderer.py` alone |

### Why two renderers rather than one

Layout produces a `Frame`; two adapters draw it. CI has no display, so the
offscreen rasteriser is what lets the graphical output be asserted on Ubuntu and
on Windows, and it is what produced the committed screenshots. The interactive
window is proved against recording doubles everywhere and against the genuine
toolkit wherever a display exists.
