# Counted / rehearsal runbook — MaRs-777

The one document an operator needs. Nothing here requires reconstructing
context from a conversation.

Order matters, and several steps exist because a live run failed on them rather
than because somebody was being careful.

---

## 0. What this run is worth — decide once, up front

`--counted` is the only thing that makes a run counted. Its absence is a
rehearsal, and a rehearsal can never report. Nothing infers the distinction from
a launch document, a secret being present, or an endpoint answering.

| | rehearsal | counted |
|---|---|---|
| flag | *(omit)* | `--counted` |
| banner run class | `KIT_FRIENDLY_ONLY` | `COUNTED_CAPABLE` |
| final report | never sent | exactly one, after mutual consensus |

---

## 1. Commit hashes

**Ours, at the time this runbook was written:**

- police `621eb1ced16aa5693772e56106590172ebc51aca`
- thief  `09848e5353e891f1c71f3ed7fedeb1a6960a6427`

**Read HEAD again at launch** and put *those* values in the declaration. The
frozen interop vector pins historical commits by design; the live declaration
must carry today's, or the peer's `check_declared_commit` refuses us.

```bash
git -C mars-777-police-agent rev-parse HEAD
git -C mars-777-thief-agent  rev-parse HEAD
```

**Peer commits — `RECONFIRM_WITH_PEER_BEFORE_LAUNCH`.** Last recorded:
police `6bbe1b3bc52c204abc5be4e510e022d72fdc1401`,
thief `f9b8a79bcea3ca82358d2eab44d0a23c405b6a3d`.
These are a coordination record, not an authority. Ask before pinning.

Before any real launch, for **both** repositories:
`HEAD == origin/main == git ls-remote`, clean worktree, empty index, no
untracked files.

---

## 2. Credentials — names only, values never

Environment variable **names** this system reads:

- `MARS777_KEY_ID`
- `MARS777_AUTH_SECRET`
- `MARS777_GMAIL_TOKEN` *(reporting only)*
- `MARS777_ROLE`, `MARS777_BIND_HOST`, `MARS777_BIND_PORT`
- `MARS777_ARTIFACT_ROOT`, `MARS777_OPPONENT_ENDPOINT`

Rules that are not negotiable:

- The rehearsal secret is **rehearsal-only**. A counted run takes a fresh secret
  and preferably a distinct `MARS777_KEY_ID`.
- Never in a file under version control, a log, an artifact or a declaration.
- Provision by sourcing a gitignored env file **in the same shell** that launches
  the process. A process started in another shell does not have it.
- If a secret ever travels in cleartext — email, chat — treat it as burned and
  rotate before the counted run.

---

## 3. Preflight

```bash
# a) free ports by PID, never by pattern: pkill -f matches your own shell
for p in $GATEWAY_PORT $POLICE_PORT $THIEF_PORT $ADMIN_PORT; do
  pid=$(ss -ltnp | grep ":$p " | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "$pid" ] && kill -9 "$pid"
done

# b) gates, both repositories
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src
uv run python tools/check_python_loc.py
uv run python tools/check_infrastructure_freeze.py
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
uv build

# c) reporting readiness — contacts nobody, sends nothing
uv run python -m mars777_police.gmail_preflight
```

---

## 4. Start order — peer, gateway, backends

The backends dial the opponent at startup (`PeerClient.__aenter__`), so
whatever they dial must already be listening. This ordering is not stylistic:
starting a backend against a dead origin exits it immediately.

1. **Opponent endpoint reachable.** `curl -o /dev/null -w '%{http_code}'` — a
   `406` is correct and means auth-required, not broken.
2. **Build the launch document**, then start the **gateway**. The gateway process
   must be *newer* than the launch file it reads; an older process serves stale
   config and produces `E-CONFIG-MISMATCH` that looks like a value disagreement
   and is not.
3. **Public tunnel up, then self-probe your own public URL.** The declared
   `mcp_endpoint` must equal the ingress actually opened — the launcher refuses
   the route otherwise, which is the guard that exists because a placeholder
   endpoint once reached a peer.
4. **Both role backends, before g01.** Police plays g01/g03/g05, thief
   g02/g04/g06. Starting one and letting the other arrive late loses the first
   sub-game that backend owns.
5. Exchange **runner ready** with the peer, then Step-0.

---

## 5. During the series

- **Step-0 once per series**, authenticated. A redelivered Step-0 is expected —
  the peer retries — and is idempotent.
- **Role collision** on `negotiate` returning `E-PROTO-STALE` is *correct*: the
  contract gives MaRs-777 police in sub-game 1. Ask the peer to open as thief.
- **A disowned session is re-established once**, automatically, and only when the
  peer states it has no such session. Any other transport failure stays terminal
  and is never replayed — whether a commitment arrived is unknowable.
- After each sub-game: one config document and one log document reach the
  gateway. Twelve by the end.

## Checkpoints, per sub-game

| after | expect |
|---|---|
| greeting | routed to the backend the schedule names |
| play | outcome recorded, chain sealed |
| audit | peer chain reproduces; `peer_chain_reproduces: true` |
| row | contributed to the group |
| documents | `config_<game_id>_gNN.json`, `log_<game_id>_gNN.json` |

---

## 6. Settlement — kill nothing early

- The **g06 owner** (our thief, under the current alternation) stays alive for
  the full **400 s** window, retrying every **2 s**.
- Both directions must complete: our envelope positively acknowledged **and** a
  matching one received. One direction is not half a settlement; it is none.
- Success condition: the same `series_consensus_sha256` on both sides.
- No match by the window's close → the series is **unsettled** and recorded
  honestly. Rule 35 scores that 0 for both groups; a result file is not written.

---

## 7. Artifacts — exactly fourteen

| file | when written | count |
|---|---|---|
| `declaration_<game_id>.json` | at Step-0 merge | 1 |
| `config_<game_id>_gNN.json` | per sub-game | 6 |
| `log_<game_id>_gNN.json` | per sub-game | 6 |
| `result_<game_id>.json` | after mutual consensus | 1 |

Proven locally end to end: a four-process rehearsal in counted mode wrote all
fourteen and reached the same consensus digest as the peer — see
`LOCAL_PRODUCTION_REHEARSAL.md`. The gateway writes the set when the last part
lands, whichever part that is; no step in this runbook triggers it by hand.

Reporting-delivery evidence is **outside** the official fourteen. A set that is
short is refused whole rather than written partially.

---

## 8. Reporting — counted only

- Recipient: `rmisegal+uoh26finalgame@gmail.com`
- Exactly **one** report per group, from the g06 owner, **after** six sub-games,
  the required audits, and mutual consensus.
- Attachment-only MIME: one `application/json` leaf named
  `result_<game_id>.json`. No `text/plain`, no `text/html`, no prose body.
- `429` is backed off and retried within the agreed bound.
- A second send for the same game is refused durably.

---

## 9. Shutdown

1. Confirm the consensus digest matches on both sides.
2. Confirm fourteen artifacts.
3. Confirm the report was sent **once** (counted) or **not at all** (rehearsal).
4. Stop backends, then the gateway, then the tunnel.

## Emergency stop

Stop immediately, before anything irreversible, if:

- the declared endpoint does not match the ingress actually opened;
- the peer's commits differ from what was pinned;
- Step-0 fails authentication;
- a run intended as a rehearsal reports `COUNTED_CAPABLE`;
- the consensus digests disagree.

Preserve the logs and artifact directory as evidence, reset to a fresh artifact
root, and diagnose before relaunching. Every live blocker so far was found this
way.
