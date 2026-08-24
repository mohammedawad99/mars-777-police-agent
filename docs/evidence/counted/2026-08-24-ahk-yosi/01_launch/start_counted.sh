#!/usr/bin/env bash
# COUNTED series vs ahk-yosi. Durable artifact root, never /tmp.
set -u
RUN=/home/awad_moha/police-thief-final-2026/counted-evidence/ahk-yosi-counted
POLICE=/home/awad_moha/police-thief-final-2026/mars-777-police-agent
THIEF=/home/awad_moha/police-thief-final-2026/mars-777-thief-agent
EXT=/home/awad_moha/police-thief-final-2026/external-execution
THEIRS=https://zealous-sliver-gleeful.ngrok-free.dev/mcp
OURS=https://exposure-nimble-wackiness.ngrok-free.dev/mcp
NGROK=/home/awad_moha/.local/bin/ngrok

# 1. GAME_START is signed into the declaration; it is not "whenever this ran".
: "${GAME_START:?set GAME_START to the agreed UTC start, e.g. 2026-08-24T19:30:00Z}"

# 2. Credential must exist before anything binds, or the gateway dies on a
#    SettingsError that names only the variable.
CRED=$HOME/.config/mars777/keys/counted-ahk-yosi.env
[ -r "$CRED" ] || { echo "REFUSED: $CRED is unreadable"; exit 1; }

# 3. Free the ports by PID. A stale rehearsal gateway once held the ngrok
#    session and cost a whole diagnosis cycle (COUNTED_RUNBOOK section 1).
for p in 8810 8811 8812 8813 4040; do
  pid=$(ss -ltnp 2>/dev/null | grep ":$p " | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "$pid" ] && { echo "freeing port $p (pid $pid)"; kill -9 "$pid" 2>/dev/null; }
done
sleep 2

# 4. Both repos must be clean and pushed: the declaration names the commit we run.
for r in "$POLICE" "$THIEF"; do
  [ -z "$(git -C "$r" status --porcelain)" ] || { echo "REFUSED: $r is dirty"; exit 1; }
  [ "$(git -C "$r" rev-parse HEAD)" = "$(git -C "$r" rev-parse origin/main)" ] \
    || { echo "REFUSED: $r HEAD != origin/main"; exit 1; }
done

PS=$(git -C "$POLICE" rev-parse HEAD); TS=$(git -C "$THIEF" rev-parse HEAD)
echo "police=$PS"; echo "thief =$TS"

export PEER_GROUP=ahk-yosi PEER_KEY_ID=mars777-ahk-yosi-20260824-02
export PEER_GAME_UID=5ed16f3b-4e6b-4e9d-65bf-8f5abab699f2

( cd "$POLICE" && uv run python "$EXT/build_counted_launch.py" mars777_police "$PS" "$TS" \
    "$OURS" '["Mohamed Awad","Rawey Sleiman"]' "$EXT/kit_terms.json" \
    "$GAME_START" 1 "$RUN/launch_police.json" ) || exit 1
( cd "$THIEF" && uv run python "$EXT/build_counted_launch.py" mars777_thief "$PS" "$TS" \
    "$OURS" '["Mohamed Awad","Rawey Sleiman"]' "$EXT/kit_terms.json" \
    "$GAME_START" 1 "$RUN/launch_thief.json" ) || exit 1

# 5. Prove the run can actually report BEFORE Step-0. This is the check whose
#    absence cost the s82kma9e report (COUNTED_RUNBOOK section 4).
cd "$POLICE"; set -a; . "$CRED"; set +a
MARS777_ROLE=police MARS777_BIND_HOST=127.0.0.1 MARS777_BIND_PORT=8810 \
MARS777_ARTIFACT_ROOT="$RUN/artifacts" MARS777_OPPONENT_ENDPOINT="$THEIRS" \
MARS777_LAUNCH="$RUN/launch_police.json" MARS777_NGROK="$NGROK" uv run python -c "
from pathlib import Path; import os, sys
from mars777_police.compose_series_writer import series_writer
from mars777_police.infra.settings import load_runtime_settings
from mars777_police.app.sealed_record_values import ActorRole
from mars777_police.operator_requests import PublicGatewayRequest
s = load_runtime_settings(os.environ, expected_role=ActorRole.POLICE)
r = PublicGatewayRequest(police_endpoint='http://127.0.0.1:8811/mcp',
    thief_endpoint='http://127.0.0.1:8812/mcp', ngrok=Path(os.environ['MARS777_NGROK']),
    launch=Path(os.environ['MARS777_LAUNCH']), counted=True)
armed = series_writer(s, r) is not None
print('COUNTED_SERIES_WRITER =', 'ARMED' if armed else 'ABSENT')
sys.exit(0 if armed else 1)
" || { echo "REFUSED: writer ABSENT - the run could not report"; exit 1; }

# 6. The gateway binds EPHEMERAL public and admin ports and drives ngrok itself.
#    Read the admin URL off its banner; MARS777_BIND_PORT is not honoured here.
export MARS777_GMAIL_TOKEN=$HOME/.config/mars777/gmail/token.json
MARS777_ROLE=police MARS777_BIND_HOST=127.0.0.1 MARS777_BIND_PORT=8810 \
MARS777_ARTIFACT_ROOT="$RUN/artifacts" MARS777_OPPONENT_ENDPOINT="$THEIRS" \
nohup uv run python -m mars777_police.kit_gateway_main \
  --police-endpoint http://127.0.0.1:8811/mcp --thief-endpoint http://127.0.0.1:8812/mcp \
  --ngrok "$NGROK" --launch "$RUN/launch_police.json" --first-role police \
  --evidence-root "$RUN/evidence" --counted > "$RUN/logs/gateway.log" 2>&1 &
echo "gateway pid $!  (COUNTED)"
