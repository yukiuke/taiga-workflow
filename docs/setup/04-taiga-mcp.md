# 04 — Taiga MCP container (stdio / SSH)

Run [pytaiga-mcp](https://github.com/TETRA-2023/pytaiga-mcp) on the VPS **without** publishing ports. Cursor reaches it via:

```text
ssh … 'docker exec -i taiga-mcp python /app/src/server_workflow.py'
```

## 1. Secrets file

```bash
cat >/opt/taiga-mcp/.env <<'EOF'
TAIGA_API_URL=http://taiga-gateway:80
TAIGA_USERNAME=agent-bot
TAIGA_PASSWORD=replace-with-strong-password
TAIGA_SERVER_MODE=workflow
TAIGA_TRANSPORT=stdio
LOG_LEVEL=INFO
EOF
chmod 600 /opt/taiga-mcp/.env
```

Set `TAIGA_API_URL` to the **Docker-network** hostname of Taiga’s API/gateway (see [02-taiga-docker.md](02-taiga-docker.md)). Wrong URL is the most common failure mode.

## 2. Attach to Taiga’s network

```bash
# List networks used by Taiga
docker inspect "$(docker ps --filter name=gateway -q | head -1)" \
  --format '{{json .NetworkSettings.Networks}}'
```

Note the network name (often like `taiga_taiga`).

## 3. Run the MCP container (long-lived, no ports)

```bash
docker pull ghcr.io/tetra-2023/pytaiga-mcp:latest

docker rm -f taiga-mcp 2>/dev/null || true

docker run -d --name taiga-mcp --restart unless-stopped \
  --network taiga_taiga \
  --env-file /opt/taiga-mcp/.env \
  --entrypoint sleep \
  ghcr.io/tetra-2023/pytaiga-mcp:latest \
  infinity
```

> Why `sleep infinity`? The image entrypoint expects to own stdio for one MCP session. Keeping the container alive lets `docker exec -i` start a **fresh** workflow server per Cursor session without exposing SSE/HTTP.

Confirm the server path inside the image (adjust if needed):

```bash
docker exec taiga-mcp ls -la /app /app/src 2>/dev/null || docker exec taiga-mcp ls -la /
docker exec taiga-mcp which python
```

If the workflow server lives elsewhere (e.g. `/usr/local/bin/...`), update `.mcp.json` accordingly.

### Alternative: `docker run -i` per session (no long-lived container)

Cursor can SSH to:

```bash
docker run -i --rm --network taiga_taiga --env-file /opt/taiga-mcp/.env \
  ghcr.io/tetra-2023/pytaiga-mcp:latest
```

That also works; use either pattern consistently.

## 4. Smoke-test over SSH from your laptop

```bash
ssh -i ~/.ssh/vps_taiga_key -T deploy@YOUR_VPS_IP \
  'docker exec -i taiga-mcp python /app/src/server_workflow.py' \
  </dev/null
```

You may see MCP initialize waiting on stdio (hang without a client) — that indicates the process started. Cancel with Ctrl+C.

## 5. Firewall check

```bash
sudo ufw status
# Must NOT show 8000/tcp or other MCP ports publicly
```

## Done when

- [ ] Container `taiga-mcp` is running on the Taiga Docker network
- [ ] `.env` is mode `600` and uses the bot user
- [ ] No MCP port is published (`docker port taiga-mcp` empty)
- [ ] SSH `docker exec -i … server_workflow.py` starts
