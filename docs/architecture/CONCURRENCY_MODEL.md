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
2. **Turn cursor guard** — every inbound message carries `(sub_game, step, phase)`. The
   state machine accepts it **only** if it matches the expected cursor. Anything else is
   `E-PROTO-STALE` (duplicate/replayed/out-of-order) and is rejected, not queued.
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

## 6. Forbidden concurrency patterns

- Mutating domain state from an I/O callback.
- Two executors, or a background task that writes game state.
- Locks around domain objects as a substitute for the single-executor design.
- Blocking the event loop with synchronous network/LLM calls.
- Letting GUI backpressure stall the game loop.
- Unbounded queues or unbounded retry loops.
