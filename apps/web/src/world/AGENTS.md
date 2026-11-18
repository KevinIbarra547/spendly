# Folder rules: apps/web/src/world/ — owner Cheyenne (SPEC.md BU6)

- Plays back the day from `visitPlayback`, `eventId` and business state. Reads only; no API writes.
- Never decide who buys, prices, stock or money. The engine's `reasonCode` is the truth.
- Same turn result = identical playback (seed visuals from `turnId` + `visitorIndex`).
- Missing data or a failed 3D load falls back to the Real-life summary.
- Not your agent's folder? Stop and ask Cheyenne. Changes here need Cheyenne's review (CODEOWNERS).
