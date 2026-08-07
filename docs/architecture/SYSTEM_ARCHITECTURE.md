# System Architecture — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only. No implementation exists.**

Input: the **locked** Stage-1 specification (`../spec/`). Nothing here may change a
locked fact; a conflict must be raised as **SPECIFICATION CONFLICT**, never resolved
silently.

## 1. Fundamental shape

The system is **two independent peer agents**. There is **no central game authority,
no referee process, no shared database, and no shared memory**. Each peer holds its
own truth, exchanges only what the protocol permits, and both cross-audit afterwards
(commit-reveal + replay). Agreement is produced by **matching evidence**, not by a
coordinator (ARCH-001/002, INV-06/11).

```
   ┌──────────────────── LOCAL AGENT PROCESS (this repository) ────────────────────┐
   │                                                                               │
   │  ┌─────────────── application / orchestration ───────────────┐                │
   │  │  Orchestrator  ──drives──►  State Machine                 │                │
   │  │       │                          │                        │                │
   │  │       │ asks                     │ gates every action     │                │
   │  │       ▼                          ▼                        │                │
   │  │  Strategy Engine ──proposes──► Legality Validator (domain) │               │
   │  └───────────────────────────────────────────────────────────┘                │
   │            │ reads (role-legal view only)                                     │
   │  ┌─────────▼──────────── domain (pure, deterministic) ───────────────┐        │
   │  │  Local Truth  ·  Belief State  ·  Scent  ·  Barriers  ·  Board    │        │
   │  │  Rules/Legality  ·  Scoring  ·  Config Model (Appendix F)         │        │
   │  └───────────────────────────────────────────────────────────────────┘        │
   │            ▲ commands / events                                                 │
   │  ┌─────────┴────────────── protocol & adapters ──────────────────────┐        │
   │  │ Commit-Reveal · Config Lock · Step-0 Auth · Protocol Adapter      │        │
   │  │ Language/Hint subsystem · Deadline & Watchdog · Gatekeeper        │        │
   │  └───────────────────────────────────────────────────────────────────┘        │
   │            ▲                                                                   │
   │  ┌─────────┴────────────────── infrastructure ───────────────────────┐        │
   │  │ FastMCP Server · FastMCP Client · Structured Logger · Artifact    │        │
   │  │ Store · Clock · Token/Cost Accounting · GUI Projection · Reporter │        │
   │  └───────────────────────────────────────────────────────────────────┘        │
   └───────────────────────────────────────────────────────────────────────────────┘
```

## 2. Components and single responsibilities

| Component | Single responsibility | Never does |
|---|---|---|
| **Orchestrator** | Sequences a sub-game: asks the state machine what is legal next, invokes the right port, records evidence | Decide moves; parse wire bytes; format e-mail |
| **State Machine** | Owns the legal state/transition graph; refuses out-of-order events | Contain game rules or strategy |
| **Strategy Engine** | Proposes an intended action from a **role-legal observation** | Send network messages, touch nonces/hashes, mutate authoritative state |
| **Legality Validator** (domain) | Deterministically accepts/rejects any proposed or received move/barrier | Ask an LLM (LLM-001/E-25) |
| **Local Truth** | This agent's own authoritative position/barrier/step facts | Store opponent private truth |
| **Belief State** | Probabilistic/inferred opponent estimate from *permitted* observations only | Read opponent truth |
| **Scent subsystem** | Pheromone field emission/decay per Appendix F (0.9 / 0.10 / 5) | Invent values outside signed config |
| **Barrier subsystem** | Barrier placement legality, quota, irreversibility | Hide a placement (BAR-001/002) |
| **Language/Hint subsystem** | Produces/consumes bounded natural-language hints + truth/lie `intent` | Decide movement |
| **Protocol Adapter** | Translates wire JSON ⇄ domain commands/events; strict validation | Apply game effects directly |
| **FastMCP Server** | Exposes this peer's inbound tool surface | Trust input; hold game truth |
| **FastMCP Client** | Outbound calls to the opponent peer | Retry policy decisions (Gatekeeper owns) |
| **Gatekeeper** | Rate-limit / concurrency / retry / backoff / queue (Appendix F T19) | Alter game semantics |
| **Commit-Reveal** | `H_commit` computation, nonce custody, reveal, verification | Reveal a nonce early (CRYPTO-002) |
| **Config Lock** | Canonical config, `config_sha256`, keyed config authentication, immutable lock | Renegotiate after lock |
| **Deadline / Watchdog** | Per-step deadline + watchdog escalation (30s / 60s NEGOTIABLE) | Silently extend a deadline |
| **Structured Logger** | Append-only evidence records | Log private opponent truth or secrets |
| **Replay Evidence** | Produces/reads the artifact set enabling independent verification | Read live agent state |
| **Metrics / Cost Accounting** | Latency, retries, tokens, cost | Influence a move |
| **GUI Projection** | Read-only projection of *permitted* view | Expose the objective board (GUI-001/002) |
| **Reporting** | Builds the final result artifact and sends it | Mutate game state |
| **SeriesLauncher** *(2A-R2)* | Selects which **independent role process** runs each sub-game of a series (supports the role-alternation convention) | **Own game truth; act as a referee; hold both peers' state; merge the two role repositories** |
| **CompatibilityProfile** *(2A-R2)* | Selects the negotiated `AuthProfile` / `CommitmentCodec` / `ResultProfile` for a match | Weaken any binding requirement in strict mode |

## 3. External boundaries and trust

| External entity | Channel | Trust | Architectural stance |
|---|---|---|---|
| **Opponent peer** | FastMCP over public tunnel | **UNTRUSTED** | Validate every field; verify hashes/tags; never accept opponent claims about our own truth |
| **Public tunnel** | HTTPS ingress | **UNTRUSTED transport** | Endpoint carries no secret; assume observable and replayable |
| **GitHub** | Git over SSH | Semi-trusted | Source identity only (`github_commit`); never a game authority |
| **Gmail** | SMTP/API egress | Semi-trusted | One-way delivery of a **finalized** artifact; cannot change state |
| **GUI user** | Local UI | Trusted operator | Read-only projection; cannot inject moves |
| **Filesystem artifacts** | Local disk | Trusted-but-auditable | Append-only evidence; canonical bytes |
| **LLM provider** (optional) | Network | **UNTRUSTED advisor** | Output is a *suggestion*; must pass deterministic validation |

**Trust boundaries (TB):**
- **TB-1 Peer boundary** — everything crossing the FastMCP surface, inbound or outbound.
- **TB-2 Process boundary** — police and thief are separate OS processes; no shared memory/variables (ARCH-001/002).
- **TB-3 Repository boundary** — the two repositories share **no runtime state**; only reviewed documentation was ever synchronized.
- **TB-4 Advisor boundary** — LLM suggestions enter only through the validator.
- **TB-5 Evidence boundary** — once written and hashed, evidence is immutable; replay/report read across it, never back.
- **TB-6 Secret boundary** — key material and credentials exist only in the local environment, never in artifacts, logs, docs, or Git.

## 4. Structural invariants

1. **No central authority.** No component may hold both peers' truth.
2. **Dependencies point inward** (`DEPENDENCY_RULES.md`); no cycles.
3. **One authoritative owner per mutable state** (`STATE_OWNERSHIP.md`).
4. **Strategy is replaceable** without touching networking, crypto, persistence, GUI, or reporting (`STRATEGY_ARCHITECTURE.md`).
5. **Zero-token operation is always viable** — the LLM path is strictly optional (`LLM_BOUNDARY.md`).
6. **Determinism where possible** — same seed + same inputs ⇒ same decisions; all non-determinism is injected (Clock, RNG, transport).
7. **Every state-changing event leaves evidence** sufficient for independent replay (REPLAY-001/002).
8. **Windows + Linux equivalence** — canonical bytes (UTF-8, LF, NFC, sorted keys) are OS-independent (JDEC-002).

## 5. Compatibility and series orchestration (Stage 2A-R2)

**SeriesLauncher.** Role alternation across sub-games is an **attachment-example and
reference convention**, not a book MUST (see `../reference/ATTACHMENT_EVIDENCE.md`
AE-01). The architecture supports it **without merging the roles**: a thin, local
`SeriesLauncher` starts the appropriate **independent** role process for each sub-game
(our police agent when we play cop, our thief agent when we play thief). It holds **no
game truth**, validates nothing, and is **not** a central authority — it only sequences
process activation. Process/tunnel persistence across sub-games is **PRD-02/PRD-05** work.

**Profiles.** Three negotiated, additive profiles are defined in
`../reference/COMPATIBILITY_PROFILES.md`:
`STRICT_COUNTED_MATCH` (default, the only emit profile for a counted game),
`LECTURER_REFERENCE_COMPATIBILITY`, `LECTURER_ATTACHMENT_COMPATIBILITY`.
A profile may **add** accepted encodings; it may **never weaken** a binding requirement.

**Self-containment (corrected).** The **four-artifact set** is self-contained, not the
result file alone: static metadata lives in the declaration and the result joins to it
by `game_uid`/`group_id` (JDEC-014, INV-10 corrected).
