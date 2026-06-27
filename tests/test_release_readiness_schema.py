"""Release readiness schema tests."""

from pathlib import Path

from tdf_product_artifact_builder.release_readiness import load_release_readiness_schema

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_readiness_schema_loads() -> None:
    schema = load_release_readiness_schema(REPO_ROOT)
    assert schema["properties"]["release_action_taken"]["const"] is False
    assert schema["properties"]["release_readiness_decision"]["enum"] == [
        "READY_FOR_RELEASE_DRAFT",
        "BLOCKED",
        "CTO_REVIEW_REQUIRED",
    ]
