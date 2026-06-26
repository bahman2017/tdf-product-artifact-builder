"""Review summary schema tests."""

import pytest
from jsonschema import ValidationError

from tdf_product_artifact_builder import (
    build_provenance_fields,
    create_review_summary,
    validate_review_bundle_provenance,
    validate_review_summary,
)


def _minimal_summary(**overrides):
    provenance = build_provenance_fields(source_commit="def", bundle_in_repo=False)
    base = create_review_summary(
        task_name="test",
        repository="https://example.com/repo",
        branch="main",
        base_commit="abc",
        head_commit=str(provenance["head_commit"]),
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
    base.update(provenance)
    base.update(overrides)
    return base


def test_review_summary_validates() -> None:
    payload = _minimal_summary()
    validate_review_summary(payload)
    validate_review_bundle_provenance(payload)


def test_review_summary_rejects_missing_required_field() -> None:
    payload = _minimal_summary()
    del payload["head_commit"]
    with pytest.raises(ValidationError):
        validate_review_summary(payload)


def test_post_commit_provenance_requires_limitation() -> None:
    provenance = build_provenance_fields(source_commit="abc123", bundle_in_repo=True)
    assert provenance["review_bundle_metadata_mode"] == "POST_COMMIT_BUNDLE_WITH_SELF_REFERENCE_LIMITATION"
    assert provenance["metadata_commit_consistent"] is True
    assert provenance["known_self_reference_limitation"]
    validate_review_bundle_provenance({**_minimal_summary(), **provenance})
