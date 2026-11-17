# Folder rules: .github/ — owner Myles (CODEOWNERS and repo settings with Kevin)

- Workflows use only standard GitHub-hosted runners (free on public repos) and never contain secrets in plain text.
- Make a check required only after it exists and passes on `main`.
- Changing loop rules (loop-check, templates, CODEOWNERS) is a harness change: name it in the task card.
- Role files in `agents/` belong to each person; edit someone's role file only with their approval.
