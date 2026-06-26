"""Product spec schema tests."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml

from tdf_product_artifact_builder import load_product_spec_schema, validate_product_spec, validate_product_spec_schema

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_reference_product_spec_validates() -> None:
    report = validate_product_spec(REFERENCE_SPEC)
    assert report.valid is True
    assert report.product_id == "lithium_filter_candidate_v0_1"
    assert report.engine_hardcoded is False
    assert report.simulation_authorized is False
    assert report.wet_lab_ready is False


def test_schema_rejects_engine_hardcoded_true() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    spec["engine_hardcoded"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_product_spec_schema(spec)


def test_schema_rejects_simulation_authorized_true() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    spec["simulation_authorized"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_product_spec_schema(spec)


def test_schema_rejects_wet_lab_ready_true() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    spec["wet_lab_ready"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_product_spec_schema(spec)


def test_forbidden_claim_in_allowed_claims_rejected(tmp_path) -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    spec["allowed_claims"] = list(spec["allowed_claims"]) + ["simulation-ready membrane"]
    bad_path = tmp_path / "bad_spec.yaml"
    bad_path.write_text(yaml.dump(spec), encoding="utf-8")
    report = validate_product_spec(bad_path)
    assert report.valid is False


def test_product_spec_schema_file_exists() -> None:
    schema = load_product_spec_schema()
    assert schema["properties"]["engine_hardcoded"]["const"] is False
