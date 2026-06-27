"""Reviewer package claim boundary tests."""

from pathlib import Path

from tdf_product_artifact_builder import (
    create_reviewer_package,
    scan_text_for_forbidden_claims,
    validate_generated_package_claims,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_generated_package_passes_claim_boundary_scan(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    report = validate_generated_package_claims(out)
    assert report.passed is True
    assert not report.forbidden_hits


def test_no_forbidden_claims_in_readme(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    readme = (out / "README_FOR_REVIEWERS.md").read_text(encoding="utf-8")
    hits = scan_text_for_forbidden_claims(readme)
    assert not hits


def test_no_simulation_statement_present(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    statement = (out / "NO_SIMULATION_NO_WETLAB_STATEMENT.md").read_text(encoding="utf-8")
    assert "No OpenMM execution occurred." in statement
    assert "No LAMMPS execution occurred." in statement
    assert "TDF_DESIGN_CANDIDATE" in statement
