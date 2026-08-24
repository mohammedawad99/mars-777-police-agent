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

**2. The fourteen-artifact assembly has no production caller.** Every component
works and every one is unit-tested: the backends build and contribute both
documents per sub-game, the gateway collects all twelve, the declaration writer
runs at Step-0 merge, the result owner holds the agreed digest, and
`series_assembly.assemble` writes exactly fourteen files or refuses. Nothing
invokes the last of these. Our side wrote its two development contribution files
and stopped.

That is the same class of defect this project has hit before — a writer nothing
calls is not a record, exactly as a guard nothing calls is not a guard — and it
is the one remaining gap on the counted artifact path.

## Not covered

The public ngrok route. `compose_public_gateway` starts a tunnel agent needing a
real credential this run must not use, so the gateway was assembled from the same
production objects and served on loopback. The tunnel stays the runbook's step.
