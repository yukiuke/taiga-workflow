"""Tests for payload schema and semantic validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.taiga_ingest.validate import (
    PayloadValidationError,
    validate_file,
    validate_payload,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_payload_passes() -> None:
    payload = validate_file(FIXTURES / "valid_payload.json")
    assert payload["project_slug"] == "demo-app"
    assert len(payload["epics"]) == 1


def test_invalid_schema_payload_fails() -> None:
    with pytest.raises(PayloadValidationError, match="Schema validation failed"):
        validate_file(FIXTURES / "invalid_schema_payload.json")


def test_invalid_semantic_payload_fails() -> None:
    with pytest.raises(PayloadValidationError, match="Semantic validation failed"):
        validate_file(FIXTURES / "invalid_semantic_payload.json")


def test_schema_only_skips_semantic() -> None:
    raw = json.loads((FIXTURES / "invalid_semantic_payload.json").read_text())
    # Still fails schema? No — invalid_semantic should pass schema.
    validate_payload(raw, semantic=False)


def test_missing_human_review_banner_fails() -> None:
    payload = json.loads((FIXTURES / "valid_payload.json").read_text())
    story = payload["epics"][0]["stories"][0]
    story["needs_human_review"] = True
    story["description"] = (
        "As noted.\n\n## Acceptance Criteria\n\n- [ ] Something happens"
    )
    with pytest.raises(PayloadValidationError, match="human-review banner"):
        validate_payload(payload)
