"""Reviewer package with evidence tests."""

from pathlib import Path

from tdf_product_artifact_builder.package_writer import REVIEWER_PACKAGE_EVIDENCE_FILES
from tdf_product_artifact_builder.reviewer_package import create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"


def test_reviewer_package_includes_evidence_files(tmp_path) -> None:
    out = tmp_path / "pkg"
    report = create_reviewer_package(SPEC, out, evidence_paths=[FIXTURE])
    assert report.evidence_included is True
    for name in REVIEWER_PACKAGE_EVIDENCE_FILES:
        assert (out / name).is_file(), f"Missing {name}"


def test_evidence_summary_is_review_safe(tmp_path) -> None:
    out = tmp_path / "pkg"
    create_reviewer_package(SPEC, out, evidence_paths=[FIXTURE])
    summary = (out / "DIAGNOSTIC_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")
    assert "simulation_executed: `False`" in summary
    assert ".pdb" not in summary
