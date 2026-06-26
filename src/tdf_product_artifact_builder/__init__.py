"""Generic product artifact builder for TDF-chain reviewer packages."""

from tdf_product_artifact_builder.checksums import sha256_bytes, sha256_file
from tdf_product_artifact_builder.claim_boundaries import (
    ALLOWED_PRODUCT_PHRASES,
    FORBIDDEN_PRODUCT_PHRASES,
    ClaimBoundaryReport,
    scan_text_for_forbidden_claims,
    validate_claim_boundaries,
)
from tdf_product_artifact_builder.manifest import ManifestEntry, PackageManifest, build_manifest, manifest_to_dict
from tdf_product_artifact_builder.product_spec import (
    FOUNDATION_MAX_READINESS,
    READINESS_STAGES,
    ProductSpecValidationReport,
    load_product_spec,
    load_product_spec_schema,
    validate_product_spec,
    validate_product_spec_schema,
)
from tdf_product_artifact_builder.review_summary import (
    create_review_summary,
    load_review_summary_schema,
    validate_review_summary,
    write_review_summary,
)
from tdf_product_artifact_builder.reviewer_package import ReviewerPackageReport, create_reviewer_package
from tdf_product_artifact_builder.version import __version__

__all__ = [
    "ALLOWED_PRODUCT_PHRASES",
    "FORBIDDEN_PRODUCT_PHRASES",
    "FOUNDATION_MAX_READINESS",
    "READINESS_STAGES",
    "ClaimBoundaryReport",
    "ManifestEntry",
    "PackageManifest",
    "ProductSpecValidationReport",
    "ReviewerPackageReport",
    "__version__",
    "build_manifest",
    "create_review_summary",
    "create_reviewer_package",
    "load_product_spec",
    "load_product_spec_schema",
    "load_review_summary_schema",
    "manifest_to_dict",
    "scan_text_for_forbidden_claims",
    "sha256_bytes",
    "sha256_file",
    "validate_claim_boundaries",
    "validate_product_spec",
    "validate_product_spec_schema",
    "validate_review_summary",
    "write_review_summary",
]
