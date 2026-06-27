"""Reviewer package determinism tests."""

import hashlib
from pathlib import Path

from tdf_product_artifact_builder import create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def _package_fingerprint(package_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(package_dir.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(package_dir).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_reviewer_package_is_deterministic(tmp_path) -> None:
    out_a = tmp_path / "pkg_a"
    out_b = tmp_path / "pkg_b"
    create_reviewer_package(REFERENCE_SPEC, out_a)
    create_reviewer_package(REFERENCE_SPEC, out_b)

    files_a = sorted(p.relative_to(out_a).as_posix() for p in out_a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(out_b).as_posix() for p in out_b.rglob("*") if p.is_file())
    assert files_a == files_b

    for rel in files_a:
        content_a = (out_a / rel).read_text(encoding="utf-8")
        content_b = (out_b / rel).read_text(encoding="utf-8")
        assert content_a == content_b, f"Content differs for {rel}"

    assert _package_fingerprint(out_a) == _package_fingerprint(out_b)
