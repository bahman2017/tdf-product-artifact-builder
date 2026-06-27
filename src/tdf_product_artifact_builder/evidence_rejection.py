"""Evidence rejection report builder and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


def default_evidence_rejection_report_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "evidence_rejection_report.schema.json"


def load_evidence_rejection_report_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_evidence_rejection_report_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence_rejection_report(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_evidence_rejection_report_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def build_evidence_rejection_report(
    *,
    source_directory: str,
    rejected_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build EVIDENCE_REJECTION_REPORT.json from rejected ingestion entries."""
    rejected = sorted(rejected_entries, key=lambda item: item["relative_path"])
    return {
        "report_version": "1.0",
        "source_directory": source_directory,
        "rejected_count": len(rejected),
        "rejected": rejected,
    }
