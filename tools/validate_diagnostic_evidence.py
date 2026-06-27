#!/usr/bin/env python3
"""Validate diagnostic evidence JSON against integration contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tdf_product_artifact_builder.diagnostic_evidence import validate_diagnostic_evidence_payload
from tdf_product_artifact_builder.evidence_adapter import validate_and_adapt_evidence
from tdf_product_artifact_builder.tdf_openmm_contract import validate_tdf_openmm_evidence_file

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate diagnostic evidence JSON")
    parser.add_argument("--evidence", required=True, help="Path to evidence JSON file")
    args = parser.parse_args()

    evidence_path = Path(args.evidence)
    if not evidence_path.is_file():
        print(f"ERROR: evidence file not found: {evidence_path}", file=sys.stderr)
        sys.exit(1)

    openmm_report = validate_tdf_openmm_evidence_file(evidence_path)
    if not openmm_report.valid:
        print(f"ERROR: {openmm_report.errors}", file=sys.stderr)
        sys.exit(1)

    try:
        adapted = validate_and_adapt_evidence(evidence_path)
        validate_diagnostic_evidence_payload(adapted)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Evidence validation passed: {evidence_path}")
    print(f"Evidence ID: {adapted['evidence_id']}")
    print(f"Source tool: {adapted['source_tool']}")
    print("Safety flags: all false")


if __name__ == "__main__":
    main()
