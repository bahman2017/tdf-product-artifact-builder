"""Ingest evidence directory CLI tests."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_valid"
CLI = REPO_ROOT / "tools/ingest_evidence_directory.py"


def test_ingest_evidence_directory_cli(tmp_path) -> None:
    out = tmp_path / "ingestion"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--evidence-dir",
            str(VALID_DIR),
            "--output-dir",
            str(out),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Accepted: 2" in result.stdout
    assert (out / "EVIDENCE_INGESTION_MANIFEST.json").is_file()
