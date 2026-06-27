"""Reviewer package builder tests."""

from pathlib import Path

from tdf_product_artifact_builder import REVIEWER_PACKAGE_REQUIRED_FILES, create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_create_reviewer_package_report_fields(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    report = create_reviewer_package(REFERENCE_SPEC, out)
    assert report.package_created is True
    assert report.manifest_present is True
    assert report.checksums_present is True
    assert report.product_report_valid is True
    assert report.claim_boundary_passed is True
    assert report.simulation_authorized is False
    assert report.wet_lab_ready is False
    assert report.readiness_stage == "TDF_DESIGN_CANDIDATE"
    assert report.product_id == "lithium_filter_candidate_v0_1"


def test_create_reviewer_package_cleans_existing_output(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")
    create_reviewer_package(REFERENCE_SPEC, out)
    assert not (out / "stale.txt").exists()
    assert (out / "MANIFEST.json").is_file()
