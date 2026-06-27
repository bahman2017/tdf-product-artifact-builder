"""validate_diagnostic_evidence CLI tests."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"
CLI = REPO_ROOT / "tools/validate_diagnostic_evidence.py"


def test_cli_validates_fixture() -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), "--evidence", str(FIXTURE)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Evidence validation passed" in result.stdout


def test_cli_fails_on_missing_file(tmp_path) -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), "--evidence", str(tmp_path / "missing.json")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
