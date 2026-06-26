"""CTO review bundle tool tests."""

import zipfile
from pathlib import Path

from tools.create_cto_review_bundle import REQUIRED_BUNDLE_FILES, create_cto_review_bundle

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cto_review_bundle_creates_required_files(tmp_path) -> None:
    bundle_dir, zip_path = create_cto_review_bundle(
        task_name="test-bundle",
        branch="feature/test",
        commit="abc123",
        output_dir=tmp_path,
    )
    for name in REQUIRED_BUNDLE_FILES:
        assert (bundle_dir / name).is_file(), f"Missing {name}"
    assert zip_path.is_file()


def test_cto_zip_excludes_forbidden_artifacts(tmp_path) -> None:
    bundle_dir, zip_path = create_cto_review_bundle(
        task_name="test-zip-audit",
        branch="feature/test",
        commit="def456",
        output_dir=tmp_path,
    )
    forbidden = tmp_path / "forbidden.xyz"
    forbidden.write_text("ATOM 0 0 0", encoding="utf-8")
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
    assert not any(name.endswith(".xyz") for name in names)
    assert not any("__pycache__" in name for name in names)
    assert not any(".venv" in name for name in names)
    assert not any(name.endswith(".env") for name in names)
