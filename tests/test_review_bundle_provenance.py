"""Review bundle provenance tests."""

import json

import pytest

from tdf_product_artifact_builder import (
    build_provenance_fields,
    validate_review_bundle_provenance,
    validate_review_summary,
)
from tools.create_cto_review_bundle import REQUIRED_BUNDLE_FILES, create_cto_review_bundle

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
BUNDLE_SUMMARY = (
    REPO_ROOT
    / "project_control/cto_review_packages/20260626_product-artifact-builder-foundation/REVIEW_SUMMARY.json"
)


def test_exact_mode_provenance() -> None:
    fields = build_provenance_fields(source_commit="abc", bundle_in_repo=False)
    assert fields["review_bundle_metadata_mode"] == "EXACT_SOURCE_COMMIT"
    assert fields["head_commit"] == "abc"
    assert fields["authoritative_commit"] == "abc"
    validate_review_bundle_provenance(dict(fields))


def test_post_commit_mode_provenance() -> None:
    fields = build_provenance_fields(source_commit="abc", bundle_in_repo=True)
    assert fields["review_bundle_metadata_mode"] == "POST_COMMIT_BUNDLE_WITH_SELF_REFERENCE_LIMITATION"
    validate_review_bundle_provenance(dict(fields))


def test_provenance_rejects_inconsistent_exact_mode() -> None:
    with pytest.raises(ValueError):
        validate_review_bundle_provenance(
            {
                "head_commit": "a",
                "authoritative_commit": "b",
                "bundle_generated_after_commit": "a",
                "review_bundle_metadata_mode": "EXACT_SOURCE_COMMIT",
                "metadata_commit_consistent": True,
            }
        )


def test_cto_review_bundle_creates_required_files(tmp_path) -> None:
    bundle_dir, zip_path = create_cto_review_bundle(
        task_name="test-bundle",
        branch="feature/test",
        commit="abc123",
        output_dir=tmp_path,
        bundle_in_repo=True,
    )
    for name in REQUIRED_BUNDLE_FILES:
        assert (bundle_dir / name).is_file(), f"Missing {name}"
    assert zip_path.is_file()
    summary = json.loads((bundle_dir / "REVIEW_SUMMARY.json").read_text(encoding="utf-8"))
    validate_review_summary(summary)
    validate_review_bundle_provenance(summary)
    assert summary["metadata_commit_consistent"] is True
    assert summary["head_commit"] == "abc123"
    manifest = (bundle_dir / "MANIFEST.md").read_text(encoding="utf-8")
    assert "head_commit" in manifest
    handoff = (bundle_dir / "CTO_HANDOFF_REPORT.md").read_text(encoding="utf-8")
    assert "Authoritative commit" in handoff or "authoritative" in handoff.lower()


def test_cto_zip_excludes_forbidden_artifacts(tmp_path) -> None:
    import zipfile

    bundle_dir, zip_path = create_cto_review_bundle(
        task_name="test-zip-audit",
        branch="feature/test",
        commit="def456",
        output_dir=tmp_path,
    )
    forbidden = tmp_path / "forbidden.xyz"
    forbidden.write_text("ATOM 0 0 0", encoding="utf-8")
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
    assert not any(name.endswith(".xyz") for name in names)
    assert not any("__pycache__" in name for name in names)
    assert not any(".venv" in name for name in names)
    assert not any(name.endswith(".env") for name in names)


def test_tracked_foundation_bundle_provenance_consistent() -> None:
    if not BUNDLE_SUMMARY.is_file():
        pytest.skip("Foundation bundle not generated yet")
    summary = json.loads(BUNDLE_SUMMARY.read_text(encoding="utf-8"))
    validate_review_summary(summary)
    validate_review_bundle_provenance(summary)
    assert summary["metadata_commit_consistent"] is True
