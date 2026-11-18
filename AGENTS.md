# AGENTS.md — Shared instructions for coding agents

Every AI coding agent (and human teammate) working in this repository must follow these rules.
They are the operating rules from `SPEC.md` ("Minimum shared AGENTS.md rules") and are binding
for every task. If a rule here conflicts with `SPEC.md`, `SPEC.md` wins.

## Before you edit anything

- Read `SPEC.md` and the linked task/issue before making any change.
- Work only on a short-lived task branch. Never commit directly to `main`.
- Respect ownership boundaries (SPEC.md, "Ownership boundaries"): only modify files within
  the task's scope.
- Inspect the current repository structure before creating folders. Do not restructure
  existing code to match the example layout in `SPEC.md`.

## While you work

- Never invent product rules, money values, API fields, or database behavior. If a required
  parameter, rule, schema, contract, or acceptance criterion is missing, stop that task and
  file an issue naming the gap and owner (SPEC.md "Agent stop rule"). Continue only on an
  independent Ready task.
- Never let AI Coach or any AI service calculate, write, or change wallet, ledger, or stock
  values. The game engine is authoritative for money math; AI writes words only.
- Keep mock data clearly separated from real application data and clearly labelled.
- Never commit API keys, passwords, recovery codes, database URLs, or other secrets. Use the
  approved secret store / environment configuration.
- Do not edit another person's active task branch or workspace.
- Do not tune game-balance values. Changes require a versioned balancing proposal and a
  regression run against the reference fixtures.

## Before you open a PR

- Run the available tests/checks for the task and report exact results. Never claim a test
  passed if it was not run.
- The golden fixture must pass before any merge that touches engine, money, or simulation
  behavior: `python3 tests/fixtures/consumer_agents_reference.py`
- Fill in every section of the pull request template, including "Data / money / security
  impact" and "Rollback".
- Explain the changes, affected files, risks, and test steps in the PR.
- Stop and ask the feature owner when requirements conflict or a required value/contract is
  missing.
