"""Evidence ingestion schema tests."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_acceptance import load_evidence_acceptance_report_schema
from tdf_product_artifact_builder.evidence_ingestion_manifest import load_evidence_ingestion_manifest_schema
from tdf_product_artifact_builder.evidence_rejection import load_evidence_rejection_report_schema

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evidence_ingestion_manifest_schema_loads() -> None:
    schema = load_evidence_ingestion_manifest_schema()
    assert schema["properties"]["manifest_version"]["const"] == "1.0"
    assert schema["properties"]["simulation_authorized"]["const"] is False


def test_evidence_acceptance_report_schema_loads() -> None:
    schema = load_evidence_acceptance_report_schema()
    assert schema["properties"]["report_version"]["const"] == "1.0"
    assert schema["properties"]["wet_lab_ready"]["const"] is False


def test_evidence_rejection_report_schema_loads() -> None:
    schema = load_evidence_rejection_report_schema()
    assert schema["properties"]["report_version"]["const"] == "1.0"
