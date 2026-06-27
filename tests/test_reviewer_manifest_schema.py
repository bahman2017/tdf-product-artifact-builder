"""Reviewer manifest schema tests."""

import json
from pathlib import Path

import pytest

from tdf_product_artifact_builder import (
    REVIEWER_PACKAGE_REQUIRED_FILES,
    build_manifest,
    create_reviewer_package,
    load_reviewer_manifest_schema,
    manifest_to_dict,
    validate_reviewer_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"
SCHEMA_PATH = REPO_ROOT / "schemas/reviewer_manifest.schema.json"


def test_reviewer_manifest_schema_loads() -> None:
    schema = load_reviewer_manifest_schema(SCHEMA_PATH)
    assert schema["title"] == "TDF Reviewer Package Manifest"
    assert "entries" in schema["required"]


def test_manifest_from_generated_package(tmp_path) -> None:
    out = tmp_path / "pkg"
    create_reviewer_package(REFERENCE_SPEC, out)
    manifest_data = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    validate_reviewer_manifest(manifest_data, SCHEMA_PATH)
    assert manifest_data["product_id"] == "lithium_filter_candidate_v0_1"
    assert manifest_data["manifest_version"] == "1.0"
    assert manifest_data["openmm_execution"] is False
    assert len(manifest_data["entries"]) == len(REVIEWER_PACKAGE_REQUIRED_FILES) - 1


def test_manifest_rejects_invalid_entry(tmp_path) -> None:
    manifest = build_manifest(tmp_path, product_id="test_product")
    payload = manifest_to_dict(manifest)
    payload["entries"] = [{"relative_path": "x.md", "sha256": "bad", "size_bytes": 0}]
    with pytest.raises(Exception):
        validate_reviewer_manifest(payload, SCHEMA_PATH)
