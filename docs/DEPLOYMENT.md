# Ambient Guard — Deployment (meow server)

Runtime: Fedora 43 · Docker 29.6.2 + Compose · nginx (host) · deployed 2026-09-07.

## Topology
```
Internet ──▶ nginx (host, :80/:443 or a dedicated port)
                └─▶ 127.0.0.1:18080  ── ambient-guard-backend-1 (FastAPI/uvicorn :8080)
                                          └─ ambient-guard-db-1 (postgres:16, internal :5432)
```
- Compose project name: `ambient-guard` (isolated from the ~10 other containers on the host).
- Backend host port **127.0.0.1:18080** (localhost only — nginx is the sole public entry). Postgres has no host port.

## Deploy / update (no root needed)
```bash
bash deploy_meow.sh        # clones/pulls the repo, writes .env, docker compose -p ambient-guard up -d --build
# health: curl -fsS http://127.0.0.1:18080/health  ->  {"status":"ok","bee_mode":"mock"}
```
`.env` on the server sets `AMBIENT_GUARD_BEE_MODE=mock` for now (the server has no `bee login`).
To run live Bee on the server, install `@beeai/cli`, run `bee login` as the container's host user,
switch the backend to `cli` mode, and mount the Bee credential path into the container (future work; see R1).

## nginx (requires sudo — run yourself; do NOT send the sudo password in chat)

Public hostname: **bee.andywongpt.com** → reverse proxy to 127.0.0.1:18080.

### Path C — Tailscale Serve / Funnel (USED for this deploy; no DNS, no certbot, no port-forward)
The `meow` node is on a tailnet (`mouse-great.ts.net`) with Tailscale + Funnel enabled, and
provisions a valid TLS cert automatically. The `meow` user is a Tailscale operator, so no sudo:
```bash
# tailnet-only HTTPS at the app root on a dedicated port:
tailscale serve --bg --https 8446 http://127.0.0.1:18080
#   -> https://meow-server.mouse-great.ts.net:8446/   (tailnet devices only)

# PUBLIC via Funnel — Funnel allows only 443/8443/8444/8445 (all otherwise in use here),
# so expose Ambient Guard as a PATH on the existing 443 Funnel (UI is path-relative):
tailscale funnel --bg --set-path /ambient-guard http://127.0.0.1:18080
#   -> https://meow-server.mouse-great.ts.net/ambient-guard   (public)

tailscale serve status
tailscale serve --https=8446 off      # remove a mount
```
Do NOT put a Tailscale IP (100.64.0.0/10, e.g. 100.111.98.103) in public DNS — those are
tailnet-only and not routable from the internet.

### Prerequisites
1. **DNS** at your registrar: `A  bee.andywongpt.com → 60.53.214.8` (server IPv4)
   and/or `AAAA → 2001:e68:540e:1523:6a1d:efff:fe4f:c0d5`. Verify: `dig +short bee.andywongpt.com`.
2. **Ports 80 + 443 reachable from the internet** to this host. If `60.53.214.8` is a
   home/CGNAT IP without port-forwarding, Let's Encrypt HTTP-01 will fail — use the
   Cloudflare Tunnel fallback below instead.

### Path A — nginx + Let's Encrypt (public IP with 80/443 open)
```bash
cd ~/ambient-guard
sudo cp deploy/nginx/ambient-guard.conf /etc/nginx/conf.d/ambient-guard.conf
sudo nginx -t && sudo systemctl reload nginx
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d bee.andywongpt.com --redirect -m you@andywongpt.com --agree-tos -n
sudo systemctl reload nginx
# then: https://bee.andywongpt.com
```

### Path B — Cloudflare Tunnel (home/CGNAT IP; no port-forward, TLS handled by CF)
```bash
# one-time: install cloudflared, then
cloudflared tunnel login
cloudflared tunnel create ambient-guard
# route DNS (creates the CNAME in Cloudflare automatically):
cloudflared tunnel route dns ambient-guard bee.andywongpt.com
# run (points the hostname at the local app):
cloudflared tunnel run --url http://127.0.0.1:18080 ambient-guard
# (persist with a systemd service for production)
```
With Path B, no nginx vhost or certbot is needed — Cloudflare terminates TLS and
tunnels to 127.0.0.1:18080. Requires the domain to be on Cloudflare.

### Old dedicated-port option (no domain)
See git history; the template previously used `listen 18090;` with `server_name _`.

## Manage
```bash
docker compose -p ambient-guard ps
docker compose -p ambient-guard logs -f backend
docker compose -p ambient-guard down          # stop (keeps pgdata volume)
```

## Health & restart
- Backend + db have healthchecks; both use `restart: unless-stopped`.
- json-file logging with rotation (10m ×3).
