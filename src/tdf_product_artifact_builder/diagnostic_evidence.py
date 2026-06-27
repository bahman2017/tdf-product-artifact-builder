"""Generic diagnostic evidence schema and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.evidence import (
    EvidenceValidationReport,
    load_evidence_json,
    verify_safety_flags,
)


def default_diagnostic_evidence_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "diagnostic_evidence.schema.json"


def load_diagnostic_evidence_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_diagnostic_evidence_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_diagnostic_evidence_payload(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_diagnostic_evidence_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def validate_diagnostic_evidence_file(
    path: str | Path,
    schema_path: str | Path | None = None,
) -> EvidenceValidationReport:
    """Load and validate a generic diagnostic evidence JSON file."""
    errors: list[str] = []
    try:
        payload = load_evidence_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return EvidenceValidationReport(
            evidence_id="",
            source_tool="",
            valid=False,
            safety_flags_passed=False,
            errors=[str(exc)],
        )

    evidence_id = str(payload.get("evidence_id", ""))
    source_tool = str(payload.get("source_tool", ""))

    try:
        validate_diagnostic_evidence_payload(payload, schema_path=schema_path)
    except jsonschema.ValidationError as exc:
        errors.append(str(exc.message))

    safety_errors = verify_safety_flags(payload)
    errors.extend(safety_errors)

    if not payload.get("claim_boundaries", {}).get("claim_boundary_passed", False):
        errors.append("claim_boundary_passed must be true")

    return EvidenceValidationReport(
        evidence_id=evidence_id,
        source_tool=source_tool,
        valid=len(errors) == 0,
        safety_flags_passed=len(safety_errors) == 0,
        errors=errors,
    )


def build_diagnostic_evidence_summary_md(payload: dict[str, Any]) -> str:
    """Build reviewer-facing diagnostic evidence summary markdown."""
    flags = payload.get("diagnostic_flags", payload)
    lines = [
        "# Diagnostic evidence summary",
        "",
        "External diagnostic evidence summary only. No raw payloads copied.",
        "Build trust in the artifact, not belief in the theory.",
        "",
        f"- Evidence ID: `{payload.get('evidence_id', '')}`",
        f"- Evidence type: `{payload.get('evidence_type', '')}`",
        f"- Source tool: `{payload.get('source_tool', '')}`",
        f"- Source version: `{payload.get('source_version', '')}`",
        "",
        "## Safety flags",
        "",
        f"- lammps_input_executed: `{flags.get('lammps_input_executed', False)}`",
        f"- simulation_executed: `{flags.get('simulation_executed', False)}`",
        f"- accepted_for_simulation: `{flags.get('accepted_for_simulation', False)}`",
        f"- force_field_ready: `{flags.get('force_field_ready', False)}`",
        f"- wet_lab_ready: `{flags.get('wet_lab_ready', False)}`",
        "",
        "## Reviewer summary",
        "",
        str(payload.get("reviewer_summary", payload.get("diagnostic_summary", ""))),
        "",
        "## Limitations",
        "",
    ]
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "- Evidence contract validation only.",
            "- No simulation execution.",
            "- No readiness stage upgrade.",
            "",
        ]
    )
    return "\n".join(lines)
