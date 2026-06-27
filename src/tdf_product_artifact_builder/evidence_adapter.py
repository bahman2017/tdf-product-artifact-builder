"""Unified evidence validation and adaptation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tdf_product_artifact_builder.diagnostic_evidence import validate_diagnostic_evidence_payload
from tdf_product_artifact_builder.evidence import load_evidence_json
from tdf_product_artifact_builder.tdf_openmm_contract import (
    TDF_OPENMM_VALIDATION_SOURCE_TOOL,
    adapt_tdf_openmm_to_diagnostic_evidence,
    validate_tdf_openmm_evidence_file,
)


def validate_and_adapt_evidence(path: str | Path) -> dict[str, Any]:
    """Validate evidence file and return generic diagnostic evidence contract dict."""
    evidence_path = Path(path)
    payload = load_evidence_json(evidence_path)
    source_tool = str(payload.get("source_tool", ""))

    if source_tool == TDF_OPENMM_VALIDATION_SOURCE_TOOL:
        report = validate_tdf_openmm_evidence_file(evidence_path)
        if not report.valid:
            raise ValueError(f"Invalid tdf-openmm-validation evidence: {'; '.join(report.errors)}")
        adapted = adapt_tdf_openmm_to_diagnostic_evidence(payload, evidence_path=evidence_path)
        validate_diagnostic_evidence_payload(adapted)
        return adapted

    raise ValueError(f"Unsupported evidence source_tool: {source_tool!r}")
