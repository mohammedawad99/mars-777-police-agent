#!/usr/bin/env bash
# Both role backends for the COUNTED series. The peer's door must already answer:
# each backend opens a session to the opponent at boot and dies on a 502/404.
set -u
RUN=/home/awad_moha/police-thief-final-2026/counted-evidence/ahk-yosi-counted
POLICE=/home/awad_moha/police-thief-final-2026/mars-777-police-agent
THIEF=/home/awad_moha/police-thief-final-2026/mars-777-thief-agent
THEIRS=https://zealous-sliver-gleeful.ngrok-free.dev/mcp
ADMIN=${ADMIN:?set ADMIN to the gateway admin url from its banner}
CRED=$HOME/.config/mars777/keys/counted-ahk-yosi.env

code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$THEIRS")
case "$code" in 502|404|000) echo "REFUSED: peer endpoint is $code - backends would die at boot"; exit 1;; esac
echo "peer answers $code - starting backends"

cd "$POLICE"; set -a; . "$CRED"; set +a
MARS777_ROLE=police MARS777_BIND_HOST=127.0.0.1 MARS777_BIND_PORT=8811 \
MARS777_ARTIFACT_ROOT="$RUN/artifacts-police" MARS777_OPPONENT_ENDPOINT="$THEIRS" \
nohup uv run python -m mars777_police.kit_backend_main \
  --launch "$RUN/launch_police.json" --port 8811 --opponent "$THEIRS" \
  --gateway-admin "$ADMIN" --first-role police --evidence-root "$RUN/evidence" \
  > "$RUN/logs/police.log" 2>&1 &
echo "police pid $!"

cd "$THIEF"; set -a; . "$CRED"; set +a
MARS777_ROLE=thief MARS777_BIND_HOST=127.0.0.1 MARS777_BIND_PORT=8812 \
MARS777_ARTIFACT_ROOT="$RUN/artifacts-thief" MARS777_OPPONENT_ENDPOINT="$THEIRS" \
nohup uv run python -m mars777_thief.kit_backend_main \
  --launch "$RUN/launch_thief.json" --port 8812 --opponent "$THEIRS" \
  --gateway-admin "$ADMIN" --first-role police --evidence-root "$RUN/evidence" \
  > "$RUN/logs/thief.log" 2>&1 &
echo "thief pid $!"
