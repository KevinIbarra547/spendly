# Rollout: one person at a time

Add one person to the loop, prove it works, then add the next. Do not skip a stage's gate.

| Stage | Who joins | Agent | Practice task (Phase 0) | Gate to pass before the next stage |
|---|---|---|---|---|
| **1** | Kevin | Claude Code | `docs` task: add a "How to run Spendly" section to `README.md` | Canary check passes; hook blocks a commit on `main`; a bad PR (no `Closes #`) fails loop-check; the good PR is reviewed by Myles and merged |
| **2** | + Myles | Codex | Repo skeleton from SPEC.md A.13 + `ci.yml` with a Postgres container | Codex loads `AGENTS.md` and `myles.md`; Kevin reviews; branch protection turned on with the 2 required checks |
| **3** | + Ethan | Claude Code / Mistral Vibe | Bring `engine_formulas_reference.py` (branch `claude/fervent-planck-o18yu0`) in through a task card, then Zod contracts from A.22 | Two people's PRs open at the same time without touching each other's folders; CODEOWNERS requests the right reviewers |
| **4** | + Cheyenne | Mistral Vibe | Asset manifest + placeholder scene in `apps/web/src/world/` | Vibe trusted-folder check passes; all four people have merged one PR each through the loop |

After stage 4: the team starts Phase 1 (`BUILD_PHASES.md`). Anyone stuck in a stage pairs with someone who already passed it.
Write down every problem you hit in a GitHub issue labelled `harness` so the harness gets better.
