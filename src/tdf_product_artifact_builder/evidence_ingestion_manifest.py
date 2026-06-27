"""Evidence ingestion manifest builder and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.evidence import REQUIRED_SAFETY_FLAGS


def default_evidence_ingestion_manifest_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "evidence_ingestion_manifest.schema.json"


def load_evidence_ingestion_manifest_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_evidence_ingestion_manifest_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence_ingestion_manifest(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_evidence_ingestion_manifest_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def build_evidence_ingestion_manifest(
    *,
    source_directory: str,
    accepted_entries: list[dict[str, Any]],
    rejected_count: int,
) -> dict[str, Any]:
    """Build EVIDENCE_INGESTION_MANIFEST.json from accepted ingestion entries."""
    accepted = sorted(accepted_entries, key=lambda item: item["relative_path"])
    checksums = {entry["relative_path"]: entry["file_sha256"] for entry in accepted}
    return {
        "manifest_version": "1.0",
        "source_directory": source_directory,
        "accepted_count": len(accepted),
        "rejected_count": rejected_count,
        "accepted_entries": accepted,
        "checksums": checksums,
        "diagnostic_flags": dict(REQUIRED_SAFETY_FLAGS),
        "simulation_authorized": False,
        "wet_lab_ready": False,
    }


def load_evidence_ingestion_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate an evidence ingestion manifest JSON file."""
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Evidence ingestion manifest root must be a JSON object.")
    validate_evidence_ingestion_manifest(payload)
    return payload
