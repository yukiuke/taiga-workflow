"""CLI entrypoint: validate and dry-run Taiga ingest payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.taiga_ingest.dry_run import plan_mcp_operations, render_dry_run_markdown
from tools.taiga_ingest.validate import PayloadValidationError, validate_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taiga-ingest",
        description="Validate and dry-run Taiga ingest payloads (no live Taiga required).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a payload against the schema")
    validate.add_argument("payload", type=Path, help="Path to taiga_payload.json")
    validate.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Optional path to JSON Schema (defaults to schemas/taiga_payload.schema.json)",
    )
    validate.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip semantic checks (story format, sprint refs, banners)",
    )

    dry = sub.add_parser(
        "dry-run",
        help="Validate then emit an ordered MCP call plan (markdown)",
    )
    dry.add_argument("payload", type=Path, help="Path to taiga_payload.json")
    dry.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write markdown plan to this path (also prints to stdout)",
    )
    dry.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Optional path to JSON Schema",
    )
    dry.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Also print the MCP ops list as JSON to stdout after the markdown",
    )
    dry.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip semantic checks",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            payload = validate_file(
                args.payload,
                schema_path=args.schema,
                semantic=not args.no_semantic,
            )
            epic_count = len(payload.get("epics", []))
            story_count = sum(len(e.get("stories", [])) for e in payload.get("epics", []))
            task_count = sum(
                len(s.get("tasks", []))
                for e in payload.get("epics", [])
                for s in e.get("stories", [])
            )
            print(
                f"OK: {args.payload} — "
                f"{epic_count} epic(s), {story_count} story(ies), {task_count} task(s)"
            )
            if payload.get("warnings"):
                print("Warnings:")
                for warning in payload["warnings"]:
                    print(f"  - {warning}")
            return 0

        if args.command == "dry-run":
            payload = validate_file(
                args.payload,
                schema_path=args.schema,
                semantic=not args.no_semantic,
            )
            ops = plan_mcp_operations(payload)
            markdown = render_dry_run_markdown(payload, ops)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(markdown, encoding="utf-8")
                print(f"Wrote dry-run plan to {args.output}", file=sys.stderr)
            print(markdown)
            if args.as_json:
                print(json.dumps(ops, indent=2))
            return 0

    except PayloadValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
