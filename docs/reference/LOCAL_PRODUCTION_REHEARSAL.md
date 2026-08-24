# Local independent-process production rehearsal

Four processes, real FastMCP HTTP across real process boundaries, run against
the exact current build. **Uncounted.** Fake secrets only. No report sent.

This is `LOCAL_PRODUCTION_REHEARSAL`, not a real-peer proof: the opponent here is
a reference sparring peer, not s82kma9e's production runner.

| process | repository | port | role |
|---|---|---|---|
| group gateway | police | 8810 public, 8813 admin | routes; decides nothing |
| police backend | police | 8811 | plays g01, g03, g05 |
| thief backend | thief | 8812 | plays g02, g04, g06 |
| reference peer | published kit | 8931 | plays the other side |

## What passed

- Authenticated Step-0, six alternating sub-games, six mutual audits.
- The peer logged all six as `audit OK` and wrote its own 14 artifacts.
- **All 12 per-sub-game official documents reached the gateway** — six configs
  and six logs, queried back through the admin surface after the run.
- All six settled rows collected.

## What it found — the reason a rehearsal exists

**1. The public route answered before it could route anything.** The first run
died at sub-game 1: the peer saw port 8810 open, sent its greeting, and the
gateway returned `E-LOCAL-DEFECT` because no backend existed to forward to. The
peer gave up; our backends, which dial the peer at startup, then found nothing to
dial and exited on `E-TRANSPORT`. A counted run is protected by the runner-ready
handshake, but the local harness had nothing equivalent. The gateway now serves
its admin surface first, waits for both backend ports, and opens the public gate
only then — so the rehearsal cannot pass for the wrong reason.

**2. The fourteen-artifact assembly had no production caller.** Every component
worked and every one was unit-tested — the backends build and contribute both
documents per sub-game, the gateway collects all twelve, the declaration writer
runs at Step-0 merge, the result owner holds the agreed digest, and
`series_assembly.assemble` writes exactly fourteen files or refuses. Nothing
invoked the last of these, so our side wrote its two development contribution
files and stopped. A writer nothing calls is not a record, exactly as a guard
nothing calls is not a guard.

## Fixed, and re-run in counted mode — the official set reaches disk

```
official artifacts : 14   (1 declaration, 6 config, 6 log, 1 result)
development files  :  1   (friendly contribution — outside the official set)
consensus digest   : 482d0d0a320b82074c5d7d9936360d61b448adbe24c0008c8a9901421626519f
peer logged        : 482d0d0a320b82074c5d7d9936360d61b448adbe24c0008c8a9901421626519f
```

The result carries six sub-games, `cumulative` cop 30 / thief 60 with outcome
`thief`, and `declaration_ref` naming the declaration written at Step-0 merge.
`log_g06` holds 140 entries with `peer_chain_reproduces: true` over 35 records
each side. Every config artifact carries its three sections — the agreed core,
the nonce-bound `terms_agreement`, and the scent-model evidence.

## Two harness facts, so this is not read as more than it is

The harness merges the peer's half of the declaration itself, because it runs no
Step-0 receiver; production learns the merged declaration from
`compose_gateway._step0_receiver`. And the launch document names the real
opponent while the process answering is the reference peer, so `game_id` and the
`teams` entry disagree on the peer's name.

Neither is a production defect. Both are why this is `LOCAL_PRODUCTION_REHEARSAL`
and not a real-peer proof.

## Not covered

The public ngrok route. `compose_public_gateway` starts a tunnel agent needing a
real credential this run must not use, so the gateway was assembled from the same
production objects and served on loopback. The tunnel stays the runbook's step.
