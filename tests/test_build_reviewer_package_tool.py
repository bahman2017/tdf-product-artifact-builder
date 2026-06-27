"""Build reviewer package CLI tests."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"
CLI = REPO_ROOT / "tools/build_reviewer_package.py"


def test_cli_generates_package(tmp_path) -> None:
    out = tmp_path / "cli_package"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--product-spec",
            str(REFERENCE_SPEC),
            "--output-dir",
            str(out),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Reviewer package created:" in result.stdout
    assert (out / "MANIFEST.json").is_file()
    assert (out / "PRODUCT_REPORT.json").is_file()


def test_cli_fails_on_missing_spec(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--product-spec",
            str(tmp_path / "missing.yaml"),
            "--output-dir",
            str(tmp_path / "out"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
