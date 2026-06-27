"""Release authorization review tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.release_authorization import (
    RELEASE_DRAFT_CHECKLIST_ITEMS,
    run_release_authorization_review,
    validate_release_authorization_report,
    write_release_authorization_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "b79987acc43c1d8a767f40892495ac751982f40d"


def test_release_authorization_review_produces_valid_report(tmp_path) -> None:
    out = tmp_path / "authorization"
    report = run_release_authorization_review(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    validate_release_authorization_report(report.payload, REPO_ROOT)
    written = write_release_authorization_outputs(report, out)
    assert "RELEASE_AUTHORIZATION_REPORT.json" in written
    payload = json.loads((out / "RELEASE_AUTHORIZATION_REPORT.json").read_text(encoding="utf-8"))
    assert payload["target_version"] == "0.1.0"
    assert payload["release_action_taken"] is False
    assert payload["release_authorization_decision"] in {
        "CTO_REVIEW_REQUIRED",
        "APPROVED FOR RELEASE DRAFT",
        "BLOCKED",
    }


def test_all_required_checklist_items_present() -> None:
    report = run_release_authorization_review(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    assert set(RELEASE_DRAFT_CHECKLIST_ITEMS) == set(report.payload["checks"].keys())
