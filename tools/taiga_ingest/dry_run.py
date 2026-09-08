"""Plan ordered pytaiga-mcp workflow tool calls from a validated payload."""

from __future__ import annotations

from typing import Any

HUMAN_REVIEW_BANNER = (
    "WARNING: [HUMAN REVIEW NEEDED] — THIS TICKET WAS GENERATED FROM "
    "UNDERSPECIFIED INPUT AND REQUIRES HUMAN REVIEW FOR ACCURACY BEFORE WORK BEGINS."
)


def plan_mcp_operations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a deterministic ordered list of mock MCP operations.

    Apply order (matches implementation plan):
    1. Sprints (plan_sprint — create milestone; stories assigned via create_story)
    2. Epics (create_epic)
    3. Stories (create_story — link epic, optional sprint)
    4. Tasks (break_down_story)

    Tool names match pytaiga-mcp *workflow* mode.
    """
    project = payload["project_slug"]
    ops: list[dict[str, Any]] = []

    for sprint in payload.get("sprints", []):
        ops.append(
            {
                "tool": "plan_sprint",
                "args": {
                    "project": project,
                    "name": sprint["name"],
                    "estimated_start": sprint["estimated_start"],
                    "estimated_finish": sprint["estimated_finish"],
                    "stories": [],
                    "note": (
                        "Create the sprint first with no stories. "
                        "Stories reference this sprint by name in create_story."
                    ),
                },
            }
        )

    for epic in payload.get("epics", []):
        ops.append(
            {
                "tool": "create_epic",
                "args": {
                    "project": project,
                    "subject": epic["subject"],
                    "description": epic["description"],
                    "temp_id": epic["temp_id"],
                },
            }
        )

        for story in epic.get("stories", []):
            description = story["description"]
            if (
                story.get("needs_human_review")
                and "[HUMAN REVIEW NEEDED]" not in description
            ):
                description = HUMAN_REVIEW_BANNER + "\n\n" + description

            create_args: dict[str, Any] = {
                "project": project,
                "subject": story["subject"],
                "description": description,
                "epic": epic["temp_id"],
                "temp_id": story["temp_id"],
            }
            if story.get("points") is not None:
                create_args["points"] = story["points"]
            if story.get("sprint_name"):
                create_args["sprint"] = story["sprint_name"]

            ops.append({"tool": "create_story", "args": create_args})

            task_subjects = [
                {
                    "subject": t["subject"],
                    "description": t.get("description", ""),
                    "temp_id": t["temp_id"],
                }
                for t in story.get("tasks", [])
            ]
            ops.append(
                {
                    "tool": "break_down_story",
                    "args": {
                        "project": project,
                        "story_ref": story["temp_id"],
                        "tasks": task_subjects,
                        "note": (
                            "Replace story_ref temp_id with the Taiga ref "
                            "returned by create_story when applying live."
                        ),
                    },
                }
            )

    return ops


def render_dry_run_markdown(payload: dict[str, Any], ops: list[dict[str, Any]]) -> str:
    lines = [
        "# Taiga ingest dry-run plan",
        "",
        f"**Project:** `{payload['project_slug']}`",
        "",
        f"**Summary:** {payload.get('summary', '')}",
        "",
    ]
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    review_stories = [
        s["temp_id"]
        for e in payload.get("epics", [])
        for s in e.get("stories", [])
        if s.get("needs_human_review")
    ]
    if review_stories:
        lines.append("## Human review flags")
        lines.append("")
        lines.append(
            "Stories marked `needs_human_review`: "
            + ", ".join(f"`{r}`" for r in review_stories)
        )
        lines.append("")

    lines.append("## Hierarchy")
    lines.append("")
    for epic in payload.get("epics", []):
        lines.append(f"- **Epic {epic['temp_id']}:** {epic['subject']}")
        for story in epic.get("stories", []):
            flag = " ⚠️ HUMAN REVIEW" if story.get("needs_human_review") else ""
            sprint = story.get("sprint_name") or "(backlog)"
            lines.append(
                f"  - **Story {story['temp_id']}:** {story['subject']} "
                f"[{story.get('points', 0)} pts → {sprint}]{flag}"
            )
            for task in story.get("tasks", []):
                lines.append(f"    - **Task {task['temp_id']}:** {task['subject']}")
    lines.append("")
    lines.append("## Ordered MCP operations (pytaiga-mcp workflow mode)")
    lines.append("")
    for index, op in enumerate(ops, start=1):
        lines.append(f"{index}. `{op['tool']}`")
        for key, value in op["args"].items():
            lines.append(f"   - **{key}:** `{value}`")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "_Dry-run only. No network calls were made. "
        "Await human clearance before applying via MCP._"
    )
    lines.append("")
    return "\n".join(lines)
