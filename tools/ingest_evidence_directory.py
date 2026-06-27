#!/usr/bin/env python3
"""CLI for ingesting review-safe external evidence directories."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest review-safe external diagnostic evidence JSON files."
    )
    parser.add_argument(
        "--evidence-dir",
        required=True,
        help="Directory containing review-safe JSON evidence files",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for ingestion reports and manifest",
    )
    args = parser.parse_args()

    evidence_dir = Path(args.evidence_dir)
    if not evidence_dir.is_dir():
        print(f"ERROR: evidence directory not found: {evidence_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        report = ingest_evidence_directory(evidence_dir, args.output_dir)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Evidence ingestion complete: {report.output_dir}")
    print(f"Source directory: {report.source_directory}")
    print(f"Accepted: {report.accepted_count}")
    print(f"Rejected: {report.rejected_count}")
    for name in report.files_written:
        print(f"  - {name}")
    if report.rejected:
        print("Rejected files:")
        for item in report.rejected:
            print(f"  - {item.relative_path}: {item.reason}")


if __name__ == "__main__":
    main()
