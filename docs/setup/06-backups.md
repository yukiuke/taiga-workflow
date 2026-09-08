# 06 — Backups and restore

## What to back up

| Component | Location (typical) | Method |
|-----------|--------------------|--------|
| Postgres data | Taiga compose volume | `pg_dump` |
| Taiga media | media volume | `tar` |
| MCP secrets | `/opt/taiga-mcp/.env` | encrypted copy / password manager |
| Caddy certs | `caddy_data` volume | optional (LE re-issues) |

## Dump script (cron-friendly)

Save as `/opt/backups/taiga/dump.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="/opt/backups/taiga"
KEEP_DAYS=14

mkdir -p "$OUT_DIR"

# Adjust container name to your taiga-docker postgres service:
PG_CONTAINER="$(docker ps --format '{{.Names}}' | grep -E 'postgres|taiga-db' | head -1)"
if [[ -z "${PG_CONTAINER}" ]]; then
  echo "No postgres container found" >&2
  exit 1
fi

docker exec "$PG_CONTAINER" pg_dump -U taiga taiga \
  | gzip > "${OUT_DIR}/taiga-${STAMP}.sql.gz"

# Optional media archive (adjust volume/path)
# docker run --rm -v taiga_taiga-media-data:/data:ro -v "${OUT_DIR}:/backup" alpine \
#   tar czf "/backup/taiga-media-${STAMP}.tar.gz" -C /data .

find "$OUT_DIR" -name 'taiga-*.sql.gz' -mtime +"${KEEP_DAYS}" -delete
echo "Backup written: ${OUT_DIR}/taiga-${STAMP}.sql.gz"
```

```bash
chmod 700 /opt/backups/taiga/dump.sh
```

Cron (daily 03:15 UTC) as `deploy`:

```bash
crontab -e
# add:
15 3 * * * /opt/backups/taiga/dump.sh >> /opt/backups/taiga/dump.log 2>&1
```

## Restore (outline)

1. Stop writers: `cd /opt/taiga && docker compose stop`
2. Start Postgres only if needed.
3. `gunzip -c taiga-YYYYMMDD.sql.gz | docker exec -i "$PG_CONTAINER" psql -U taiga taiga`
4. Start the full stack: `docker compose up -d`
5. Verify UI login and a known epic/story.

Practice restore on a staging VPS before you need it.

## Done when

- [ ] At least one successful dump exists under `/opt/backups/taiga`
- [ ] Cron is installed
- [ ] You have written down the postgres container name that works on your host
