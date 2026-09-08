# 03 — Caddy reverse proxy (HTTPS)

Human browser access only. Agents do **not** use Caddy for MCP.

## Option A — Caddy binary / simple container (recommended to start)

### DNS

Create an `A` record: `taiga.yourdomain.com` → VPS public IP. Wait for propagation.

### Caddyfile

On the VPS:

```bash
mkdir -p /opt/caddy
cat >/opt/caddy/Caddyfile <<'EOF'
taiga.yourdomain.com {
    reverse_proxy 127.0.0.1:9000
}
EOF
```

### Run Caddy in Docker

```bash
docker run -d --name caddy --restart unless-stopped \
  -p 80:80 -p 443:443 \
  -v /opt/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  -v caddy_data:/data \
  -v caddy_config:/config \
  caddy:2
```

Caddy will obtain Let’s Encrypt certificates automatically.

Verify:

```bash
curl -I https://taiga.yourdomain.com
```

Update Taiga `.env` `TAIGA_SITES_DOMAIN` / `TAIGA_SITES_SCHEME=https` to match, then:

```bash
cd /opt/taiga
docker compose up -d
```

## Option B — caddy-docker-proxy

If you prefer label-driven config ([lucaslorentz/caddy-docker-proxy](https://github.com/lucaslorentz/caddy-docker-proxy)):

1. Run the `caddy-docker-proxy` container with access to the Docker socket.
2. Add labels on the Taiga gateway service (via compose override), e.g. host `taiga.yourdomain.com`.
3. Do **not** attach public labels to the MCP container.

## Done when

- [ ] HTTPS loads the Taiga UI without certificate warnings
- [ ] HTTP→HTTPS redirect works
- [ ] Port 9000 is **not** exposed in UFW (only localhost bind on the host is fine)
