"""tdf-openmm-validation evidence schema tests."""

import copy
import json
from pathlib import Path

import pytest

from tdf_product_artifact_builder.tdf_openmm_contract import (
    load_tdf_openmm_evidence_schema,
    validate_tdf_openmm_evidence_file,
    validate_tdf_openmm_evidence_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"
SCHEMA = REPO_ROOT / "schemas/tdf_openmm_validation_evidence.schema.json"


def test_tdf_openmm_schema_loads() -> None:
    schema = load_tdf_openmm_evidence_schema(SCHEMA)
    assert schema["properties"]["source_tool"]["const"] == "tdf-openmm-validation"


def test_minimal_fixture_passes() -> None:
    report = validate_tdf_openmm_evidence_file(FIXTURE, SCHEMA)
    assert report.valid is True


def test_missing_required_field_fails() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    del payload["evidence_id"]
    with pytest.raises(Exception):
        validate_tdf_openmm_evidence_payload(payload, SCHEMA)
