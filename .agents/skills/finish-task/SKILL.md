---
name: finish-task
description: Finish a Spendly task and open the pull request. Use when the user says /finish-task or the task's work is done.
---

# /finish-task

1. **Right branch.** `git branch --show-current` must look like `feat|fix|chore|docs|test/<issue#>-name`. Never `main`,
   never `spike/...` (a spike cannot be merged; rebuild it through a task card).
2. **Scope check.** `git diff --name-only origin/main...HEAD` plus uncommitted files: every file must be inside the
   task card's scope. If not, stop and tell the user which files are outside.
3. **Run the checks** that exist (for example `npm run typecheck`, `npm test`, and for engine/money/simulation changes
   `python3 tests/fixtures/consumer_agents_reference.py | diff - tests/fixtures/CONSUMER_AGENT_REFERENCE_RESULTS.txt`).
   Record exact commands and results. If something fails, fix it or stop and report.
4. **Protected flows.** If any file listed in `docs/harness/PROTECTED_FLOWS.md` changed, the task card must name that
   flow and its test must pass. Otherwise stop.
5. **No secrets.** Check the diff for keys, passwords or database URLs. Never commit `.env`.
6. **Commit** with a clear message: `<type>: <what changed> (#<issue#>)`.
7. **Push the branch:** `git push -u origin <branch>`.
8. **Open the PR** to `main` using `.github/pull_request_template.md`. The first section must say `Closes #<issue#>`.
   Fill every section in plain language. Use `gh pr create` if available; otherwise give the user the GitHub
   "Compare & pull request" link and the filled-in text to paste.
9. **Tell the user** who should review (the area owner from CODEOWNERS) and that agents never approve or merge.
