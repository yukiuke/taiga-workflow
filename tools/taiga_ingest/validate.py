"""Load and validate Taiga ingest payloads against the JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "schemas" / "taiga_payload.schema.json"

HUMAN_REVIEW_BANNER = (
    "WARNING: [HUMAN REVIEW NEEDED] — THIS TICKET WAS GENERATED FROM "
    "UNDERSPECIFIED INPUT AND REQUIRES HUMAN REVIEW FOR ACCURACY BEFORE WORK BEGINS."
)


class PayloadValidationError(ValueError):
    """Raised when a payload fails schema or semantic checks."""


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    path = schema_path or DEFAULT_SCHEMA_PATH
    data = load_json(path)
    if not isinstance(data, dict):
        raise PayloadValidationError(f"Schema at {path} must be a JSON object")
    return data


def _format_schema_errors(errors: list[Any]) -> str:
    lines = []
    for err in sorted(errors, key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        lines.append(f"- {path}: {err.message}")
    return "\n".join(lines)


def validate_semantic(payload: dict[str, Any]) -> list[str]:
    """Return semantic issues (empty list means OK)."""
    issues: list[str] = []
    sprint_names = {s["name"] for s in payload.get("sprints", [])}

    epic_ids: set[str] = set()
    story_ids: set[str] = set()
    task_ids: set[str] = set()

    for epic in payload.get("epics", []):
        eid = epic["temp_id"]
        if eid in epic_ids:
            issues.append(f"Duplicate epic temp_id: {eid}")
        epic_ids.add(eid)

        for story in epic.get("stories", []):
            sid = story["temp_id"]
            if sid in story_ids:
                issues.append(f"Duplicate story temp_id: {sid}")
            story_ids.add(sid)

            sprint_name = story.get("sprint_name")
            if sprint_name is not None and sprint_name not in sprint_names:
                issues.append(
                    f"Story {sid} references unknown sprint_name: {sprint_name!r}"
                )

            if story.get("needs_human_review") and HUMAN_REVIEW_BANNER not in story.get(
                "description", ""
            ):
                issues.append(
                    f"Story {sid} has needs_human_review=true but description "
                    f"is missing the ALL-CAPS human-review banner"
                )

            subject = story.get("subject", "")
            if not (
                "as a" in subject.lower()
                and "i want" in subject.lower()
                and "so that" in subject.lower()
            ):
                issues.append(
                    f"Story {sid} subject should follow "
                    f"'As a... I want... So that...' format"
                )

            description = story.get("description", "")
            if "- [ ]" not in description and "* [ ]" not in description:
                issues.append(
                    f"Story {sid} description should include markdown "
                    f"checkbox acceptance criteria (- [ ])"
                )

            for task in story.get("tasks", []):
                tid = task["temp_id"]
                if tid in task_ids:
                    issues.append(f"Duplicate task temp_id: {tid}")
                task_ids.add(tid)

    capacity = payload.get("velocity", {}).get("sprint_capacity_points", 0)
    if capacity > 0 and payload.get("sprints"):
        points_by_sprint: dict[str, float] = {name: 0.0 for name in sprint_names}
        for epic in payload.get("epics", []):
            for story in epic.get("stories", []):
                name = story.get("sprint_name")
                if name and name in points_by_sprint:
                    points_by_sprint[name] += float(story.get("points") or 0)
        for name, total in points_by_sprint.items():
            if total > capacity:
                issues.append(
                    f"Sprint {name!r} assigned {total} points exceeds "
                    f"capacity {capacity}"
                )

    return issues


def validate_payload(
    payload: dict[str, Any],
    *,
    schema_path: Path | None = None,
    semantic: bool = True,
) -> None:
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        raise PayloadValidationError(
            "Schema validation failed:\n" + _format_schema_errors(errors)
        )
    if semantic:
        issues = validate_semantic(payload)
        if issues:
            raise PayloadValidationError(
                "Semantic validation failed:\n" + "\n".join(f"- {i}" for i in issues)
            )


def validate_file(
    payload_path: Path,
    *,
    schema_path: Path | None = None,
    semantic: bool = True,
) -> dict[str, Any]:
    payload = load_json(payload_path)
    if not isinstance(payload, dict):
        raise PayloadValidationError("Payload must be a JSON object")
    validate_payload(payload, schema_path=schema_path, semantic=semantic)
    return payload
