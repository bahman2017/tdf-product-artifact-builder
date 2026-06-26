"""Verify required project_control docs exist."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "project_control/PROJECT_CHARTER.md",
    "project_control/PRODUCTIZATION_STRATEGY.md",
    "project_control/ENGINE_PRODUCT_SEPARATION.md",
    "project_control/ROADMAP.md",
    "project_control/COMPLETED_WORK.md",
    "project_control/NEXT_ACTIONS.md",
    "project_control/DECISION_LOG.md",
    "project_control/PROMPT_LOG.md",
    "project_control/CURSOR_FEEDBACK_LOG.md",
    "project_control/RELEASE_CHAIN_STATUS.md",
    "project_control/PRODUCT_SPEC_REGISTRY.md",
    "project_control/REVIEW_BUNDLE_REQUIREMENTS.md",
    "project_control/CLAIM_BOUNDARIES.md",
    "project_control/PRODUCT_READINESS_LADDER.md",
]


def test_project_control_docs_exist() -> None:
    for rel in REQUIRED_DOCS:
        assert (REPO_ROOT / rel).is_file(), f"Missing {rel}"
