"""Raw coordinate and secret file pattern tests."""

from tools.static_policy_audit import RAW_COORDINATE_SUFFIXES, FORBIDDEN_PATH_MARKERS


def test_raw_coordinate_suffixes_defined() -> None:
    assert ".pdb" in RAW_COORDINATE_SUFFIXES
    assert ".xyz" in RAW_COORDINATE_SUFFIXES
    assert ".cif" in RAW_COORDINATE_SUFFIXES


def test_forbidden_path_markers_include_env_and_cache() -> None:
    assert ".env" in FORBIDDEN_PATH_MARKERS
    assert "__pycache__" in FORBIDDEN_PATH_MARKERS
    assert ".pytest_cache" in FORBIDDEN_PATH_MARKERS
    assert ".venv" in FORBIDDEN_PATH_MARKERS
