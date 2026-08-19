# Match runbook — MaRs-777

For a **development friendly** against a real partner. Counted play is not yet
available: see the two open items at the end.

## Before the match

**Repositories**

- [ ] both repos clean, on `main`, `HEAD == origin/main` (`git status`, `git ls-remote`)
- [ ] the exact SHAs you intend to play are the ones pushed
- [ ] CI green for those exact SHAs
- [ ] no local edit "just for the match" — a source edit mid-series invalidates the run

**Secrets and environment** (never printed, never committed)

- [ ] `MARS777_ROLE`, `MARS777_BIND_HOST`, `MARS777_BIND_PORT`, `MARS777_KEY_ID`,
      `MARS777_AUTH_SECRET`, `MARS777_ARTIFACT_ROOT`, `MARS777_OPPONENT_ENDPOINT` set
- [ ] the ngrok agent installed and its authtoken configured in the agent's own config
- [ ] launch document ready, including the `kit_terms` the pairing agreed

**Agreed with the partner, before anything starts**

- [ ] their `group_id`
- [ ] their public endpoint
- [ ] **who takes which side in sub-game 1** — alternation makes g01 decide all six
- [ ] the fourteen flat terms, byte-exact (a float differing only in `repr` breaks the signature)
- [ ] six sub-games, `REFERENCE_ODD_EVEN_ALTERNATION`, thief moves first each sub-game
- [ ] *(counted only, later)* the keyed Step-0 arrangement — see the pairing handoff
- [ ] *(counted only, later)* how the two final result digests will be exchanged

**Start, in this order**

1. Police backend, in the police repo:
   `uv run python -m mars777_police.kit_backend_main --launch <doc> --port <private> --opponent <their public url> --gateway-admin http://127.0.0.1:<admin>/mcp --first-role <police|thief>`
2. Thief backend, in the thief repo, same shape with its own private port.
3. The group front door, in either repo:
   `uv run python -m mars777_police.kit_gateway_main --police-endpoint <private> --thief-endpoint <private> --ngrok <path> --first-role <police|thief>`
4. Read the **public endpoint** off the banner and send it to the partner. It is
   discovered fresh every run; never reuse yesterday's.

## During the match

- Do **not** edit strategy, source or configuration.
- Do **not** restart the tunnel unless the match is being abandoned — the endpoint
  changes and the partner is left dialling a dead route.
- Watch only: the readiness lines, the routed sub-game, and settlement.
- If a sub-game disagrees between the two sides, stop and record it. Do not
  "fix" it mid-series.

## After the match

- [ ] preserve the development evidence directory before anything else
- [ ] merge the two role contributions into the one series document
- [ ] compare audits both ways: did each side's chain reproduce for the other?
- [ ] compare settlements row by row — six agreements, or a recorded disagreement
- [ ] stop the gateway (Ctrl-C); confirm the tunnel and both backends are gone
- [ ] **do not label the run counted.** It is `KIT_FRIENDLY_ONLY`, and it stays that way
- [ ] review before scheduling the next series

## Still open before counted play

1. **Keyed Step-0 authentication** — the partner must agree to carry a keyed proof;
   the exact non-secret contract is in `KIT_PAIRING_HANDOFF.md`.
2. **Result-digest exchange** — the pinned four-tool wire has no operation that can
   carry it, so it needs an agreed extension.
