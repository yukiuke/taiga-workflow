# Setup runbook (manual)

End-to-end instructions to host Taiga on a VPS, expose the UI via Caddy HTTPS, run **pytaiga-mcp** for agents over **SSH stdio**, and connect Cursor from a laptop.

**Estimated time:** ~45–90 minutes the first time.

## Order of operations

| Step | Doc | Outcome |
|------|-----|---------|
| 1 | [01-vps-bootstrap.md](01-vps-bootstrap.md) | Docker, UFW, `deploy` user, hardened SSH |
| 2 | [02-taiga-docker.md](02-taiga-docker.md) | Taiga stack on `localhost:9000` |
| 3 | [03-caddy.md](03-caddy.md) | `https://taiga.yourdomain.com` |
| 4 | [04-taiga-mcp.md](04-taiga-mcp.md) | `taiga-mcp` container (stdio, not public) |
| 5 | [05-local-cursor.md](05-local-cursor.md) | Local `.mcp.json` + first dry-run ingest |
| 6 | [06-backups.md](06-backups.md) | Postgres dump cron + restore notes |

## Architecture reminder

```
[ Cursor LAT ] --SSH stdio--> [ VPS: docker exec taiga-mcp ]
                                    |
                                    +--> Taiga API (Docker network)

[ Browser ] --HTTPS--> [ Caddy ] --> Taiga front/gateway :9000
```

- **Agents** never talk to Caddy for MCP; they use SSH.
- **Firewall** allows only 22, 80, 443 inbound.

## Prerequisites checklist

- [ ] Hostinger (or similar) VPS with a public IPv4
- [ ] Domain DNS `A` record pointing at the VPS (for Caddy TLS)
- [ ] Local machine with `ssh`, Cursor, Python 3.11+
- [ ] This repo cloned locally

## Security defaults (non-negotiable)

From [`.plan/security-recommendations.md`](../.plan/security-recommendations.md):

- Password SSH auth **off**; Ed25519 keys only
- No root SSH login
- MCP **not** bound to a public HTTP port
- Taiga bot password only in VPS container env / secrets files (mode `600`)
