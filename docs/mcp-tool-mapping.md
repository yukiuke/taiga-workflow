# pytaiga-mcp workflow tool mapping

This project uses [tetra-2023/pytaiga-mcp](https://github.com/TETRA-2023/pytaiga-mcp) in **`workflow`** mode (`TAIGA_SERVER_MODE=workflow`, default). Agents apply `.ai/taiga_payload.json` **only after** human clearance, following the ordered plan from:

```bash
python -m tools.taiga_ingest dry-run .ai/taiga_payload.json -o .ai/dry_run_plan.md
```

## Transport (local Cursor → VPS)

Copy [`.mcp.json.example`](../.mcp.json.example) to `.mcp.json` (gitignored):

```json
{
  "mcpServers": {
    "taiga": {
      "command": "ssh",
      "args": [
        "-i",
        "~/.ssh/vps_taiga_key",
        "-T",
        "deploy@YOUR_VPS_IP_OR_HOSTNAME",
        "docker exec -i taiga-mcp python /app/src/server_workflow.py"
      ]
    }
  }
}
```

- MCP stdio is piped over SSH; **do not** publish MCP HTTP/SSE ports on the VPS firewall.
- Taiga credentials live in the **container env** on the VPS (not in the local MCP JSON), see [setup/04-taiga-mcp.md](setup/04-taiga-mcp.md).
- Adjust the `docker exec` command if your image entrypoint path differs; confirm with `docker exec -it taiga-mcp ls /app`.

### Optional: local MCP against remote HTTPS Taiga

For debugging without SSH exec into a container (credentials stay local — less preferred for production):

```json
{
  "mcpServers": {
    "taiga": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TAIGA_API_URL",
        "-e", "TAIGA_USERNAME",
        "-e", "TAIGA_PASSWORD",
        "-e", "TAIGA_SERVER_MODE=workflow",
        "ghcr.io/tetra-2023/pytaiga-mcp:latest"
      ]
    }
  }
}
```

Export `TAIGA_*` in your shell (or use a local `.env` loaded by your process manager). Prefer the SSH pattern for day-to-day use.

## Apply order

| Step | Payload source | MCP tool | Notes |
|------|----------------|----------|-------|
| 1 | `sprints[]` | `plan_sprint` | Create milestone with dates; pass empty `stories` initially. Stories attach via `create_story.sprint`. |
| 2 | `epics[]` | `create_epic` | Map `temp_id` (e.g. `E1`) → returned epic id/ref in memory / `.ai/apply_result.json`. |
| 3 | `epics[].stories[]` | `create_story` | Pass project slug, subject, description, epic (resolved), optional `sprint` name, points if supported. |
| 4 | `stories[].tasks[]` | `break_down_story` | Pass real story **ref** from step 3, not `US*`. |
| 5 | (optional) | `move_to_sprint` | If a story missed sprint assignment at create time. |
| 6 | (optional) | `add_comment` | e.g. link back to ingest run / audit confidence. |

Exact parameter names may vary slightly by pytaiga-mcp version — inspect tool schemas in Cursor’s MCP panel and mirror the dry-run plan’s intent.

## Payload ↔ tool field map

### `plan_sprint`

| Payload | Tool arg (conceptual) |
|---------|------------------------|
| `project_slug` | `project` |
| `sprints[].name` | `name` |
| `sprints[].estimated_start` | `estimated_start` |
| `sprints[].estimated_finish` | `estimated_finish` |

### `create_epic`

| Payload | Tool arg |
|---------|----------|
| `project_slug` | `project` |
| `epics[].subject` | `subject` |
| `epics[].description` | `description` |
| `epics[].temp_id` | Track locally only |

### `create_story`

| Payload | Tool arg |
|---------|----------|
| `project_slug` | `project` |
| `stories[].subject` | `subject` |
| `stories[].description` | `description` (must already include human-review banner when required) |
| parent `epics[].temp_id` | Resolve to epic, then `epic` |
| `stories[].sprint_name` | `sprint` (omit / null → backlog) |
| `stories[].points` | points / estimation field if available |
| `stories[].temp_id` | Track locally only |

### `break_down_story`

| Payload | Tool arg |
|---------|----------|
| `stories[].temp_id` | Resolve to Taiga `story_ref` |
| `tasks[].subject` (+ description) | `tasks` list |
| `tasks[].temp_id` | Track locally only |

## Human-review banner

When `needs_human_review` is true, descriptions must contain:

```text
WARNING: [HUMAN REVIEW NEEDED] — THIS TICKET WAS GENERATED FROM UNDERSPECIFIED INPUT AND REQUIRES HUMAN REVIEW FOR ACCURACY BEFORE WORK BEGINS.
```

The dry-run planner injects this if missing; the Product Owner skill should already include it.

## Apply result artifact

After a live apply, write `.ai/apply_result.json`:

```json
{
  "project_slug": "demo-app",
  "created": {
    "sprints": [{ "name": "Sprint 1", "id": 0 }],
    "epics": [{ "temp_id": "E1", "id": 0, "ref": 0 }],
    "stories": [{ "temp_id": "US1", "id": 0, "ref": 0 }],
    "tasks": [{ "temp_id": "T1", "id": 0, "ref": 0 }]
  },
  "errors": []
}
```

## Read tools (optional, minimal verbosity)

Useful before apply: `get_project_overview`, `browse_backlog`, `session_status`, `get_current_user`. Always pass `verbosity: "minimal"` when supported.

## Out of scope

- `full` server mode (107 CRUD tools) — not required for ingest.
- Bypassing MCP with raw HTTP from the agent — use MCP after the human gate; CLI only validates/plans.
