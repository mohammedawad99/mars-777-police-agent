# Local counted rehearsal — full six-sub-game series

The infrastructure checkpoint this project freezes against. It is a **local
rehearsal**, not a counted game: uncounted, fake secrets only, no report sent and
no tag created.

## What was run

Our real two-process group against the reference peer, four processes, real
FastMCP HTTP over loopback:

| process | repository | port | role |
|---|---|---|---|
| group gateway | police | 8810 (public), 8813 (admin) | routes, decides nothing |
| police backend | police | 8811 | plays `g01`, `g03`, `g05` |
| thief backend | thief | 8812 | plays `g02`, `g04`, `g06` |
| reference peer | opponent's published kit | 8931 | plays the other side |

The peer ran with its own published series-consensus extension installed. That
extension is a **wire contract both sides must implement**; no strategy of the
opponent's was read or used. Without it the bare kit never sends
`series_consensus`, and the rehearsal would have proved only that our side waits
out its window and honestly records an unsettled series.

## Result

```
sub-games played      : 6
all peer chains verify: True
alternation correct   : True    police g01/g03/g05, thief g02/g04/g06
exactly one settler   : True
settled digest        : 482d0d0a320b82074c5d7d9936360d61b448adbe24c0008c8a9901421626519f
```

The peer independently logged `series consensus confirmed: 482d0d0a…` — the same
digest our thief backend recorded — reported all six of its audits as
`Verified OK`, and wrote its own 14 artifacts. Every row of ours carries
`peer_chain_reproduces: true`.

The police contribution carries **no** `series_consensus_sha256` and the thief
contribution carries one. That is the reporting-ownership rule holding
structurally rather than by assertion: the side that owns the final sub-game is
the side that settles.

## What the rehearsal found that tests could not

1. **The settlement wiring was never connected.** `compose_role_backend` left
   `contribute` and `series_rows` at their refusal defaults and only `settled`
   was replaced at boot. Every unit test passed because each injected its own
   callables; in production the police backend died the instant it finished
   `g01`. Closed by `KitBackendBoot._wire`, with a test that asserts *which
   object* each member is rather than that one of them works.

2. **A role collision was correctly refused.** The peer opened `g01` as police
   while the frozen contract gives MaRs-777 police; the gateway answered
   `E-PROTO-STALE` instead of playing on.

3. **A stale listener silently costs a whole sub-game.** A leftover process
   holding the thief backend's port made it fail to bind, and `g02` simply never
   happened. Freeing the ports by PID before anything binds is a preflight step,
   not a convenience.

## What this rehearsal does **not** cover

The public route. `compose_public_gateway` also starts an ngrok agent and
advertises a hostname; that needs a real credential this run must not use, so the
gateway was assembled from the same production objects and served on plain
loopback instead. The tunnel remains the runbook's step and is untested here.
