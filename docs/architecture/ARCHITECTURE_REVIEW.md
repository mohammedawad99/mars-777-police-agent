# Architecture Red-Team Review — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — adversarial review of the Stage-2A design.**

The architecture was attacked along the mandated axes. Findings are recorded whether or
not they were comfortable. **All architecture-blocking findings are resolved below**;
open items are non-blocking and carry an explicit owner stage.

Severity: **BLOCKING** (must resolve before Stage 2A PASS) · **HIGH** · **MEDIUM** · **LOW**.

| # | Severity | Component | Failure mode | Correction | Status |
|---|---|---|---|---|---|
| **R-01** | BLOCKING | Orchestrator / state | **Central-state creep** — an orchestrator that accumulates both peers' facts becomes a de-facto referee, contradicting ARCH-001/002. | `STATE_OWNERSHIP.md` gives every datum exactly one owner and lists **no opponent-truth state at all**; the orchestrator holds only a turn cursor and sub-game index. | **RESOLVED** |
| **R-02** | BLOCKING | Repos / runtime | **Accidental shared state** between police and thief (shared venv, shared artifact dir, cross-import). | TB-2/TB-3 declared; `DEPENDENCY_RULES.md` forbids cross-package import; per-repo `.venv` and artifact roots; isolation test planned (`TEST_ARCHITECTURE.md` #18). | **RESOLVED** |
| **R-03** | BLOCKING | Strategy | **Strategy/network coupling** — a strategy that can call the peer or write artifacts can cheat, leak, or desynchronize. | `StrategyPort` accepts `Observation`, returns `ProposedAction`; strategy may import only `app.strategy_api` + domain value types; transport/crypto/artifact imports forbidden and test-enforced. | **RESOLVED** |
| **R-04** | BLOCKING | GUI | **GUI private-truth leak** — rendering the objective board would violate GUI-001/002. | GUI consumes **projection events only**, never the domain aggregate; belief is rendered explicitly labelled as belief; leak-scan test asserts forbidden keys absent. | **RESOLVED** |
| **R-05** | BLOCKING | Logger | **Log private-truth leak** — a generic "dump state" logger would serialize secrets or forbidden data. | Logger takes **whitelisted structured events**, not arbitrary objects; nonce only in the final-audit section; secrets never logged; scan test planned (#17). | **RESOLVED** |
| **R-06** | BLOCKING | Config | **Config ambiguity** — local settings silently overriding binding game values. | `CONFIG_ARCHITECTURE.md` R2/R8: binding config has **one source** and **no override chain**; an override attempt is `E-LOCAL-DEFECT`; immutable after lock. | **RESOLVED** |
| **R-07** | BLOCKING | Crypto | **Self-referential digest/tag** — hashing bytes that contain the hash is undefined and forgeable. | Non-self-reference is explicit for `config_sha256`, `result_sha256`, and every `auth_tag`; domain separation via `context ∈ {"step0","config"}` prevents cross-object replay. | **RESOLVED** |
| **R-08** | BLOCKING | Concurrency | **Race on turn state** — two concurrent peer requests mutating the same turn. | Single Turn Executor + turn-cursor guard + idempotent re-delivery (`CONCURRENCY_MODEL.md` §2). Domain never entered concurrently. | **RESOLVED** |
| **R-09** | HIGH | State | **Duplicated mutable state** — e.g. barriers living in both domain and log. | Log is an **append-only record**, not a second live set; score is computed once and recorded once; anti-duplication rules listed in `STATE_OWNERSHIP.md`. | **RESOLVED** |
| **R-10** | HIGH | Async | **Ordering bugs** — out-of-order/duplicate/stale messages applied twice. | State machine R6/R8: cursor match required; stale ⇒ `E-PROTO-STALE`, answered idempotently; planned test #7. | **RESOLVED** |
| **R-11** | BLOCKING | Replay | **Replay depending on live state** — would make "verification" circular and worthless. | `ReplayPort` takes **file paths only**; `infra.replay` forbidden from importing `app`/live `domain`; planned test #20 runs replay in a fresh process with no network. | **RESOLVED** |
| **R-12** | HIGH | Reporting | **E-mail/report changing game state.** | Reporter reads **sealed artifacts**; no write path into domain/app; `result_sha256` covers an already-final core. | **RESOLVED** |
| **R-13** | BLOCKING | LLM | **LLM bypassing the validator** (directly producing a move). | Every advisor output enters as a `ProposedAction` through the same deterministic validator; bypass import forbidden; T2 only under the locked mutual-agreement exception; zero-token fallback always viable. | **RESOLVED** |
| **R-14** | HIGH | Cross-OS | **Windows/Linux path & encoding drift** breaking byte-identical hashes. | Canonical bytes fixed (UTF-8, NFC, LF, sorted keys, `(",",":")`, no trailing newline); golden-vector tests asserted on both OSes; CI already runs both (planned test #16). | **RESOLVED** |
| **R-15** | HIGH | Modules | **Modules too large for the ≤150-line rule**, or the opposite failure — shredding into meaningless micro-files. | `MODULE_BOUNDARIES.md` splits along **real seams** (rules vs scoring; server vs client vs gatekeeper; commitment vs keyed_auth vs config_lock) and states the sizing rule explicitly. Re-checked at implementation time as a Repository-Gate criterion. | **RESOLVED (re-verify in 2C)** |
| **R-16** | BLOCKING | Testability | **Architecture untestable without public internet** — would make CI meaningless. | All layers through INTEGRATION/REPLAY run offline against an in-process or subprocess **fake peer**; only EXTERNAL DELIVERY needs the internet; `ClockPort` injected so timing is deterministic. | **RESOLVED** |
| **R-17** | HIGH | Security | **Prompt injection via peer-supplied hint text** reaching the LLM. | Peer text is **data, never instruction**; bounded sanitized context; output advisory only and validator-gated (T12 in `SECURITY_ARCHITECTURE.md`). | **RESOLVED** |
| **R-18** | HIGH | Security | **Secret leakage through error messages / metrics labels** (e.g. keying a metric by the key itself). | Only non-secret `key_id` may appear anywhere; error payloads carry alg/verdict only; secret scan is a Repository-Gate criterion. | **RESOLVED** |
| **R-19** | MEDIUM | Belief | **Belief promoted to truth** — a code path copying belief into `domain.truth` would fabricate knowledge. | Explicit anti-duplication rule 4; separate types; belief always carries uncertainty and is labelled wherever it surfaces. | **RESOLVED** |
| **R-20** | MEDIUM | Metrics | **"Belief quality" metric requiring opponent truth live**, which would breach the privacy model. | Belief quality is defined as a **replay-time, post-disclosure** analysis only; never computed during play (`OBSERVABILITY.md` §3). | **RESOLVED** |
| **R-21** | MEDIUM | Gatekeeper | **Retrying an integrity error** (e.g. re-sending after an auth failure) would look like an attack. | `ERROR_MODEL.md` principle 2: only transport-class errors retry; integrity/legality never retried. | **RESOLVED** |
| **R-22** | MEDIUM | GUI | **GUI backpressure stalling the game loop.** | GUI channel is subscribe-only and **lossy by design**; dropping a frame cannot block or alter play. | **RESOLVED** |
| **R-23** | MEDIUM | Artifacts | **Half-written artifact after a crash** breaking replay. | Atomic write (temp → fsync → rename); write-once then sealed; graceful shutdown drains and seals. | **RESOLVED** |
| **R-24** | LOW | Ports | **Over-specifying FastMCP signatures too early**, locking us out of opponent negotiation. | `API_BOUNDARIES.md` fixes **architecture-level ports only**; concrete tool signatures deferred to Stage 2B/2C except where the locked source already forces a field. | **ACCEPTED (deliberate)** |
| **R-25** | LOW | Strategy | **Non-deterministic strategy breaking reproducibility.** | Strategies are deterministic **given a seed**; seed recorded as evidence; global randomness forbidden. | **RESOLVED** |

## Blocking-finding status

**All 10 BLOCKING findings (R-01, R-02, R-03, R-04, R-05, R-06, R-07, R-08, R-11, R-13, R-16) are RESOLVED within Stage 2A.**
No architecture-blocking issue remains open.

## Deliberately deferred (non-blocking, with owner)

| Item | Why deferred | Owner |
|---|---|---|
| Concrete FastMCP tool signatures | Requires opponent negotiation; premature locking would create interop risk | Stage 2B/2C (PRD-02/05) |
| LLM provider/SDK selection | No dependency may be added at Stage 2A; T0 must work regardless | Stage 2C (PRD-04) |
| Local settings file format / CLI flags | Implementation detail with no architectural consequence | Stage 2B/2C |
| Re-verification of the ≤150-line rule | Can only be measured against real code | Stage 2C + Repository Gate |
| GUI toolkit choice | Must not influence the projection contract | Stage 2C (PRD-07) |
