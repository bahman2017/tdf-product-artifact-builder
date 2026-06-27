"""Reviewer package simulation flag tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder import create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_product_report_flags_are_false(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    report = json.loads((out / "PRODUCT_REPORT.json").read_text(encoding="utf-8"))
    assert report["engine_hardcoded"] is False
    assert report["simulation_authorized"] is False
    assert report["wet_lab_ready"] is False
    assert report["openmm_execution"] is False
    assert report["lammps_execution"] is False


def test_manifest_flags_are_false(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["simulation_authorized"] is False
    assert manifest["wet_lab_ready"] is False
    assert manifest["openmm_execution"] is False
    assert manifest["lammps_execution"] is False


def test_readiness_stage_preserved(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    report_obj = create_reviewer_package(REFERENCE_SPEC, out)
    assert report_obj.readiness_stage == "TDF_DESIGN_CANDIDATE"
    product_report = json.loads((out / "PRODUCT_REPORT.json").read_text(encoding="utf-8"))
    assert product_report["readiness_stage"] == "TDF_DESIGN_CANDIDATE"
