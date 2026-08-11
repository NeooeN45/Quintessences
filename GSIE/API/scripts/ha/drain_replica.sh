#!/usr/bin/env sh
set -eu

replica="${1:-}"
case "$replica" in
  api-ha-a|api-ha-b) ;;
  *)
    echo "Usage : $0 api-ha-a|api-ha-b" >&2
    exit 2
    ;;
esac

drain_file="${GSIE_GRACEFUL_DRAIN_FILE:-/tmp/gsie-draining}"
drain_wait_seconds="${GSIE_HA_DRAIN_WAIT_SECONDS:-3}"
stop_grace_seconds="${GSIE_HA_STOP_GRACE_SECONDS:-45}"

docker exec "$replica" touch "$drain_file"
sleep "$drain_wait_seconds"

ready_code="$(
  docker exec "$replica" python -c \
    "import urllib.error, urllib.request
try:
    print(urllib.request.urlopen('http://localhost:8000/ready').status)
except urllib.error.HTTPError as exc:
    print(exc.code)"
)"

if [ "$ready_code" != "503" ]; then
  echo "Refus d'arrêter : le replica répond encore $ready_code sur /ready" >&2
  exit 1
fi

docker stop --time "$stop_grace_seconds" "$replica" >/dev/null
echo "$replica retiré puis arrêté proprement"
