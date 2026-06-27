#!/usr/bin/env python3
"""CLI for v0.1.0 release authorization review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tdf_product_artifact_builder.release_authorization import (
    run_release_authorization_review,
    write_release_authorization_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run release authorization review without tag, release, or publish actions."
    )
    parser.add_argument("--target-version", required=True, help="Target release version, e.g. 0.1.0")
    parser.add_argument("--base-commit", required=True, help="Base commit SHA for review provenance")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for release authorization reports",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running pytest during review (for faster checks)",
    )
    args = parser.parse_args()

    try:
        report = run_release_authorization_review(
            repo_root=REPO_ROOT,
            target_version=args.target_version,
            base_commit=args.base_commit,
            run_tests=not args.skip_tests,
        )
        written = write_release_authorization_outputs(report, Path(args.output_dir))
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    decision = report.payload["release_authorization_decision"]
    print(f"Release authorization review complete: {args.output_dir}")
    print(f"Target version: {args.target_version}")
    print(f"Decision: {decision}")
    print(f"Blockers: {len(report.payload['known_blockers'])}")
    for name in written:
        print(f"  - {name}")

    if decision == "BLOCKED":
        sys.exit(1)


if __name__ == "__main__":
    main()
