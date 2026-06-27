# Release candidate checklist -- v0.1.0

## Version metadata

- [x] `pyproject.toml` version is `0.1.0`
- [x] `src/tdf_product_artifact_builder/version.py` is `0.1.0`
- [x] `CHANGELOG.md` present
- [x] `RELEASE_NOTES_DRAFT.md` present

## Validation

- [x] `python3 -m pytest -q` passes
- [x] `python3 tools/static_policy_audit.py` passes
- [x] Evidence ingestion succeeds (review-safe fixtures)
- [x] Reviewer package generation succeeds in `/tmp`
- [x] Release-readiness audit succeeds

## Safety invariants

- [x] No simulation executed
- [x] No OpenMM or LAMMPS execution
- [x] No runtime import of `tdf-openmm-validation`
- [x] No tracked real product package generated
- [x] No product readiness stage upgrade
- [x] Reference product spec remains `TDF_DESIGN_CANDIDATE`

## Release actions (must remain false)

- [x] No git tag created
- [x] No GitHub release created
- [x] No package published to PyPI

## Post-draft governance (separate CTO approval required)

- [ ] CTO approval for tag creation
- [ ] CTO approval for GitHub release
- [ ] CTO approval for package publish
- [ ] Real tracked product package generation (still blocked)
- [ ] Runtime integration with `tdf-openmm-validation` (still blocked)
