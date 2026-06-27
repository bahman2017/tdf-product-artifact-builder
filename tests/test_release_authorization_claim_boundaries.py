"""Release authorization claim boundary tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.release_authorization import run_release_authorization_review
from tdf_product_artifact_builder.release_readiness import FORBIDDEN_DECISION_PHRASES

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "b79987acc43c1d8a767f40892495ac751982f40d"


def test_authorization_decision_does_not_approve_publish_or_release() -> None:
    report = run_release_authorization_review(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    decision = report.payload["release_authorization_decision"]
    assert decision in {"CTO_REVIEW_REQUIRED", "APPROVED FOR RELEASE DRAFT", "BLOCKED"}
    assert decision not in {"APPROVED TO PUBLISH", "APPROVED TO RELEASE"}
    serialized = json.dumps(report.payload).upper()
    for phrase in FORBIDDEN_DECISION_PHRASES:
        assert phrase not in serialized
