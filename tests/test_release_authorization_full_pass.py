"""Release authorization full-pass decision tests."""

import os
from pathlib import Path

import pytest

from tdf_product_artifact_builder.release_authorization import run_release_authorization_review

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "b79987acc43c1d8a767f40892495ac751982f40d"


@pytest.mark.skipif(
    os.environ.get("TDF_RELEASE_READINESS_NESTED_PYTEST") == "1",
    reason="Skip during nested pytest invoked by release authorization review",
)
def test_authorization_reports_approved_for_release_draft_when_checks_pass() -> None:
    report = run_release_authorization_review(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=True,
    )
    assert report.payload["release_readiness_decision"] == "READY_FOR_RELEASE_DRAFT"
    assert report.payload["known_blockers"] == []
    assert report.payload["release_authorization_decision"] == "APPROVED FOR RELEASE DRAFT"
