# Role: Ethan — engine, money math, consumer agents, stock-market engine, backend

**Autonomy level:** 1 (see `docs/harness/AUTONOMY.md`)
**Agents:** Claude Code and Mistral Vibe (Google AI Studio for drafts only)
**GitHub:** `ethan-chang-2028`

## You own
- `packages/engine/` — turn engine, formulas F1–F27, consumer agents (A.26), deterministic RNG (A.14.1), market engine (A.6).
- `apps/server/` — Express API, auth, security, Admin, scheduled jobs.
- `db/` — migrations and seeds (plain PostgreSQL only).
- `packages/contracts/` — Zod schemas from A.22 (shared: every change needs the affected screen owner's review).

## You do not own (ask first)
- `apps/web/` (Kevin's screens, Cheyenne's world and stocks), `.github/` and CI (Myles).

## v2.8.7 items assigned to you
- `visitPlayback` list in each business day result (anonymous: visitorIndex, archetype, reasonCode, units).
- Stocks: `GET /stocks/{symbol}/candles`, `GET /stocks/trades`, `cost_basis_cents` on holdings, `StockDailyCandle` table,
  daily roll-up + 7-day tick cleanup, event pins.
- Admin storage check (warn at 70%), daily logical backup (7 copies) to free separate storage before launch.
- Create the Neon, Groq and FRED accounts; Replit hosting runs on your account. Keys only in Replit Secrets.

## Your spec sections
`# Section 4 — Engine Math`, `## A.2`–`## A.6`, `## A.9`–`## A.12`, `# Appendix A.14`, `# Appendix A.22`, `# Appendix A.26`, BU1–BU5, S1, Admin features.

## Extra rules for your area
- Golden fixture (`tests/fixtures/consumer_agents_reference.py`) must stay green; it is a protected flow.
- Money is integer cents; rounding follows the spec's D-rules. Any balance change needs a spec change first.
