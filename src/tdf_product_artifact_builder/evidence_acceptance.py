"""Evidence acceptance report builder and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.evidence import REQUIRED_SAFETY_FLAGS


def default_evidence_acceptance_report_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "evidence_acceptance_report.schema.json"


def load_evidence_acceptance_report_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_evidence_acceptance_report_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence_acceptance_report(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_evidence_acceptance_report_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def build_evidence_acceptance_report(
    *,
    source_directory: str,
    accepted_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build EVIDENCE_ACCEPTANCE_REPORT.json from accepted ingestion entries."""
    accepted = sorted(accepted_entries, key=lambda item: item["relative_path"])
    return {
        "report_version": "1.0",
        "source_directory": source_directory,
        "accepted_count": len(accepted),
        "accepted": accepted,
        "diagnostic_flags": dict(REQUIRED_SAFETY_FLAGS),
        "simulation_authorized": False,
        "wet_lab_ready": False,
    }
