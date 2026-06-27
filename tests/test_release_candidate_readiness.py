"""Release candidate readiness decision tests."""

import os
from pathlib import Path

import pytest

from tdf_product_artifact_builder.release_readiness import run_release_readiness_audit

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "e46844919cc7adc9bf4aafb5aeecb6ba6f8d0c8a"


@pytest.mark.skipif(
    os.environ.get("TDF_RELEASE_READINESS_NESTED_PYTEST") == "1",
    reason="Skip during nested pytest invoked by release-readiness audit",
)
def test_release_candidate_reports_ready_for_release_draft_when_checks_pass() -> None:
    report = run_release_readiness_audit(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=True,
    )
    assert report.payload["package_version"] == "0.1.0"
    assert report.payload["pyproject_version"] == "0.1.0"
    assert report.payload["known_blockers"] == []
    assert report.payload["release_readiness_decision"] == "READY_FOR_RELEASE_DRAFT"
    assert report.payload["governance_notes"]
