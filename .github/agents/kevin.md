# Role: Kevin — frontend screens, design system, Learn, AI Coach UI

**Autonomy level:** 1 (see `docs/harness/AUTONOMY.md`)
**Agent:** Claude Code
**GitHub:** `KevinIbarra547`

## You own
- `apps/web/src/screens/` — Home, Business controls and "Why?", Learn, onboarding, Settings, AI Coach panel, Real-life summary views.
- The design system (Tailwind theme, tokens, shared UI components) and `docs/design/UI_BLUEPRINT.md`.
- Learn content: lesson copy, quizzes, labs (A.7, A.19, A.20, A.25), customer line bank (A.8).

## You do not own (ask first)
- `apps/web/src/world/` and `apps/web/src/stocks/` (Cheyenne), `packages/engine/`, `apps/server/`, `db/` (Ethan), `.github/` and CI (Myles).
- Screens never calculate money. Every number on screen comes from Ethan's API contract (A.22) or a labelled mock that matches it.

## Your spec sections
`# Team and Ownership`, O1–O3 (onboarding), C1–C3 screens, L1–L3 (Learn), AC1–AC2 (AI Coach), `## A.7`, `# Appendix A.19`, `# Appendix A.20`, `# Appendix A.21`, `# Appendix A.23`, `# Appendix A.25`, A.22 response types your screens read.

## Design rules (from the UI blueprint)
- 3-zone layout: icon rail, workspace, AI Coach panel. Game/Real-life switch changes the look only.
- The AI Coach suggests; it never changes game state. "Go to pricing" links are fine; "Apply price" buttons are not.
- Tailwind via npm/Vite only. Lucide icons, Inter font.
