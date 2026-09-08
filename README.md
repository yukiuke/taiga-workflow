# Taiga Agentic Workflow

Manually triggered Cursor workflow that turns unstructured notes into Taiga
Epics, User Stories, Tasks, and Sprints via a three-pass agent chain, then
creates them on a remote Taiga Docker instance through MCP (after a human gate).

## What this does

1. **Human kickoff** — paste Discord/chat notes into `/ingest-requirements` (or ask the agent to run the ingest-requirements skill).
2. **Automated passes** (no human input between passes):
   - Systems Architect → `.ai/draft_spec.md`
   - Challenger → `.ai/audit_report.md` (confidence score; flags vague work)
   - Product Owner → `.ai/taiga_payload.json`
3. **Local validate / dry-run** — schema checks and an ordered MCP call plan (no network).
4. **Human gate** — review the brief summary; then either stop, dry-run only, or apply via Taiga MCP over SSH.

Work-on-tickets / verification agents are **out of scope** for this phase.

## Quick start (local, no VPS required)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Validate a fixture payload
python -m tools.taiga_ingest validate tests/fixtures/valid_payload.json

# Emit a dry-run MCP plan
python -m tools.taiga_ingest dry-run tests/fixtures/valid_payload.json -o .ai/dry_run_plan.md
```

## Cursor usage

1. Copy [`.mcp.json.example`](.mcp.json.example) to `.mcp.json` and point SSH at your VPS (see [docs/setup/](docs/setup/README.md)).
2. Open this repo in Cursor so project skills under `.cursor/skills/` load.
3. Trigger ingest with raw notes; the orchestrator skill auto-runs the three subagent passes, then pauses for clearance before any Taiga writes.

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/setup/README.md](docs/setup/README.md) | Manual VPS + Taiga + Caddy + MCP + local Cursor setup |
| [docs/mcp-tool-mapping.md](docs/mcp-tool-mapping.md) | pytaiga-mcp workflow tools ↔ payload apply order |
| [docs/dry-run-walkthrough.md](docs/dry-run-walkthrough.md) | Sample notes → dry-run E2E |
| [schemas/taiga_payload.schema.json](schemas/taiga_payload.schema.json) | Product Owner output contract |

## Constraints

- Workflows are **manually triggered** and have a defined end of life.
- Never run indefinitely or auto-trigger.
- Underspecified input → agent warning **and** ALL-CAPS `[HUMAN REVIEW NEEDED]` in ticket details.
- Agent traffic uses MCP over **SSH stdio** (no public MCP HTTP port).
