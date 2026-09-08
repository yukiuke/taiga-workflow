"""Tests for dry-run MCP operation planning."""

from __future__ import annotations

import json
from pathlib import Path

from tools.taiga_ingest.dry_run import plan_mcp_operations, render_dry_run_markdown
from tools.taiga_ingest.validate import validate_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_plan_order_is_sprints_epics_stories_tasks() -> None:
    payload = validate_file(FIXTURES / "valid_payload.json")
    ops = plan_mcp_operations(payload)
    tools = [op["tool"] for op in ops]

    assert tools[0] == "plan_sprint"
    assert tools.count("plan_sprint") == 1
    assert tools.count("create_epic") == 1
    assert tools.count("create_story") == 2
    assert tools.count("break_down_story") == 2

    # After the sprint op: epic, then for each story create + break_down
    assert tools[1] == "create_epic"
    assert tools[2] == "create_story"
    assert tools[3] == "break_down_story"
    assert tools[4] == "create_story"
    assert tools[5] == "break_down_story"


def test_create_story_includes_sprint_and_review_banner() -> None:
    payload = validate_file(FIXTURES / "valid_payload.json")
    ops = plan_mcp_operations(payload)
    login = next(
        op for op in ops if op["tool"] == "create_story" and op["args"]["temp_id"] == "US1"
    )
    assert login["args"]["sprint"] == "Sprint 1"
    assert "[HUMAN REVIEW NEEDED]" in login["args"]["description"]
    assert login["args"]["epic"] == "E1"


def test_break_down_includes_all_tasks() -> None:
    payload = validate_file(FIXTURES / "valid_payload.json")
    ops = plan_mcp_operations(payload)
    breakdown = next(
        op
        for op in ops
        if op["tool"] == "break_down_story" and op["args"]["story_ref"] == "US1"
    )
    subjects = [t["subject"] for t in breakdown["args"]["tasks"]]
    assert subjects == ["Add login API endpoint", "Wire login form to API"]


def test_render_dry_run_markdown_contains_summary() -> None:
    payload = validate_file(FIXTURES / "valid_payload.json")
    ops = plan_mcp_operations(payload)
    md = render_dry_run_markdown(payload, ops)
    assert "demo-app" in md
    assert "Ordered MCP operations" in md
    assert "US1" in md
    assert "Dry-run only" in md


def test_cli_dry_run_writes_output(tmp_path: Path) -> None:
    from tools.taiga_ingest.cli import main

    out = tmp_path / "plan.md"
    code = main(
        [
            "dry-run",
            str(FIXTURES / "valid_payload.json"),
            "-o",
            str(out),
        ]
    )
    assert code == 0
    assert out.exists()
    assert "plan_sprint" in out.read_text()
