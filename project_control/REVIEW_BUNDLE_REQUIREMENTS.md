# Review bundle requirements

## Required contents

- Product spec copy or summary
- Claim boundaries document
- Limitations document
- Manifest with SHA256 checksums
- Explicit non-claims for simulation, wet-lab, and physics proof

## Exclusions

- Raw coordinate files (PDB, XYZ, CIF, etc.)
- Secrets, tokens, `.env` files
- Caches, venvs, `__pycache__`
- Simulation outputs
- Wet-lab or client dispatch packages
- Large binaries

## Flags

All review bundles must record:

- `simulation_authorized: false`
- `wet_lab_ready: false`
- `engine_hardcoded: false`
