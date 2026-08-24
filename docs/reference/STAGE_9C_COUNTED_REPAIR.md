# Stage 9C — the alternating counted series reports itself

**Status: RELEASED.** An alternating counted series now completes its result
agreement over the pinned wire and reports itself automatically, exactly once.

## What was broken, established before anything changed

A real counted series against `s82kma9e` on `92ff04b5…` / `16d3e910…` completed
six sub-games, six mutual audits and a genuine bidirectional settlement, and
wrote exactly fourteen official artifacts. **The lecturer was never mailed.**
Appendix E rule 35 scores a missing report **0 for both groups**.

Two counted-capable paths existed and they were disjoint:

| | fixed-role | alternating |
|---|---|---|
| entry | `__main__` → `compose_series` → `AutonomousBoot` → `SeriesDriver` | `kit_gateway_main --counted` + two `kit_backend_main` |
| plays alternation? | **no** — `SeriesDriver.role` is fixed for all six, and `kit_schedule.owned_by` / `require_ours` are called only from `kit_backend.py` | **yes** — the agreed `REFERENCE_ODD_EVEN_ALTERNATION` |
| result writer | `artifact_documents.result_document` — carries the three reporting members | `kit_result_document` — carries none of them |
| reports? | **yes**, `SeriesDriver._report` | **no reporter existed in the gateway at all** |

`kit_backend_main` being `KIT_FRIENDLY_ONLY` was a **symptom, not the cause**:
even a counted-capable backend would not have mailed anything, because reporting
was never wired into the gateway. Counted-ness legitimately belongs to the
gateway — it is the only process that holds the whole series, which is why
`series_result_owner` exists.

## A wrong turn, recorded because it matters

An intermediate version of this stage mapped **"the peer's wire carries no token
field"** to **"the peer reported 0"**, behind a constant named
`REPORTED_WHEN_UNREPORTED`. That was wrong on the contract and worse in effect:

- `sub_games[].tokens` are **participant-owned**. Each side contributes its own
  six values inside its own `ResultContribution`; `total_tokens` is their sum.
  Manufacturing the peer's half asserts a value the peer never authored.
- It **hid a real protocol gap** — the one described below — behind a plausible
  default, and would have produced a reportable-looking result for a series
  whose result no peer had agreed.

It is removed: the constant, every code path that substituted zero, every test
that read a missing field as a reported zero, and every line of
`RESULT_CONTRACT.md` / `COUNTED_RUNBOOK.md` that said so.

## The gap, stated plainly

`ResultAgreement` already travels on a **public** tool, with no ninth family and
no fifth tool:

```
TOOL_KINDS["receive_control"] == ("result_agreement",)          envelopes.py:130
client.py:144   call("receive_control","result_agreement",…) -> Sha256Digest
router.py:77    -> operations.on_result_agreement(...)
server.py       receive_control(...) -> str      # 64 lowercase hex
```

That carriage exists on the **internal** `STRICT_PROJECT` surface only. On
`TransportEnvelopeProfile.KIT_EXTERNAL`, `build_kit_tools` registers
`receive_control(message) -> {"ok": true}` — *"a status signal. It touches no
game state and settles nothing."* No contribution in, no digest back.

**That was the gap.** Against a peer on the pinned KIT wire the two
contributions could not be exchanged, so the `RESULT_APPROVAL_CORE` could not be
built and the series could never become reportable - the open item
`KIT_PAIRING_HANDOFF.md` already listed as needing partner agreement.

Stage 9C closes it by making the **existing** `result_agreement` kind reachable
on `KIT_EXTERNAL` too. See `PEER_RESULT_AGREEMENT_EXTENSION.md` for what a
partner must implement.

## The repair, as shipped

| file | what it does |
|---|---|
| `transport/kit_control_envelope.py` | tells the two `receive_control` forms apart by the `kind` the pinned message already carries |
| `transport/call_arguments.py` | `arguments_for()` builds the one shared kind per profile; the strict rendering is byte-identical to before |
| `app/kit_contribution_entries.py` | admits a backend's entry only if the schedule owns the sub-game and the commit matches the role played |
| `app/kit_backend_contribution.py` | the backend's participant-owned half: commit played, tokens from `TokenAccountingPort` |
| `app/kit_result_agreement.py` | the group's single agreement authority, assembled late, with the bounded readiness wait |
| `compose_result_agreement.py` | builds the one `ResultExchange` from parts the gateway already holds |
| `compose_series_writer.py` | renders the reporting members only from `is_agreed`; the official set waits for the agreement |

Four public tools. Nine kinds. No new family.

## The readiness race — a real cross-peer condition

The four-process rehearsal produced it: a correct, authenticated request reached
a receiver still publishing its sixth contribution entry, because both sides
finish sub-game six at different moments and the proposer sends immediately.

Handled as production semantics, not a harness sleep: wait boundedly on the
agreed watchdog for our own half, then process the **same** request; suspend
rather than spin; on timeout refuse with an explicit retryable not-ready error
and mutate nothing; answer a replay idempotently. Malformed and unauthenticated
requests never wait - the envelope is parsed and the sender authenticated first.

## Phase F — LOCAL_COMPATIBILITY_HARNESS rehearsal

Four independent processes over real KIT_EXTERNAL FastMCP: gateway (counted,
loopback), police backend, thief backend, and the pinned sparring peer taught
the same extension. The mail transport is a sink; `MARS777_GMAIL_TOKEN` unset.

```
COUNTED_ALTERNATION = PASS   SUB_GAMES = 6/6   MUTUAL_AUDITS = 6/6
SERIES_SETTLEMENT   = PASS   OUR_CONTRIBUTION = 6/6   PEER_CONTRIBUTION = 6/6
OUR_RESULT_SHA256   = 4e0a7ae8b1660738236069e8bb7dac0bab02631018a1b4cc16fa7736b2ccc1cd
PEER_RESULT_SHA256  = 4e0a7ae8b1660738236069e8bb7dac0bab02631018a1b4cc16fa7736b2ccc1cd
RESULT_APPROVAL_CORE_MATCH = YES     RESULT_SHA256_MATCH = YES
MUTUAL_AGREEMENT = true
SERIES_CONSENSUS_SHA256 = 482d0d0a...   RESULT_SHA256_IS_DISTINCT_AUTHORITY = YES
TOTAL_TOKENS = {"MaRs-777": 0, "sparring-s82kma9e": 207}
REPORTED_BY = MaRs-777       OFFICIAL_ARTIFACTS = 14/14
NORMAL_REPORT_ELIGIBILITY = PASS
AUTO_REPORT_TRIGGERED = YES  AUTO_REPORT_SEND_COUNT = 1
REAL_LECTURER_EMAIL_SENT = NO
LEGACY_KIT_STATUS_CONTROL = PASS     TOOL_ERRORS_IN_RUN = 0
```

`total_tokens` is **asymmetric** - 0 from our accounting authority, 207 from the
peer's own ledger. Both halves are participant-owned; neither is manufactured.

## What Phase F does and does not prove

**Does.** Two separately running processes, over the real wire, exchange the
agreement in both directions and derive a byte-identical approval core and
digest. The peer's arithmetic lives in a module that shares **no code** with the
`mars777_*` packages.

**Does not.** It is **not independent external evidence** - the peer is our own
adaptation of the pinned sparring kit. And because that kit implements no keyed
Step-0, the harness pre-binds the inbound session, so the run does **not**
exercise the authentication gate. That gate is proven by unit test: an
unauthenticated `result_agreement` is refused outright.

Independent proof comes from the next real peer. `PEER_RESULT_AGREEMENT_EXTENSION.md`
is what they need.

## Preserved from Stage 9C

- the alternating gateway owns whole-series assembly
- `result_sha256` and `series_consensus_sha256` remain two distinct facts
- `mutual_agreement` only from genuine agreement
- `reported_by` from the existing group authority
- the normal report eligibility gate, never bypassed
- automatic reporter wiring, exactly-once delivery
- the fake/sink mail transport rehearsal harness

## The completed s82kma9e series is untouched

Its fourteen artifacts and its manual delivery evidence are preserved exactly as
they were. Nothing in this stage rewrote, re-reported or re-derived them.
