"""Static policy audit tests."""

import subprocess
from pathlib import Path

from tools.static_policy_audit import (
    audit_tracked_files,
    format_report,
    scan_forbidden_claim_line,
    scan_hidden_unicode,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_static_policy_audit_passes_on_repo() -> None:
    report = audit_tracked_files(REPO_ROOT)
    assert report.passed, format_report(report)


def test_hidden_unicode_controls_rejected() -> None:
    text = "safe\u202atext"
    hits = scan_hidden_unicode(text)
    assert hits


def test_raw_coordinate_suffix_rejected(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "bad.xyz").write_text("ATOM 0 0 0\n", encoding="utf-8")
    subprocess.run(["git", "add", "bad.xyz"], cwd=repo, check=True, capture_output=True)
    report = audit_tracked_files(repo)
    assert not report.passed
    assert any(f.check == "raw_coordinates" for f in report.findings)


def test_forbidden_claims_rejected() -> None:
    assert scan_forbidden_claim_line("This is a proven lithium filter.") == "proven lithium filter"
    assert scan_forbidden_claim_line("- forbidden: proven lithium filter") is None


def test_engine_coupling_rejected(tmp_path) -> None:
    repo = tmp_path / "repo"
    engine = repo / "src" / "tdf_product_artifact_builder"
    engine.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (engine / "bad.py").write_text('PRODUCT = "lithium_filter_candidate_v0_1"\n', encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    report = audit_tracked_files(repo)
    assert not report.passed
    assert any(f.check == "engine_product_coupling" for f in report.findings)


def test_static_policy_script_exits_zero() -> None:
    result = subprocess.run(
        ["python3", "tools/static_policy_audit.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RESULT: PASS" in result.stdout
