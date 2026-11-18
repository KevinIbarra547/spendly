# Role: Cheyenne — World Simulation, Stocks display, 3D art

**Autonomy level:** 1 (see `docs/harness/AUTONOMY.md`)
**Agent:** Mistral Vibe (trust the repo folder so Vibe loads `AGENTS.md`)
**GitHub:** `cheyenneminniefee-blip`

## You own
- `apps/web/src/world/` — **World Simulation (BU6):** how the Game-path world plays back each day: timeline, customer journey,
  reactions, lines, event effects, shop states, camera, determinism, fallback.
- `apps/web/src/stocks/` — **Stocks display (S3):** watchlist, stock page, line/candle chart (1D/1W/1M/All), order ticket,
  portfolio with average cost and gain/loss, trade history, event pins, notices.
- `assets/` — 3D models, characters, art, asset manifest (A.18).

## You do not own (ask first)
- `packages/engine/`, `apps/server/`, `db/` (Ethan), `apps/web/src/screens/` (Kevin), `.github/` (Myles).
- Your code **reads** engine results and API data. It never decides who buys, prices, stock levels or money.

## Your spec sections
BU6 (World Simulation), S3 (Stocks display), S1–S2, `## A.6`, A.18 (assets), A.22 types `VisitPlaybackItem`,
`StockCandlesResponse`, `StockTradesResponse`, `StockAccountResponse`, `StocksMarketResponse`.

## Extra rules for your area
- Same turn result = same playback, every time (seed visual variety from `turnId` + `visitorIndex`).
- Not in MVP: limit/stop orders, short selling, margin, dividends, volume bars.
- Until Ethan's endpoints exist, use labelled mock data that matches the A.22 types exactly.
