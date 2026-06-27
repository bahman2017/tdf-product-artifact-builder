# Roadmap

## Phase 1 -- Foundation (merged)

1. Foundation project-control docs and schemas
2. Generic product-spec schema
3. Reference product spec: `lithium_filter_candidate_v0_1`
4. Reviewer package builder scaffold
5. Tests for schema, claim boundaries, engine/product separation
6. CTO review bundle tooling

## Phase 1b -- CI and static policy foundation (merged)

1. GitHub Actions CI workflow
2. Static policy audit for tracked files
3. Hidden/bidirectional Unicode control checks
4. Forbidden claim and engine/product coupling checks in CI
5. CTO review bundle for CI foundation

## Phase 1c -- Generic reviewer package builder hardening (merged)

1. Deterministic reviewer package generation from product specs
2. Product report schema and reviewer manifest schema
3. Manifest and checksum generation
4. Claim-boundary validation on generated outputs
5. CLI tool for local reviewer package generation
6. Determinism and no-simulation flag tests

## Phase 1d -- tdf-openmm-validation integration contract (merged)

1. Diagnostic evidence schema and validators
2. tdf-openmm-validation evidence contract schema
3. Evidence manifest and checksum generation
4. Optional evidence summaries in reviewer packages
5. Review-safe JSON fixtures and contract tests only

## Phase 1e -- Review-safe external evidence ingestion (merged)

1. Directory-based ingestion of review-safe JSON evidence files
2. Acceptance and rejection reports with clear reasons
3. Evidence ingestion manifest with checksums
4. Reviewer package builder consumes ingestion manifest
5. Deterministic tests using temporary directories only

## Phase 1f -- v0.1.0 release-readiness audit (merged)

1. Release-readiness audit tooling and schema
2. Machine-readable and human-readable readiness reports
3. Blocker documentation without tag, release, or publish
4. Decision: READY_FOR_RELEASE_DRAFT, BLOCKED, or CTO_REVIEW_REQUIRED only

## Phase 1g -- v0.1.0 release-candidate finalization (in progress)

1. Bump package metadata from dev to candidate 0.1.0
2. CHANGELOG, release notes draft, release candidate checklist
3. Re-run release-readiness audit for release draft readiness
4. No tag, release, or publish

## Phase 2 -- Integration (after release-readiness validation)

1. Live ingestion of tdf-openmm-validation diagnostic outputs
2. External reviewer package generation from validated evidence

## Phase 2a -- Release draft (CTO approval required)

1. Consider v0.1.0 release draft only if audit approves and CTO authorizes
2. No tag, publish, or GitHub release without explicit approval

## Phase 3 -- Validation planning

1. Conventional validation plan templates and registry

## Phase 4 -- Gated execution (CTO approval required)

1. Controlled simulation only after explicit CTO approval

## Phase 5 -- External validation (downstream)

1. Wet-lab/fabrication readiness only after external validation

## Phase 2b -- Product package generation (after builder validation)

1. Real product package generation from validated product specs
2. Generic builder validation before lithium reference package output

Controlled simulation and wet-lab stages remain blocked.
