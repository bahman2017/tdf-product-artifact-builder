"""Evidence manifest builder and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.evidence import REQUIRED_SAFETY_FLAGS, compute_payload_checksum


def default_evidence_manifest_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "evidence_manifest.schema.json"


def load_evidence_manifest_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_evidence_manifest_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence_manifest(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_evidence_manifest_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def build_evidence_manifest(
    *,
    product_id: str,
    evidence_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build EVIDENCE_MANIFEST.json from validated evidence payloads."""
    entries: list[dict[str, str]] = []
    for payload in evidence_payloads:
        entries.append(
            {
                "evidence_id": str(payload["evidence_id"]),
                "source_tool": str(payload["source_tool"]),
                "source_version": str(payload["source_version"]),
                "evidence_type": str(payload["evidence_type"]),
                "sha256": compute_payload_checksum(payload),
            }
        )
    entries.sort(key=lambda item: item["evidence_id"])
    return {
        "manifest_version": "1.0",
        "product_id": product_id,
        "evidence_count": len(entries),
        "entries": entries,
        "diagnostic_flags": dict(REQUIRED_SAFETY_FLAGS),
        "simulation_authorized": False,
        "wet_lab_ready": False,
    }
