"""Product spec loading and schema validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from tdf_product_artifact_builder.claim_boundaries import validate_claim_boundaries

READINESS_STAGES: tuple[str, ...] = (
    "TDF_DESIGN_CANDIDATE",
    "REVIEWABLE_ATOMIC_BLUEPRINT",
    "DIAGNOSTIC_PREPARATION_PACKAGE",
    "EXTERNAL_REVIEWER_PACKAGE",
    "CONVENTIONAL_VALIDATION_PLAN",
    "CONTROLLED_SIMULATION",
    "WET_LAB_FABRICATION_READINESS",
)

FOUNDATION_MAX_READINESS = "TDF_DESIGN_CANDIDATE"


@dataclass(frozen=True)
class ProductSpecValidationReport:
    product_id: str
    valid: bool
    schema_valid: bool
    claim_boundary_passed: bool
    readiness_within_foundation_limit: bool
    engine_hardcoded: bool
    simulation_authorized: bool
    wet_lab_ready: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def default_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "product_spec.schema.json"


def load_product_spec(path: str | Path) -> dict[str, Any]:
    """Load a product spec YAML file."""
    spec_path = Path(path)
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Product spec root must be a mapping.")
    return payload


def load_product_spec_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    """Load the product spec JSON schema."""
    path = Path(schema_path) if schema_path else default_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_product_spec_schema(
    spec: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    """Validate a product spec dict against the JSON schema. Raises on failure."""
    schema = load_product_spec_schema(schema_path)
    jsonschema.validate(instance=spec, schema=schema)


def validate_product_spec(
    path: str | Path,
    *,
    schema_path: str | Path | None = None,
    max_readiness_stage: str = FOUNDATION_MAX_READINESS,
) -> ProductSpecValidationReport:
    """Load and fully validate a product spec file."""
    spec_path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        spec = load_product_spec(spec_path)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        return ProductSpecValidationReport(
            product_id="",
            valid=False,
            schema_valid=False,
            claim_boundary_passed=False,
            readiness_within_foundation_limit=False,
            engine_hardcoded=True,
            simulation_authorized=True,
            wet_lab_ready=True,
            errors=[str(exc)],
        )

    product_id = str(spec.get("product_id", ""))
    schema_valid = True
    try:
        validate_product_spec_schema(spec, schema_path=schema_path)
    except jsonschema.ValidationError as exc:
        schema_valid = False
        errors.append(str(exc.message))

    claim_report = validate_claim_boundaries(
        allowed_claims=list(spec.get("allowed_claims", [])),
        forbidden_claims=list(spec.get("forbidden_claims", [])),
    )
    if not claim_report.passed:
        errors.extend(f"Forbidden claim: {hit}" for hit in claim_report.forbidden_hits)

    readiness = str(spec.get("readiness_stage", ""))
    stage_index = READINESS_STAGES.index(readiness) if readiness in READINESS_STAGES else -1
    max_index = READINESS_STAGES.index(max_readiness_stage)
    readiness_ok = 0 <= stage_index <= max_index
    if not readiness_ok:
        errors.append(f"readiness_stage {readiness!r} exceeds foundation limit {max_readiness_stage!r}")

    engine_hardcoded = bool(spec.get("engine_hardcoded", True))
    simulation_authorized = bool(spec.get("simulation_authorized", True))
    wet_lab_ready = bool(spec.get("wet_lab_ready", True))

    if engine_hardcoded:
        errors.append("engine_hardcoded must be false")
    if simulation_authorized:
        errors.append("simulation_authorized must be false")
    if wet_lab_ready:
        errors.append("wet_lab_ready must be false")

    valid = schema_valid and claim_report.passed and readiness_ok and not errors

    return ProductSpecValidationReport(
        product_id=product_id,
        valid=valid,
        schema_valid=schema_valid,
        claim_boundary_passed=claim_report.passed,
        readiness_within_foundation_limit=readiness_ok,
        engine_hardcoded=engine_hardcoded,
        simulation_authorized=simulation_authorized,
        wet_lab_ready=wet_lab_ready,
        errors=errors,
        warnings=warnings,
    )
