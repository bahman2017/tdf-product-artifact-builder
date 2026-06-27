# Completed work

## tdf-openmm-validation v1.0.0 -- LIVE/CLOSED

- Release URL: https://github.com/bahman2017/tdf-openmm-validation/releases/tag/v1.0.0
- Tag: `v1.0.0` -> `874ef6190847d14a4c4c649a4a1849a67eaf0c93`
- Main CI: PASS
- Tests: 147 passed
- Examples: 10/10 OK
- Diagnostic flags:
  - `lammps_input_executed = false`
  - `simulation_executed = false`
  - `accepted_for_simulation = false`
- Interpretation: stable diagnostic/preparation release only; no simulation authorization.

## tdf-product-artifact-builder v0.1.0-dev -- FOUNDATION MERGED

- PR #1 merged into `main`
- Merge commit: `0a67db9f6e2a2200214f447d7d7cc78e16cdfb96`
- Foundation head: `e931b3e1d876c0aab58bdb4fe93ac434244930e6`
- Tests at foundation close: 24 passed
- No CI workflow existed at foundation close
- Generic engine scaffold, product-spec schema, review-summary schema, CTO review bundle tooling
- Reference product spec `lithium_filter_candidate_v0_1` added (input only)

## tdf-product-artifact-builder v0.1.0-dev -- CI/STATIC POLICY MERGED

- PR #2 merged into `main`
- Merge commit: `50760712a9c4f19a03944f8e22c035a038e9d967`
- Tests at merge: 41 passed
- GitHub Actions: PASS (Python 3.11 and 3.12)
- Static policy audit: PASS
- GitHub Actions CI workflow, static policy audit tooling, hidden Unicode checks

## tdf-product-artifact-builder v0.1.0-dev -- REVIEWER PACKAGE BUILDER HARDENING IN PROGRESS

- Generic reviewer package builder implementation
- Product report and reviewer manifest schemas
- CLI tool `tools/build_reviewer_package.py`
- Deterministic package generation tests (temporary directories only)
- No tag; no release; no real product packages tracked
