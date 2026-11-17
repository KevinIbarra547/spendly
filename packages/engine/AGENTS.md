# Folder rules: packages/engine/ — owner Ethan

- Pure, deterministic code: no network, no database calls, no unseeded randomness (use the A.14.1 RNG registry).
- Money is integer cents with the spec's rounding rules. Formulas follow SPEC.md Section 4 exactly.
- The golden fixture (`tests/fixtures/`) must stay green; changing balance numbers needs an approved spec change.
- Not your agent's folder? Stop and ask Ethan. Changes here need Ethan's review (CODEOWNERS).
