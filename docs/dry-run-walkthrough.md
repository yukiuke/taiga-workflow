# Dry-run E2E walkthrough

This walkthrough verifies the **local** half of the pipeline (skills + CLI) without a live Taiga apply. Use it for debugging prompts, schema, and dry-run ordering.

## Prerequisites

```bash
cd /path/to/taiga-agentic-workflow
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

Expected: all tests pass.

## Path A — Agent ingest (preferred)

1. Open this repo in Cursor.
2. Start a new Agent chat.
3. Paste the contents of [fixtures/sample-discord-notes.md](fixtures/sample-discord-notes.md).
4. Send:

   > Run the **ingest-requirements** skill for `project_slug` `demo-app` with velocity **10**. Dry-run only — do not apply to Taiga.

5. Confirm the orchestrator:
   - Saves `.ai/raw_notes.md`
   - Spawns Architect → writes `.ai/draft_spec.md`
   - Spawns Challenger → writes `.ai/audit_report.md` (with `confidence_score`)
   - Spawns Product Owner → writes `.ai/taiga_payload.json`
   - Runs validate + dry-run
   - Prints a brief summary and **pauses**

6. In a terminal:

```bash
python -m tools.taiga_ingest validate .ai/taiga_payload.json
python -m tools.taiga_ingest dry-run .ai/taiga_payload.json -o .ai/dry_run_plan.md
less .ai/dry_run_plan.md
```

### What good looks like

| Check | Expectation |
|-------|-------------|
| Epics | Themes such as Authentication, Admin export, Notifications (may vary) |
| Stories | `As a… I want… So that…` + `- [ ]` AC |
| Sprints | A near-term sprint with login/logout; export may be backlog or later |
| Review flags | Vague items (e.g. “remember for a week”, “activity” CSV) likely `needs_human_review` or warnings |
| Dry-run order | `plan_sprint`* → `create_epic` → (`create_story` → `break_down_story`)* |

7. Reply **stop** (EOL) or, only with MCP configured, **apply to Taiga**.

## Path B — CLI-only dry-run (no agent)

Useful when debugging the planner without burning tokens:

```bash
python -m tools.taiga_ingest dry-run tests/fixtures/valid_payload.json -o .ai/dry_run_plan.md
```

Open `.ai/dry_run_plan.md` and confirm:

1. First op is `plan_sprint` for `Sprint 1`
2. Then `create_epic` for auth
3. `create_story` for `US1` includes `[HUMAN REVIEW NEEDED]` and `sprint: Sprint 1`
4. `break_down_story` lists both login tasks
5. Footer states dry-run only / await human clearance

## Path C — Intentional failure (semantic)

```bash
python -m tools.taiga_ingest validate tests/fixtures/invalid_semantic_payload.json
```

Expected: non-zero exit, messages about story format / AC / banner / capacity.

## Artifact tree after a full agent dry-run

```text
.ai/
  raw_notes.md
  draft_spec.md
  audit_report.md
  taiga_payload.json
  dry_run_plan.md
```

If a ticket looks wrong later in Taiga, inspect this folder first (Architect → Challenger → PO).

## Optional live smoke (not default)

1. Complete [setup/README.md](setup/README.md).
2. Use a **throwaway** Taiga project slug.
3. After dry-run review, say **apply to Taiga**.
4. Verify epics/stories/tasks/sprints in the UI; save `.ai/apply_result.json`.
5. Delete the throwaway project when finished.
