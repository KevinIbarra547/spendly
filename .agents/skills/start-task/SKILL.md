---
name: start-task
description: Start a Spendly task the right way. Use when the user says /start-task <issue number> or asks to begin work on a task card.
---

# /start-task <issue#>

Follow every step. If a step fails, stop and tell the user what failed.

1. **Know who you work for.** Read only your person's role file `.github/agents/<name>.md` (named in the user's personal
   agent file). If you do not know the person, ask. Note their autonomy level.
2. **Hooks check.** Run `git config core.hooksPath`. If it is not `.githooks`, run `sh scripts/setup-hooks.sh`.
3. **Clean start.** Run `git status`. If there are uncommitted changes, stop and ask what to do with them.
4. **Latest main.** `git checkout main && git pull --ff-only`.
5. **Read the task card.** Open issue #<issue#> (GitHub web page, `gh issue view`, or ask the user to paste it).
   It must have: owner, scope (folders), spec sections, acceptance checks, test plan. If anything is missing or the
   owner is not your person, stop and offer `/plan-task` to fix the card.
6. **Scope check.** Every folder in the scope must belong to your person (see `AGENTS.md` ownership table), unless the
   card names the other owner as reviewer. Otherwise stop and ask.
7. **Branch.** `git checkout -b <type>/<issue#>-<short-kebab-name>` where type is `feat`, `fix`, `chore`, `docs` or `test`.
8. **Read only the spec sections the card lists** (search their headings in `SPEC.md`), plus folder `AGENTS.md` files.
9. **Plan back to the user** in 3–6 bullets: what you will change, which files, which tests prove it. At Level 1 wait
   for "go" before writing code.
