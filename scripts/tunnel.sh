#!/usr/bin/env bash
# Cloudflare Tunnel for judges (prompt 7.4). Usage: scripts/tunnel.sh quick|named|token|stop
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-quick}"

if [[ "$mode" == "quick" ]]; then
  if docker compose ps --status running --services 2>/dev/null | grep -qx tunnel; then
    echo "WARNING: a quick tunnel is already running. Restarting it would change the address and break" >&2
    echo "saved phone sign-ins, offline cases and every Telegram link already sent. Not restarting." >&2
  else
    docker compose --profile tunnel up -d tunnel
  fi
  url=""
  for _ in $(seq 1 30); do
    url="$(docker compose --profile tunnel logs tunnel 2>&1 | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1 || true)"
    [[ -n "$url" ]] && break
    sleep 2
  done
  [[ -n "$url" ]] || { echo "No tunnel address yet; check: docker compose --profile tunnel logs tunnel" >&2; exit 1; }
elif [[ "$mode" == "stop" ]]; then
  docker compose --profile tunnel --profile tunnel-named --profile tunnel-token stop tunnel tunnel-named tunnel-token
  sed -i.bak -E "s#^PUBLIC_BASE_URL=.*#PUBLIC_BASE_URL=#" .env && rm -f .env.bak
  docker compose up -d api >/dev/null
  echo "Public links stopped; case links point at this laptop again."
  exit 0
elif [[ "$mode" == "token" ]]; then
  grep -qE '^TUNNEL_TOKEN=[^[:space:]#]+' .env || { echo "Set TUNNEL_TOKEN in .env first (see HOW_TO_RUN.md)." >&2; exit 1; }
  docker compose --profile tunnel-token up -d tunnel-token
  url="https://$(grep -E '^TUNNEL_HOSTNAME=' .env | cut -d= -f2 | sed 's/#.*//' | tr -d '[:space:]')"
  [[ "$url" != "https://" ]] || { echo "Set TUNNEL_HOSTNAME in .env to the tunnel's public hostname." >&2; exit 1; }
else
  [[ -f deploy/cloudflared/config.yml ]] || { echo "Copy deploy/cloudflared/config.example.yml to config.yml first." >&2; exit 1; }
  docker compose --profile tunnel-named up -d tunnel-named
  url="https://$(grep -E '^TUNNEL_HOSTNAME=' .env | cut -d= -f2 | tr -d '[:space:]')"
fi

sed -i.bak -E "s#^PUBLIC_BASE_URL=.*#PUBLIC_BASE_URL=${url}#" .env && rm -f .env.bak
docker compose up -d api >/dev/null
echo "Public link: ${url} (written to PUBLIC_BASE_URL; api restarted so case links use it)"
