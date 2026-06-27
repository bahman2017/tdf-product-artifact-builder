#!/usr/bin/env python3
"""CLI for generating reviewer packages from product specs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tdf_product_artifact_builder.reviewer_package import create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a reviewer-facing package from a product spec."
    )
    parser.add_argument(
        "--product-spec",
        required=True,
        help="Path to product_spec.yaml",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for the reviewer package",
    )
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Optional diagnostic evidence JSON file (repeatable)",
    )
    parser.add_argument(
        "--evidence-ingestion-manifest",
        default=None,
        help="Optional EVIDENCE_INGESTION_MANIFEST.json from evidence directory ingestion",
    )
    args = parser.parse_args()

    spec_path = Path(args.product_spec)
    if not spec_path.is_file():
        print(f"ERROR: product spec not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    if args.evidence and args.evidence_ingestion_manifest:
        print("ERROR: provide --evidence or --evidence-ingestion-manifest, not both.", file=sys.stderr)
        sys.exit(1)

    manifest_path = Path(args.evidence_ingestion_manifest) if args.evidence_ingestion_manifest else None
    if manifest_path and not manifest_path.is_file():
        print(f"ERROR: evidence ingestion manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    try:
        report = create_reviewer_package(
            spec_path,
            args.output_dir,
            evidence_paths=args.evidence or None,
            evidence_ingestion_manifest_path=manifest_path,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Reviewer package created: {report.output_dir}")
    print(f"Product ID: {report.product_id}")
    print(f"Readiness stage: {report.readiness_stage}")
    print(f"Files written: {len(report.files_written)}")
    print(f"Claim boundary passed: {report.claim_boundary_passed}")
    print(f"simulation_authorized: {report.simulation_authorized}")
    print(f"wet_lab_ready: {report.wet_lab_ready}")
    print(f"evidence_included: {report.evidence_included}")
    for name in sorted(report.files_written):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
