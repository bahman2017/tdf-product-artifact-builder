"""Release readiness audit must not perform release actions."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "tools/release_readiness_audit.py"
BASE_COMMIT = "5ca67ccf731d059b3dd8eb0bb619fe5ff6974827"


def test_release_readiness_cli_no_release_actions(tmp_path) -> None:
    out = tmp_path / "readiness"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--target-version",
            "0.1.0",
            "--base-commit",
            BASE_COMMIT,
            "--output-dir",
            str(out),
            "--skip-tests",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in {0, 1}
    payload_path = out / "RELEASE_READINESS_REPORT.json"
    assert payload_path.is_file()
    text = payload_path.read_text(encoding="utf-8")
    assert '"release_action_taken": false' in text
    assert '"tag_created": false' in text
    assert '"github_release_created": false' in text
    assert '"package_published": false' in text
    assert (out / "NO_RELEASE_ACTIONS_TAKEN.md").is_file()


def test_release_readiness_tool_has_no_tag_or_publish_commands() -> None:
    source = (REPO_ROOT / "src/tdf_product_artifact_builder/release_readiness.py").read_text(
        encoding="utf-8"
    )
    cli = CLI.read_text(encoding="utf-8")
    forbidden = ("git tag", "gh release", "twine upload", "pip publish")
    for phrase in forbidden:
        assert phrase not in source
        assert phrase not in cli
