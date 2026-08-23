# Counted / rehearsal runbook — MaRs-777

Not executed. Order matters; three of these steps come from failures actually
observed rather than from caution.

## Preflight

1. **Free the ports by PID.** A stale listener silently costs a whole sub-game —
   the backend fails to bind and that sub-game simply never happens.
   ```bash
   for p in $GATEWAY $POLICE_PORT $THIEF_PORT $ADMIN; do
     pid=$(ss -ltnp | grep ":$p " | grep -oP 'pid=\K[0-9]+' | head -1)
     [ -n "$pid" ] && kill -9 "$pid"
   done
   ```
2. **Read HEAD at launch time** and put those SHAs in the declaration:
   ```bash
   git -C mars-777-police-agent rev-parse HEAD
   git -C mars-777-thief-agent  rev-parse HEAD
   ```
   The frozen interop vector pins *historical* commits by design; the live
   declaration must carry today's. A stale commit fails `check_declared_commit`
   against the peer.
3. **Gates, both repos**: `ruff check` · `ruff format --check` · `mypy --strict src` ·
   `tools/check_python_loc.py` · `tools/check_infrastructure_freeze.py` · `uv build`.
4. **Secrets from the environment only** — `MARS777_AUTH_SECRET` is never in a
   file, a log, an artifact or a declaration.

## Start order — peer first, gateway second, backends last

The backends dial the opponent at startup (`PeerClient.__aenter__`), so anything
they dial must already be listening.

1. Opponent endpoint reachable.
2. **Gateway** (public route + loopback admin). Confirm the banner reports the
   first role read from the frozen contract: `police`.
3. **Both role backends — before g01.** Police plays g01/g03/g05, thief
   g02/g04/g06. Starting one and letting the other arrive late loses the first
   sub-game that backend owns.

## During

- Role collision on `negotiate` → `E-PROTO-STALE` is **correct**: the contract
  gives MaRs-777 police in sub-game 1. Ask the peer to open as thief.
- A dropped backend session is reopened once automatically, and only on a
  transport failure; a backend *refusal* is propagated untouched.

## Settlement — do not kill anything early

- The g06 owner (our **thief**) stays alive for the full 400 s consensus window.
- Both sides send and both verify. `series consensus confirmed: <digest>` on the
  peer and the same digest in our thief contribution's
  `series_consensus_sha256` is the success condition.
- If the window closes with no match, the contribution records **no**
  `series_consensus_sha256`. That is an unsettled series, and it is reported
  honestly rather than papered over.

## After

- Exactly **one** report per group, from the g06 owner, after mutual consensus.
- 14 official artifacts per side.
- Verify: 6 sub-games, 6 mutual audits, one settlement digest agreed by both.

## Not covered by the local rehearsal

The **ngrok public route**. The rehearsal ran the real gateway objects on plain
loopback because a tunnel needs a real credential. The tunnel is the one step
first exercised live, so bring it up and self-probe it before opening the gate.
