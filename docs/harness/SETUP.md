# One-time setup (each person, each computer)

1. **Get the repo:** `git clone https://github.com/KevinIbarra547/spendly` (or `git pull` if you already have it).
   If you have an old copy with commits that are not on GitHub, ask Myles before pushing anything.
2. **Turn on the loop guards:** `sh scripts/setup-hooks.sh` (blocks commits/pushes on `main` and force-pushes).
3. **Tell your agent who you are** — add ONE line to your *personal* agent file (never commit it):

   | Tool | Personal file |
   |---|---|
   | Claude Code | `~/.claude/CLAUDE.md` |
   | Mistral Vibe | `~/.vibe/AGENTS.md` (also trust the `spendly` folder when Vibe asks, or it will not load `AGENTS.md`) |
   | Codex | `~/.codex/AGENTS.md` |

   Line to add (use your own name): `When working in the spendly repo, I am Kevin. Read .github/agents/kevin.md at the start of every session.`
4. **Canary check:** start your agent in the repo and ask: *"Who am I, what is my autonomy level, and which folders can you edit?"*
   It must answer from your role file. If it does not, fix step 3.
5. **Secrets:** never paste keys into chat, the repo or Discord. Local testing uses a `.env` file (already gitignored);
   the live app uses Replit Secrets on Ethan's account.
6. **Google AI Studio:** thinking and drafts only. Nothing from it goes into the repo except through your repo agent and a PR.

## Repository settings (Kevin, as repo owner, after the harness PR merges)

GitHub → Settings → Branches → Add rule (or Rules → New ruleset) for `main`:
- Require a pull request before merging; require 1 approval; **require review from Code Owners**.
- Dismiss stale approvals when new commits are pushed; require conversation resolution.
- Require status checks: "Loop check (branch name + task link)" and "Golden fixture (consumer agents reference)".
  Add more checks later only after they exist and pass.
- Block force pushes and deletions. Do not allow bypassing (include administrators).
- Settings → General: turn on "Automatically delete head branches".
