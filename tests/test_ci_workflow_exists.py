"""CI workflow existence tests."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists() -> None:
    assert CI_WORKFLOW.is_file()


def test_ci_workflow_runs_pytest() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "pytest -q" in text


def test_ci_workflow_runs_static_policy_audit() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "static_policy_audit.py" in text


def test_ci_workflow_does_not_run_openmm_or_lammps() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8").lower()
    assert "openmm" not in text
    assert "lammps" not in text
    assert "lmp -in" not in text
    assert "minimize" not in text
    assert "dynamics" not in text
