"""Product report schema tests."""

import json
from pathlib import Path

import pytest
import yaml

from tdf_product_artifact_builder import (
    build_product_report,
    load_product_report_schema,
    validate_product_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"
SCHEMA_PATH = REPO_ROOT / "schemas/product_report.schema.json"


def test_product_report_schema_loads() -> None:
    schema = load_product_report_schema(SCHEMA_PATH)
    assert schema["title"] == "TDF Product Report"
    assert "product_id" in schema["required"]


def test_build_product_report_from_reference_spec() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    report = build_product_report(spec)
    assert report["product_id"] == "lithium_filter_candidate_v0_1"
    assert report["readiness_stage"] == "TDF_DESIGN_CANDIDATE"
    assert report["engine_hardcoded"] is False
    assert report["simulation_authorized"] is False
    assert report["wet_lab_ready"] is False
    assert report["openmm_execution"] is False
    assert report["lammps_execution"] is False
    assert report["package_type"] == "reviewer_package"


def test_product_report_validates_against_schema() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    report = build_product_report(spec)
    validate_product_report(report, SCHEMA_PATH)


def test_product_report_rejects_simulation_authorized_true() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    report = build_product_report(spec)
    report["simulation_authorized"] = True
    with pytest.raises(Exception):
        validate_product_report(report, SCHEMA_PATH)
