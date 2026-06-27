"""Reproducibility documentation tests."""

from pathlib import Path

from tdf_product_artifact_builder import create_reviewer_package
from tdf_product_artifact_builder.reproducibility import build_reproducibility_md
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"


def test_reproducibility_md_is_deterministic() -> None:
    spec = yaml.safe_load(REFERENCE_SPEC.read_text(encoding="utf-8"))
    a = build_reproducibility_md(spec)
    b = build_reproducibility_md(spec)
    assert a == b
    assert "build_reviewer_package.py" in a
    assert "No simulation execution" in a


def test_reproducibility_file_in_package(tmp_path) -> None:
    out = tmp_path / "reviewer_package"
    create_reviewer_package(REFERENCE_SPEC, out)
    content = (out / "REPRODUCIBILITY.md").read_text(encoding="utf-8")
    assert "Deterministic output" in content
    assert "lithium_filter_candidate_v0_1" not in content or "Product ID" in content
