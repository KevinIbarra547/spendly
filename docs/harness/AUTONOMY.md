# Autonomy levels

Goal: start with humans driving every step, then let agents run the loop with less help as the team earns trust.
Your level is written in your role file (`.github/agents/<name>.md`). Everyone starts at Level 1.

| Level | Human does | Agent does | Tool setting |
|---|---|---|---|
| **1. Training wheels** | Picks the task, runs `/start-task`, says "go" after the plan, approves commands, runs `/finish-task` | Builds inside the card's scope | Ask before edits and commands |
| **2. Task runner** | Reviews the PR | Picks the next Ready card in your area from the board, runs the whole loop, opens the PR | Auto-approve edits inside owned folders; still ask for installs and anything outside scope |
| **3. Teammate** | Approves merges | Runs several cards in a row; a reviewer agent comments on the PR before a human reviews | Same as Level 2 plus a reviewer-agent step |

**Never automated at any level:** approving or merging into `main`, changing protected flows without a named task,
changing `SPEC.md` rules, touching secrets, or changing repository settings.

**Moving up a level** (Myles records it in the role file through a PR the person approves):
- Level 1 → 2: at least 5 merged PRs through the loop, none reverted, no loop-check failures in the last 3.
- Level 2 → 3: at least 10 more merged PRs, none reverted, and the area has protected-flow tests.

**Moving down:** a reverted PR, a protected-flow break or a loop bypass drops that person one level until 3 clean PRs.
