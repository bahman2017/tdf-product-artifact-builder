"""Evidence ingestion rejects raw coordinate files."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"


def test_raw_pdb_file_rejected(tmp_path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "structure.pdb").write_text("ATOM 1 N ALA\n", encoding="utf-8")
    (evidence_dir / "valid.json").write_text(BASE_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(evidence_dir, out)
    assert report.accepted_count == 1
    assert report.rejected_count == 1
    assert report.rejected[0].reason == "forbidden_raw_or_coordinate_file"
