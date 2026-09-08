---
name: ingest-requirements
description: >-
  Orchestrates the Taiga ingest pipeline from unstructured notes into Epics,
  Stories, Tasks, and Sprints. Use when the user runs /ingest-requirements,
  pastes Discord/chat dumps for ticket creation, or asks to ingest requirements
  into Taiga. Auto-runs Architect → Challenger → Product Owner subagent passes,
  then pauses for human clearance before any Taiga MCP writes.
disable-model-invocation: false
---

# Ingest Requirements (Orchestrator)

Manually triggered, finite workflow. After kickoff, run Passes 1→2→3 **automatically** via subagents with **no human input between passes**. Pause only before Taiga writes.

## Inputs

Collect from the user message (use defaults when omitted):

| Input | Required | Default |
|-------|----------|---------|
| Raw notes / chat dump | Yes | — |
| `project_slug` | No | Ask once if missing |
| Sprint velocity (points) | No | Leave `velocity.notes` explaining assumption |
| Mode | No | `dry-run` until user explicitly says **apply to Taiga** |

## Hard rules

- Do **not** call Taiga MCP write tools until the human explicitly clears apply.
- Do **not** skip passes or merge them into one agent turn.
- Do **not** loop or re-run passes unless the human re-triggers ingest.
- Prefer `verbosity: minimal` on any MCP **read** tools.
- Refuse apply if `python -m tools.taiga_ingest validate` fails.

## Phase 0 — Prepare

1. Ensure `.ai/` exists.
2. Save the raw human input to `.ai/raw_notes.md` (overwrite).
3. Tell the user: passes will run automatically; you will pause with a summary before any writes.

## Phase 1 — Systems Architect (subagent, required)

Dispatch a **fresh subagent** with instructions to follow the `taiga-architect` skill:

- Read `.ai/raw_notes.md` (and any user-supplied project/velocity hints).
- Write **only** to `.ai/draft_spec.md`.
- Return a one-line confirmation when the file is written.

Wait until the file exists and is non-empty. Then proceed immediately to Phase 2.

## Phase 2 — Challenger (subagent, required)

Dispatch a **fresh subagent** with instructions to follow the `taiga-challenger` skill:

- Read `.ai/draft_spec.md`.
- Write **only** to `.ai/audit_report.md` (include `confidence_score` and findings).
- If score &lt; 0.8, ensure `[HUMAN REVIEW NEEDED]` appears in the audit.

Wait until the file exists. Then proceed immediately to Phase 3.

## Phase 3 — Product Owner (subagent, required)

Dispatch a **fresh subagent** with instructions to follow the `taiga-product-owner` skill:

- Read `.ai/draft_spec.md` and `.ai/audit_report.md`.
- Write **only** to `.ai/taiga_payload.json` matching `schemas/taiga_payload.schema.json`.
- Propagate human-review banners when confidence &lt; 0.8 or stories are underspecified.

Wait until the JSON file exists.

## Phase 4 — Validate + dry-run (local CLI)

From the repo root:

```bash
python -m tools.taiga_ingest validate .ai/taiga_payload.json
python -m tools.taiga_ingest dry-run .ai/taiga_payload.json -o .ai/dry_run_plan.md
```

If validate fails: show errors, stop (EOL). Do not call MCP writes.

## Phase 5 — Human gate (mandatory pause)

Show a **brief** summary:

- Project slug
- Counts: epics / stories / tasks / sprints
- Confidence score from the audit (quote it)
- Any `warnings` and stories with `needs_human_review`
- Point to `.ai/dry_run_plan.md`

Then **stop and wait** for explicit human clearance. Options to present:

1. **Stop** — end workflow (EOL)
2. **Dry-run only** — already done; EOL
3. **Apply to Taiga** — proceed to Phase 6 only if the user clearly requests apply

## Phase 6 — Apply via MCP (only after explicit clearance)

1. Re-run validate; abort if invalid.
2. Follow [docs/mcp-tool-mapping.md](../../../docs/mcp-tool-mapping.md) using the ordered ops in `.ai/dry_run_plan.md`.
3. Resolve `temp_id` → real Taiga refs as you create entities.
4. Write results to `.ai/apply_result.json` (created refs, errors if any).
5. Print a short completion summary. **EOL — do not continue into implementation work.**

## EOL

Always end after Phase 5 (if not applying) or Phase 6 (if applying). Never start coding tickets as part of this skill.
