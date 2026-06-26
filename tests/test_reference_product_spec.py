"""Reference product spec tests."""

from pathlib import Path

import yaml

from tdf_product_artifact_builder import create_reviewer_package, validate_product_spec

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_reference_spec_fields() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    assert spec["product_id"] == "lithium_filter_candidate_v0_1"
    assert spec["readiness_stage"] == "TDF_DESIGN_CANDIDATE"
    assert spec["engine_hardcoded"] is False
    assert spec["simulation_authorized"] is False
    assert spec["wet_lab_ready"] is False


def test_reviewer_package_from_reference_spec(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    report = create_reviewer_package(REFERENCE_SPEC, out)
    assert report.package_created is True
    assert report.simulation_authorized is False
    assert report.wet_lab_ready is False
    assert (out / "MANIFEST.json").is_file()


def test_reference_spec_validation_report() -> None:
    report = validate_product_spec(REFERENCE_SPEC)
    assert report.claim_boundary_passed is True
    assert report.readiness_within_foundation_limit is True
