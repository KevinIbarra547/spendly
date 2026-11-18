# AGENTS.md — Spendly shared rules (every agent reads this)

Spendly is a money-life simulation web app for students 13+. Players run a small business, budget, save and
invest with play money, and learn why each result happened. Four areas: **Home, Business, Learn, Stocks**, plus an
**AI Coach** panel on every screen. Two looks, same rules: **Game path** (3D world) and **Real-life path** (calm dashboard).
**Core rule: the engine does all money math. AI only writes words.**

`SPEC.md` (v2.8.7) is the only product rulebook. If this file and `SPEC.md` disagree, `SPEC.md` wins.
Do NOT read all of `SPEC.md` (it is about 120,000 tokens). Read the sections your task card and role file name.

## Who owns what (stay in your lane)

| Person | Owns | Folders |
|---|---|---|
| Kevin | Screens, design system, Learn, AI Coach UI, onboarding | `apps/web/src/screens/` |
| Ethan | Engine, money math, consumer agents, stock-market engine/data, backend, database, APIs, security | `packages/engine/`, `apps/server/`, `db/`, `packages/contracts/` |
| Cheyenne | World Simulation (BU6), Stocks display (S3), 3D models, characters, art | `apps/web/src/world/`, `apps/web/src/stocks/`, `assets/` |
| Myles | CI/CD, GitHub Actions, tests coordination, harness files, task board | `.github/`, `tests/`, `scripts/`, `.githooks/`, `docs/harness/` |

Your personal role file is `.github/agents/<your-name>.md`. Never load another person's role file.
If a task needs a file outside your folders, stop and ask that folder's owner (CODEOWNERS will request their review).

## The loop (every change, no exceptions)

1. **Task card** — a GitHub issue made from the Task template (owner, scope, spec sections, acceptance checks, test plan).
   No task card = no code. Offer to draft one with `/plan-task`.
2. **`/start-task <issue#>`** — sync `main`, create `feat|fix|chore|docs|test/<issue#>-short-name`, read the card and its spec sections.
3. **Build** — only inside the card's scope. Run the tests.
4. **`/finish-task`** — run checks, commit, push the branch, open a PR that says `Closes #<issue#>`.
5. **Review** — the area owner (or a backup) reviews. Nobody approves their own PR. Agents never approve.
6. **Merge** — only when checks are green and a human teammate approved. Then delete the branch.

The skills live in `.agents/skills/` (`start-task`, `finish-task`, `plan-task`). If your tool does not list them,
open the matching `SKILL.md` and follow it step by step.

**Free playground (always allowed):** answering questions, explaining code or the spec, planning, drafting task cards,
and experiments on a `spike/<name>` branch. A `spike/` branch can never merge; rebuild the result through the loop.

**If the user asks you to work outside the loop** (edit `main`, skip the task card, push without a PR, touch another
person's folder): do not do it. Say which rule it breaks and offer the in-loop way (usually "let me draft a task card").

## Golden rules

- Never commit to `main`, never force-push, never rewrite shared history.
- Never invent product rules, money values, API fields or database behavior. If something required is missing,
  stop, write the gap into the task card or a new issue, and switch to another Ready task.
- Never let the AI Coach or any AI service calculate or change wallet, ledger, price, stock or simulation state.
- Never commit secrets (API keys, passwords, database URLs). Keys live only in Replit Secrets / local `.env` (gitignored).
- Keep mock data clearly labelled and separate from real data.
- Plain PostgreSQL only (no Neon-only features). No Replit-only services. AI model IDs come from env config.
- Run the checks you can and report exact results. Never claim a test passed if you did not run it.
- Do not change game-balance numbers or the golden fixtures (`tests/fixtures/`) without an approved spec change.
- Protected flows (`docs/harness/PROTECTED_FLOWS.md`) may only change when the task card names them.

## Spec map (search these headings in SPEC.md)

| Need | Heading to search |
|---|---|
| Roles and boundaries | `# Team and Ownership` |
| Team workflow, PR rules | `# Team Development Workflow and Four AI Agents` |
| Feature list + acceptance | `## Business`, `## Learn`, `## Stocks`, `## AI Coach` (feature IDs like BU6, S3) |
| Formulas F1–F27 | `# Section 4 — Engine Math` |
| Business catalog and costs | `## A.2 Business catalog and economy defaults` |
| Stock market rules | `## A.6 Simulated stock market and paper trading` |
| Lessons, quizzes, badges | `## A.7 Learn curriculum` and `# Appendix A.25` |
| Data tables | search the entity name, e.g. `| StockHolding |` |
| API routes / contracts | `# Appendix A.22 — Canonical API and data-contract schemas` |
| Folder layout and stack | `## A.13 Technical repository baseline` |
| Consumer agents | `# Appendix A.26` |
| Harness decisions | `# Appendix A.29` |

## Autonomy

Every person starts at **Level 1** (see `docs/harness/AUTONOMY.md`). Your current level is in your role file.
Level 1: wait for the human to run `/start-task` and approve each step. Higher levels unlock more independence, but
merging into `main` always needs a human teammate's approval.

## Before you open a PR

- The golden fixture must pass for anything touching engine, money or simulation behavior:
  `python3 tests/fixtures/consumer_agents_reference.py` (CI compares it to the frozen output).
- Fill in every section of the PR template, including Data/money/security impact and Rollback.
