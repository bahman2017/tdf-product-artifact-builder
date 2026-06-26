"""Engine / product separation tests."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "tdf_product_artifact_builder"

FORBIDDEN_ENGINE_TERMS = (
    "lithium_filter_candidate",
    "lithium_filter_candidate_v0_1",
    "if product_id ==",
    "elif product_id ==",
    "match product_id",
)


def test_no_product_specific_branching_in_engine() -> None:
    for path in ENGINE_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_ENGINE_TERMS:
            assert term not in text, f"Forbidden product term {term!r} in {path.name}"


def test_lithium_filter_only_in_product_spec_and_docs() -> None:
    hits: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        if any(".egg-info" in part for part in path.parts):
            continue
        if ".pytest_cache" in path.parts:
            continue
        if path.suffix in {".pyc", ".zip"}:
            continue
        if path.is_relative_to(ENGINE_DIR):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "lithium_filter" in text or "lithium filter" in text.replace("-", " "):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits, "Reference product should appear in specs/docs"
    for hit in hits:
        allowed = (
            hit.startswith("product_specs/")
            or hit.startswith("project_control/")
            or hit.startswith("tests/")
            or hit.startswith("schemas/")
            or hit == "README.md"
        )
        assert allowed, f"Unexpected lithium reference in {hit}"
