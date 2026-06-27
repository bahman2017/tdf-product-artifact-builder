"""Diagnostic evidence schema tests."""

import json
from pathlib import Path

import pytest
import yaml

from tdf_product_artifact_builder.diagnostic_evidence import (
    load_diagnostic_evidence_schema,
    validate_diagnostic_evidence_payload,
)
from tdf_product_artifact_builder.evidence_adapter import validate_and_adapt_evidence

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"
SCHEMA = REPO_ROOT / "schemas/diagnostic_evidence.schema.json"


def test_diagnostic_evidence_schema_loads() -> None:
    schema = load_diagnostic_evidence_schema(SCHEMA)
    assert "diagnostic_flags" in schema["required"]


def test_adapted_fixture_validates_against_diagnostic_schema() -> None:
    adapted = validate_and_adapt_evidence(FIXTURE)
    validate_diagnostic_evidence_payload(adapted, SCHEMA)


def test_missing_required_field_fails() -> None:
    adapted = validate_and_adapt_evidence(FIXTURE)
    del adapted["evidence_id"]
    with pytest.raises(Exception):
        validate_diagnostic_evidence_payload(adapted, SCHEMA)
