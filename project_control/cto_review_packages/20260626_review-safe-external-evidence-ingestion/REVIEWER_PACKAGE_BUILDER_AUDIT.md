# Reviewer package builder audit

- Generic reviewer package builder implemented.
- Generates 11 required reviewer files from product spec input.
- Deterministic output verified in tests (temporary directories only).
- Claim-boundary validation on generated outputs.
- No simulation, OpenMM, or LAMMPS execution.
- CLI: `tools/build_reviewer_package.py`
