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
```bash
sudo cp deploy/nginx/ambient-guard.conf /etc/nginx/conf.d/ambient-guard.conf
# edit listen/server_name/TLS as desired
sudo nginx -t && sudo systemctl reload nginx
```
The bundled `deploy/nginx/ambient-guard.conf` proxies a chosen public port to 127.0.0.1:18080.
Pick a free host port (18090 is a suggested default; verify with `ss -tln`) or add a server_name + TLS block.

## Manage
```bash
docker compose -p ambient-guard ps
docker compose -p ambient-guard logs -f backend
docker compose -p ambient-guard down          # stop (keeps pgdata volume)
```

## Health & restart
- Backend + db have healthchecks; both use `restart: unless-stopped`.
- json-file logging with rotation (10m ×3).
