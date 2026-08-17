# Concurrency Model — group MaRs-777

**Status: STAGE 2A ARCHITECTURE FREEZE — design only.**

**Guiding rule: the game is deterministic and single-threaded; only I/O is
concurrent.** Simplicity is a correctness feature here — a race that corrupts turn
state is indistinguishable from cheating and can void a match.

## 1. Model

```
   async I/O edge (FastMCP server, client, timers)
                │  events enqueued
                ▼
        ┌────────────────────────┐
        │  single Turn Executor  │   ← serializes ALL state-changing work
        │  (one logical thread)  │
        └────────────────────────┘
                │ applies
                ▼
        state machine + domain (never touched concurrently)
```

- **One asyncio event loop.** No threads for game logic; no multiprocessing.
- **The domain and state machine are never entered concurrently.** All mutation happens
  inside the Turn Executor's serialized critical section.
- **Inbound requests do not mutate directly.** The MCP server validates, converts to an
  event, and submits it to the executor queue.

## 2. The concurrency rule that matters most

> **Two concurrent peer requests must never mutate the same turn state.**

Enforced by three layers:

1. **Serialization** — a single executor with an ordered queue; one event is processed
   to completion (including evidence write) before the next begins.
2. **Turn cursor + admissibility guard** — a turn-scoped inbound message carries
   `(sub_game, step)`, which identifies the turn; the executor accepts it **only** if that
   cursor matches the expected one **and** the message family is admissible in the
   receiver's current `ProtocolMachine` state. Anything else is `E-PROTO-STALE`
   (duplicate/replayed/out-of-order) and is rejected, not queued. Phase is **not** a
   transmitted cursor field — the receiver already owns the one authoritative phase
   (Stage 4E-R1-FIX1; previously this read "every inbound message carries
   `(sub_game, step, phase)`"). Control and finalization messages carry their own
   semantic identity instead of a turn cursor.
3. **Idempotency** — re-delivery of an already-applied step is answered from the
   recorded result; it never re-applies an effect (`STATE_MACHINE.md` R8).

Consequence: concurrency cannot reorder game history, and a hostile peer cannot induce
a double-apply by flooding.

## 3. Component lifecycles

| Component | Lifecycle | Notes |
|---|---|---|
| **FastMCP server** | started at BOOT, stopped at shutdown | Bound locally; exposed via tunnel; readiness is a BOOT gate |
| **Outgoing peer calls** | per request, `async`, bounded | Always through Gatekeeper; never fire-and-forget for state-changing calls |
| **State machine** | one instance per process | Entered only from the executor |
| **Watchdog** | one timer per active step | Escalates: soft (`response_timeout_sec`) → hard (`watchdog_timeout_sec`). **Appendix F defaults 30 s / 60 s, status NEGOTIABLE** — the values actually used are read from the **locked negotiated config**, never hard-coded |
| **Deadline timers** | per step / per outbound call | Cancelled on completion; expiry becomes an executor event |
| **Retries** | Gatekeeper-owned | Transport-class errors only; never integrity errors |
| **Token bucket** | process-wide | `tokens←min(C, tokens + r·Δt)`; send iff `tokens ≥ 1` (NET-002) |
| **Queue depth** | bounded (App F T19 default 100 MINIMUM) | Overflow ⇒ reject with backpressure, never unbounded growth |
| **GUI channel** | subscribe-only async queue | **Lossy by design** — dropping a frame must never block or alter the game |
| **Graceful shutdown** | drain → seal evidence → stop server | Never abandon a half-written artifact |

## 4. Rate limiting and backoff

- Token-bucket limiter on **outgoing** calls (default 30 rpm MINIMUM).
- Concurrency cap (default 2 MINIMUM) on simultaneous outbound requests.
- Retry with backoff (default 5s MINIMUM, max_retries 3 MINIMUM).
- **HTTP 429 ⇒ back off and wait for the next window**, never immediate retry
  (REPORT-003/NET-002) — blind retry risks account suspension.
- Retry budget exhaustion ⇒ `E-RETRY-EXHAUSTED`, escalate per `ERROR_MODEL.md`.

## 5. Determinism guarantees

- Given the same seed, the same `Observation` sequence and the same injected clock, the
  **strategy decisions are reproducible**.
- Non-determinism is confined to `PeerTransportPort`, `PeerServerPort`, `ClockPort`,
  `ReportPort`, `LlmAdvisorPort` — all injected and fakeable.
- Replay never depends on timing: it reads sealed artifacts and recomputes hashes.

## 6. Known limitation — native-Windows two-process blackout

**Status: open, investigation closed, no workaround adopted (Stage 6C-C2-FINAL).**

The full six-sub-game series runs end to end on Ubuntu and WSL, as two real OS
processes, writing all fourteen official files and exiting 0. On **native
Windows** the same pair reproducibly stalls at the `g01` step-22 acknowledgement
and neither side finishes.

What was measured, twice, at two different negotiated response deadlines:

| Locked `response_timeout_sec` | Peer POST held | Opponent heartbeat blackout |
|---|---|---|
| 30 | 30.375 s | 30.375 s |
| 45 | 45.391 s | 45.593 s |

The request body arrives promptly and completely; the receiving side's event
loop then makes no progress until the *caller's* deadline expires, and resumes
at that moment. **The blackout is released by peer cancellation, so raising the
deadline lengthens the stall rather than surviving it.** The negotiated default
therefore stays at Appendix F's 30 s, no retry was added, and no gameplay,
protocol or configuration workaround was adopted.

Scope and honesty about what this is:

- It is **not** a Proactor-specific scheduling defect. A controlled experiment
  reproduced essentially the same stall with the synthetic opponent running
  `_WindowsSelectorEventLoop` while this agent stayed on `ProactorEventLoop`, so
  it reproduces under **both** tested Windows event-loop policies.
- It is best described as a **Windows-native two-process event-loop blackout /
  mutual peer-request deadlock in the current FastMCP / MCP / AnyIO execution
  path**. The exact internal third-party or runtime primitive responsible
  **remains unresolved**, and nothing here is a proven upstream bug in FastMCP,
  MCP, AnyIO, asyncio or Windows.
- `g01` step 22 is the **observed integration seam** where it surfaces, not a
  protocol-mandated failing cursor.
- The counterparty is the synthetic, non-counted integration opponent. This
  limitation says nothing about counted interoperability, which still requires
  another group's agent.

Two real timeout-authority defects were found and fixed while investigating it
(`PeerDeadline` binding the locked config, and a held session refreshing its
read deadline after the lock). Both are correct on their own merits and are
kept; **neither solves this stall.**

CI keeps it visible rather than hidden: the Windows gating job runs the whole
suite except this one test, and a separate non-gating job
*Windows native exact-six known limitation* runs exactly that test in full view.
The test is not deleted and not `xfail`ed, and on Linux it remains fully gating.

If a future dependency upgrade eliminates it, revalidate then; no work is
scheduled around it now.

## 7. Forbidden concurrency patterns

- Mutating domain state from an I/O callback.
- Two executors, or a background task that writes game state.
- Locks around domain objects as a substitute for the single-executor design.
- Blocking the event loop with synchronous network/LLM calls.
- Letting GUI backpressure stall the game loop.
- Unbounded queues or unbounded retry loops.
