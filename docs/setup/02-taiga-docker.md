# 02 — Taiga Docker

Uses the official [taigaio/taiga-docker](https://github.com/taigaio/taiga-docker) **stable** branch.

## 1. Clone on the VPS

```bash
cd /opt/taiga
git clone https://github.com/taigaio/taiga-docker.git .
git checkout stable
```

## 2. Configure `.env`

```bash
cp .env.example .env   # if present; otherwise edit the provided .env
chmod 600 .env
```

Set at least:

| Variable | Guidance |
|----------|----------|
| `TAIGA_SECRET_KEY` | Long random string (`openssl rand -hex 32`) |
| `TAIGA_SITES_DOMAIN` | `taiga.yourdomain.com` (no scheme) |
| `TAIGA_SITES_SCHEME` | `https` once Caddy is in front |
| Postgres / Rabbit / Redis passwords | Change all defaults |

For first bring-up **before** DNS/Caddy works, you may temporarily use:

```env
TAIGA_SITES_DOMAIN=localhost:9000
TAIGA_SITES_SCHEME=http
```

…then flip to your public domain + `https` and recreate front/gateway containers (see Taiga docs).

## 3. Start the stack

```bash
cd /opt/taiga
docker compose up -d
docker compose ps
```

Wait until gateway/front are healthy. Local check on the VPS:

```bash
curl -I http://127.0.0.1:9000
```

## 4. Create admin / project / bot user

1. Open Taiga in a browser (via SSH tunnel if Caddy not ready yet):

   ```bash
   # On your laptop:
   ssh -i ~/.ssh/vps_taiga_key -L 9000:127.0.0.1:9000 deploy@YOUR_VPS_IP
   # Visit http://localhost:9000
   ```

2. Complete initial admin setup if prompted.
3. Create a **project** (note its **slug**, e.g. `demo-app`).
4. Create a dedicated user for agents, e.g. `agent-bot`, with membership on that project (role that can create epics/stories/tasks/sprints).
5. Store the bot username/password for [04-taiga-mcp.md](04-taiga-mcp.md) (password manager + VPS env file).

## 5. API URL for MCP

Inside Docker, MCP should call the **internal** API URL (not the public Caddy URL), typically something like:

```text
http://taiga-gateway:80
```

or whatever service name the compose file uses for the API gateway. Discover:

```bash
docker network ls
docker compose -f /opt/taiga/docker-compose.yml ps
docker inspect "$(docker compose -f /opt/taiga/docker-compose.yml ps -q gateway | head -1)" | head
```

If MCP runs on the **same compose network**, prefer the internal hostname. If you only expose the gateway on host port 9000, MCP can use `http://172.17.0.1:9000` or `http://host.docker.internal:9000` depending on the engine — prefer attaching MCP to Taiga’s compose network (documented in step 04).

## Done when

- [ ] `curl -I http://127.0.0.1:9000` returns success on the VPS
- [ ] You can log in, see a project, and know its slug
- [ ] `agent-bot` can create backlog items manually in the UI
