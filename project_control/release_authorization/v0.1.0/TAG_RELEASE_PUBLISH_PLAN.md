# Tag / release / publish plan -- v0.1.0

Documentation only. No commands in this document have been executed.

Every future command requires separate explicit CTO approval.

## Planned tag (not executed)

```text
PLANNED ONLY - DO NOT RUN WITHOUT CTO APPROVAL
git tag -a v0.1.0 -m "tdf-product-artifact-builder v0.1.0"
git push origin v0.1.0
```

## Planned GitHub release draft (not executed)

```text
PLANNED ONLY - DO NOT RUN WITHOUT CTO APPROVAL
gh release create v0.1.0 --draft --title "v0.1.0" \
  --notes-file project_control/release_readiness/v0.1.0/RELEASE_NOTES_DRAFT.md
```

## Planned PyPI publish (not executed)

```text
PLANNED ONLY - DO NOT RUN WITHOUT CTO APPROVAL
python3 -m build
python3 -m twine upload dist/*
```

This plan does not authorize any release action.
