# Build phases (authoritative plan, SPEC.md v2.8.7)

Each phase ends with a **QA gate**. Do not start the next phase's core work until the gate passes
(isolated work on mocks may start early). When a gate passes: lock the new flows in
`PROTECTED_FLOWS.md`, then Myles tags a checkpoint (`phase-N-done`) so the team can roll back.

| Phase | Goal | Kevin | Ethan | Cheyenne | Myles | QA gate |
|---|---|---|---|---|---|---|
| **0. Harness + skeleton** | The loop works for everyone | Joins loop first (ROLLOUT stage 1); Tailwind theme stub | Joins loop (stage 3); Neon/Groq/FRED accounts; Replit app shell | Joins loop (stage 4); Vibe trusted-folder check | Repo skeleton (A.13), `ci.yml` with Postgres container, task board | A PR that breaks a test or the loop is blocked; Replit shows a blank page from `main` |
| **1. Foundations** | Shared building blocks | Design system + 3-zone layout shell (UI blueprint) | Zod contracts (A.22), base migrations, RNG helper + vectors | Asset manifest + placeholder models; world scene loads | Contract tests + type-check required | RNG vectors and contract tests pass; layout shell renders |
| **2. First playable day** | One full day end to end | Onboarding, Lesson 0 screens, Home, Business controls + "Why?" | Accounts, wallet + ledger, $100 grant, Sticker Shop turn, consumer agents, `visitPlayback` | World Simulation plays a day from `visitPlayback` (BU6) | E2E test "sign up, finish Lesson 0, play 3 days" | Golden fixture + 30-turn tests + E2E pass → 🔒 protect |
| **3. Full business** | Every MVP business rule | Restock, second slot, Money Report, Make Your Own forms | 18 templates, events, loans, savings, overdraft, Fresh Start, month-end | Event reactions, shop states, second-slot building | Business integration tests | Business tests pass → 🔒 |
| **4. Learn** | Lessons, quizzes, labs, badges | 9 lessons, quizzes, labs, badges screens | Progress + once-only rewards | Learn art | Learn E2E | Learn tests pass → 🔒 |
| **5. Stocks** | Paper trading | Stocks unlock flow | Market engine, candles, trades, average cost, roll-up job | Stocks display (S3): watchlist, candles, ticket, portfolio, history | Stocks E2E | Stocks tests pass → 🔒 |
| **6. AI Coach** | Coach panel | Coach panel UI, prompts | Provider plug-in, moderation, caps, budget | — | Coach tests (mocked providers) | Coach tests pass → 🔒 |
| **7. Release** | Ready for players | Premium mock checkout, Settings, polish | Admin, safe mode, write queue, demo mode, backups, restore drill | Art polish | Release checklist, deploy, checkpoint | Release checklist + restore drill pass |

Extras that are not MVP (command palette, number-key shortcuts, limit orders, etc.) wait until after Phase 7.
If time runs short, cut from the end of a phase's extras, never from a QA gate.
