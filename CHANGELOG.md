# Changelog

All notable changes to `tdf-product-artifact-builder` are documented here.

## [0.1.0] - release candidate (unreleased)

Release-candidate preparation only. No tag, GitHub release, or package publish has occurred.

### Added

- Generic product-spec schema and reference product spec input
- GitHub Actions CI and static policy audit tooling
- Deterministic reviewer package builder with manifest and checksums
- tdf-openmm-validation evidence contract (schemas and validators only)
- Review-safe external evidence directory ingestion workflow
- Release-readiness audit tooling and reports
- Release candidate checklist and release notes draft

### Safety and scope

- No simulation, OpenMM, or LAMMPS execution
- No runtime import of `tdf-openmm-validation`
- No tracked real product package generation
- Reference product spec remains `TDF_DESIGN_CANDIDATE`
- Build trust in the artifact, not belief in the theory

### Prior development milestones (merged to main)

- PR #1: foundation
- PR #2: CI/static policy
- PR #3: generic reviewer package builder hardening
- PR #4: tdf-openmm-validation evidence contract
- PR #5: review-safe external evidence ingestion
- PR #6: v0.1.0 release-readiness audit
