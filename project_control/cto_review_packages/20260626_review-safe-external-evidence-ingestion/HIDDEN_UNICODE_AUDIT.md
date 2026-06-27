# Hidden Unicode audit

- Scanned tracked text files for bidi controls, zero-width characters, BOM, and Cf/Cc/Cs controls.
- Scanned reviewer-facing text and CTO review ZIP members for strict ASCII.
- Allowed controls: newline, carriage return, tab only.
- Result: see STATIC_POLICY_AUDIT.md hidden_unicode and reviewer_ascii findings if any.

Final result: PASS
