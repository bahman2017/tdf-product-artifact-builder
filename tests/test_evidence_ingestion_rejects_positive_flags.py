"""Evidence ingestion rejects positive readiness flags."""

import json
from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"


def test_wet_lab_ready_true_rejected(tmp_path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    payload = json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))
    payload["wet_lab_ready"] = True
    (evidence_dir / "bad_flag.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")

    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(evidence_dir, out)
    assert report.accepted_count == 0
    assert report.rejected_count == 1
    assert report.rejected[0].reason == "positive_readiness_or_simulation_flag"
