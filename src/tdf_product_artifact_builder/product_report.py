"""Product report schema and builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.version import __version__


def default_product_report_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "product_report.schema.json"


def load_product_report_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_product_report_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_product_report(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_product_report_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def build_product_report(spec: dict[str, Any]) -> dict[str, Any]:
    """Build PRODUCT_REPORT.json content from a validated product spec."""
    return {
        "product_id": str(spec["product_id"]),
        "product_type": str(spec["product_type"]),
        "target_behavior": str(spec["target_behavior"]),
        "source_artifacts": list(spec.get("source_artifacts", [])),
        "required_diagnostics": list(spec.get("required_diagnostics", [])),
        "allowed_claims": list(spec.get("allowed_claims", [])),
        "forbidden_claims": list(spec.get("forbidden_claims", [])),
        "readiness_stage": str(spec["readiness_stage"]),
        "reviewer_outputs": list(spec.get("reviewer_outputs", [])),
        "external_validation_requirements": list(spec.get("external_validation_requirements", [])),
        "engine_hardcoded": False,
        "simulation_authorized": False,
        "wet_lab_ready": False,
        "openmm_execution": False,
        "lammps_execution": False,
        "builder_version": __version__,
        "package_type": "reviewer_package",
    }
