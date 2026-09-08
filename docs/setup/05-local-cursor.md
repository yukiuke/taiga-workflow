# 05 — Local Cursor configuration

## 1. Clone / open this repo

```bash
git clone <your-fork-or-remote> taiga-agentic-workflow
cd taiga-agentic-workflow
cursor .
```

Project skills under `.cursor/skills/` and the rule `.cursor/rules/taiga-ingest.mdc` load with the workspace.

## 2. Python tooling (dry-run / validate)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## 3. MCP config

```bash
cp .mcp.json.example .mcp.json
```

Edit `.mcp.json`:

- Replace `YOUR_VPS_IP_OR_HOSTNAME`
- Confirm key path `~/.ssh/vps_taiga_key`
- Confirm `docker exec` command matches [04-taiga-mcp.md](04-taiga-mcp.md)

Reload MCP servers in Cursor (Command Palette → “MCP: Restart” / reload window).

Verify the `taiga` server shows tools such as `create_story`, `create_epic`, `plan_sprint`, `break_down_story`.

## 4. First ingest (dry-run only)

1. Open a new Agent chat in this repo.
2. Paste sample notes from [../fixtures/sample-discord-notes.md](../fixtures/sample-discord-notes.md) (or your own).
3. Ask: **Run ingest-requirements for project_slug `demo-app` (dry-run only).**
4. Expect automated Passes 1→2→3 writing under `.ai/`, then a summary + pause.
5. Locally confirm:

```bash
python -m tools.taiga_ingest validate .ai/taiga_payload.json
python -m tools.taiga_ingest dry-run .ai/taiga_payload.json -o .ai/dry_run_plan.md
```

6. Only when ready: reply **apply to Taiga** so the orchestrator uses MCP write tools per [../mcp-tool-mapping.md](../mcp-tool-mapping.md).

## 5. Troubleshooting

| Symptom | Check |
|---------|--------|
| MCP server fails to start | SSH key perms (`chmod 600`), `AllowUsers deploy`, docker group |
| Auth errors from Taiga | Bot password in `/opt/taiga-mcp/.env`, project membership |
| Empty tool list | Wrong `server_workflow.py` path; try `docker exec -it taiga-mcp ls` |
| Validate fails | Read schema errors; re-run Product Owner pass only if human re-triggers |

## Done when

- [ ] Cursor lists Taiga MCP tools
- [ ] Dry-run ingest produces `.ai/taiga_payload.json` + `.ai/dry_run_plan.md`
- [ ] You understand that apply requires an explicit second clearance
