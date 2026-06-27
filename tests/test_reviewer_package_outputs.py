"""Reviewer package output file tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder import REVIEWER_PACKAGE_REQUIRED_FILES, create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_all_required_files_exist(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    for name in REVIEWER_PACKAGE_REQUIRED_FILES:
        assert (out / name).is_file(), f"Missing required file: {name}"


def test_product_report_contains_spec_fields(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    report = json.loads((out / "PRODUCT_REPORT.json").read_text(encoding="utf-8"))
    assert report["product_id"] == "lithium_filter_candidate_v0_1"
    assert report["product_type"] == "phase_gated_bn_membrane_candidate"
    assert "Li/Na analog diagnostic separation" in report["target_behavior"]
    assert len(report["source_artifacts"]) >= 1
    assert len(report["allowed_claims"]) >= 1
    assert len(report["forbidden_claims"]) >= 1


def test_checksums_match_content_files(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    checksums = json.loads((out / "CHECKSUMS.sha256.json").read_text(encoding="utf-8"))
    assert checksums["algorithm"] == "sha256"
    assert checksums["product_id"] == "lithium_filter_candidate_v0_1"
    rel_paths = {entry["relative_path"] for entry in checksums["files"]}
    assert "MANIFEST.json" not in rel_paths
    assert "CHECKSUMS.sha256.json" not in rel_paths
    assert "README_FOR_REVIEWERS.md" in rel_paths
