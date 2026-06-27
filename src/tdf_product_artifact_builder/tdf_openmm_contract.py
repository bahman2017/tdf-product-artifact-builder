"""tdf-openmm-validation integration contract (schemas and validators only)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.claim_boundaries import scan_text_for_forbidden_claims
from tdf_product_artifact_builder.evidence import (
    EvidenceValidationReport,
    compute_payload_checksum,
    load_evidence_json,
    verify_safety_flags,
)

TDF_OPENMM_VALIDATION_SOURCE_TOOL = "tdf-openmm-validation"


@dataclass(frozen=True)
class TdfOpenmmContractReport:
    evidence_id: str
    valid: bool
    schema_valid: bool
    safety_flags_passed: bool
    claim_boundary_passed: bool
    errors: list[str] = field(default_factory=list)


def default_tdf_openmm_evidence_schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "schemas"
        / "tdf_openmm_validation_evidence.schema.json"
    )


def load_tdf_openmm_evidence_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_tdf_openmm_evidence_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_tdf_openmm_evidence_payload(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_tdf_openmm_evidence_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def adapt_tdf_openmm_to_diagnostic_evidence(
    payload: dict[str, Any],
    *,
    evidence_path: str | Path,
) -> dict[str, Any]:
    """Adapt tdf-openmm-validation evidence to generic diagnostic evidence contract."""
    path = Path(evidence_path)
    checksum = compute_payload_checksum(payload)
    return {
        "evidence_id": str(payload["evidence_id"]),
        "evidence_type": str(payload["evidence_type"]),
        "source_tool": TDF_OPENMM_VALIDATION_SOURCE_TOOL,
        "source_version": str(payload["source_version"]),
        "source_repository": str(payload.get("source_repository", "")),
        "source_commit": str(payload.get("source_commit", "")),
        "created_at": "1970-01-01T00:00:00Z",
        "input_artifacts": [path.name],
        "diagnostic_flags": {
            "lammps_input_executed": False,
            "simulation_executed": False,
            "accepted_for_simulation": False,
            "force_field_ready": False,
            "wet_lab_ready": False,
        },
        "claim_boundaries": {
            "claim_boundary_passed": bool(payload.get("claim_boundary_passed", False)),
            "allowed_claims": [
                "diagnostic preparation metadata",
                "static validation package reference",
            ],
            "forbidden_claims": [
                "simulation-ready membrane",
                "force-field-ready",
                "wet-lab-ready product",
            ],
        },
        "limitations": list(payload.get("limitations", [])),
        "reviewer_summary": str(payload.get("diagnostic_summary", "")),
        "evidence_files": [{"relative_path": path.name, "sha256": checksum}],
        "checksums": {
            "algorithm": "sha256",
            "files": [{"relative_path": path.name, "sha256": checksum}],
        },
    }


def validate_tdf_openmm_evidence_file(
    path: str | Path,
    schema_path: str | Path | None = None,
) -> TdfOpenmmContractReport:
    """Validate tdf-openmm-validation evidence without importing that package."""
    errors: list[str] = []
    schema_valid = True
    safety_flags_passed = False
    claim_boundary_passed = False

    try:
        payload = load_evidence_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return TdfOpenmmContractReport(
            evidence_id="",
            valid=False,
            schema_valid=False,
            safety_flags_passed=False,
            claim_boundary_passed=False,
            errors=[str(exc)],
        )

    evidence_id = str(payload.get("evidence_id", ""))

    try:
        validate_tdf_openmm_evidence_payload(payload, schema_path=schema_path)
    except jsonschema.ValidationError as exc:
        schema_valid = False
        errors.append(str(exc.message))

    safety_errors = verify_safety_flags(payload)
    safety_flags_passed = len(safety_errors) == 0
    errors.extend(safety_errors)

    summary_text = str(payload.get("diagnostic_summary", ""))
    forbidden_hits = scan_text_for_forbidden_claims(summary_text)
    claim_boundary_passed = bool(payload.get("claim_boundary_passed", False)) and not forbidden_hits
    if forbidden_hits:
        errors.append(f"Forbidden claims in diagnostic_summary: {forbidden_hits}")
    if not payload.get("claim_boundary_passed", False):
        errors.append("claim_boundary_passed must be true")

    return TdfOpenmmContractReport(
        evidence_id=evidence_id,
        valid=len(errors) == 0,
        schema_valid=schema_valid,
        safety_flags_passed=safety_flags_passed,
        claim_boundary_passed=claim_boundary_passed,
        errors=errors,
    )
