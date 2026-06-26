# Claim boundaries

## Forbidden claims

The following claims are **explicitly forbidden** in product specs, reviewer packages, and engine outputs:

- TDF physics proof claim
- Real lithium selectivity claim
- Real battery performance claim
- Simulation-ready claim
- Force-field-ready claim
- Wet-lab-ready claim
- Fabrication-ready claim
- Experimentally validated claim
- Production-ready membrane claim

## Allowed framing (reference product)

- Lithium-selective membrane **candidate**
- Phase-gated BN membrane **artifact**
- Li/Na analog **diagnostic result**
- Reviewable atomic blueprint
- Static validation package
- Diagnostic preparation package
- External reviewer package
- Conventional validation required

## Enforcement

- JSON schema enforces `engine_hardcoded`, `simulation_authorized`, and `wet_lab_ready` as `false`
- `claim_boundaries.py` scans for forbidden phrases
- Tests reject invalid specs and engine product coupling
