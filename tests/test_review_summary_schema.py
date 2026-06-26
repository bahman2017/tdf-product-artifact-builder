"""Review summary schema tests."""

import pytest
from jsonschema import ValidationError

from tdf_product_artifact_builder import create_review_summary, validate_review_summary


def _minimal_summary(**overrides):
    base = create_review_summary(
        task_name="test",
        repository="https://example.com/repo",
        branch="main",
        base_commit="abc",
        head_commit="def",
        tests_run="pytest -q",
        tests_passed=True,
        ci_status="NOT_APPLICABLE",
        generated_outputs_tracked=False,
        raw_data_committed=False,
        claim_boundary_passed=True,
        product_readiness_stage="TDF_DESIGN_CANDIDATE",
        completed_work_updated=True,
        next_actions_updated=True,
        decision_log_updated=True,
        prompt_log_updated=True,
        cursor_feedback_log_updated=True,
        cto_review_zip_created=True,
        review_zip_path="project_control/cto_review_packages/test.zip",
        known_risks=[],
        blockers=[],
        next_recommended_step="review",
    )
    base.update(overrides)
    return base


def test_review_summary_validates() -> None:
    validate_review_summary(_minimal_summary())


def test_review_summary_rejects_missing_required_field() -> None:
    payload = _minimal_summary()
    del payload["head_commit"]
    with pytest.raises(ValidationError):
        validate_review_summary(payload)
