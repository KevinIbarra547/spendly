# Protected flows

A protected flow already works and has a test that proves it. Its test is a **required check**: a PR that breaks it
cannot merge. A task may change a protected flow only if its task card names the flow here, and the owner reviews it.

How a flow gets added: when a phase's QA gate passes, the owner adds a row, Myles makes its test required on `main`.

| Flow | Owner | Files | Test (required check) | Since |
|---|---|---|---|---|
| Consumer-agent golden fixture | Ethan | `tests/fixtures/consumer_agents_reference.py`, `tests/fixtures/CONSUMER_AGENT_REFERENCE_RESULTS.txt` | CI job "Golden fixture (consumer agents reference)" | Phase 0 |
| The loop itself | Myles | `.github/workflows/loop-check.yml`, `.githooks/`, `.agents/skills/` | CI job "Loop check (branch name + task link)" | Phase 0 |
