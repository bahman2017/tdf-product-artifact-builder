"""Ensure no OpenMM/LAMMPS imports or execution in engine code."""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "tdf_product_artifact_builder"

FORBIDDEN_IMPORTS = {"openmm", "lammps", "tdf_openmm_validation", "tdf-openmm-validation"}


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_no_openmm_or_lammps_imports_in_engine() -> None:
    hits: list[str] = []
    for path in ENGINE_DIR.glob("*.py"):
        imports = _imports_in_file(path)
        bad = imports & FORBIDDEN_IMPORTS
        if bad:
            hits.append(f"{path.name}: {sorted(bad)}")
    assert not hits, f"Forbidden imports found: {hits}"
