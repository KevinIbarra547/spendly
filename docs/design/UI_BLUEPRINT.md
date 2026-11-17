# Spendly UI blueprint (design baseline, SPEC.md v2.8.7)

Source: Google Gemini layout draft, adopted November 17, 2026 as the visual baseline. Owner: Kevin (design system);
Cheyenne owns the World Simulation and Stocks views inside it.

## Required fixes (these override the draft below)

1. **AI Coach never changes the game.** Replace "Apply $2.60 Price Now" with a "Go to pricing" link; the player sets the price. (SPEC.md AC1: AI writes words only.)
2. **No fake simulation logic in code.** "6 units if price <= $2.60" is a mock for the picture only. Real results come from Ethan's engine API.
3. **Tailwind via npm and Vite**, never the CDN script, in the real app. Lucide icons and Inter font are approved.
4. **Remove owner badges** ("Kevin: screens", "Ethan: numbers") from the real UI; they were labels for the team demo.
5. **Extras after MVP:** command palette (Cmd+K), number-key shortcuts and the Settings extras wait until after Phase 7.
6. **Sim Assistant = AI Coach.** Use the name "AI Coach" and its rules (opens only when the player opens it; daily question caps).
7. The Stocks view follows SPEC.md S3 (candles, ranges 1D/1W/1M/All, order ticket, portfolio, trade history).

---

## Original draft (Gemini)

This document breaks down the exact architecture, layout hierarchy, design tokens, and interactive logic of the **Spendly Business Simulation** dashboard so you can replicate it cleanly inside Claude Artifacts.

---

## 1\. Core Layout Architecture (3-Zone Shell)

The application uses a full-viewport (`h-screen w-screen overflow-hidden`), pure white (`#FFFFFF`) three-zone shell with `1px` structural borders (`#E5E7EB`) instead of heavy shadows or tinted backgrounds:

1. **Left Navigation Rail (`60px` wide on Desktop / Bottom Tab Bar on Mobile):**

   * **Desktop (`md:w-[60px]`):** Fixed vertical icon rail with a top brand icon (`trending-up`), primary section triggers (`Home`, `Business`, `Learn`, `Stocks`), a quick `⌘K` search button, and bottom-anchored `Settings` \+ User Avatar (`JD`).  
   * **Tooltips & Shortcut Hints:** Hovering any rail icon reveals a dark floating tooltip (`bg-slate-900 text-white`) showing the section name and its keyboard shortcut key (`1`–`4`).  
   * **Status Dots:** Unread indicator dots (`w-2 h-2 rounded-full`) sit at the top-right of icons (e.g., blue dot on `Learn` for a newly unlocked lesson, amber dot on `Business` when pricing updates) and clear automatically when the user clicks that tab.  
   * **Mobile (`< 768px`):** Converts automatically into a fixed bottom tab bar (`order-2 h-14 border-t`).  
2. **Center Workspace (`flex-1 overflow-y-auto bg-white`):**

   * **Global Top Header (`h-16 border-b border-[#E5E7EB]`):**  
     * **Left:** Brand title (`Spendly`), active section breadcrumb pill, green Wallet balance pill (`$100.00`), and Day counter pill (`Day 1 of 30`).  
     * **Right:** `Game path` / `Real-life path` segmented toggle, `⌘K` search button, and the primary `Sim Assistant` toggle button (which displays an animated ping badge whenever a day advances while the assistant is collapsed).  
   * **Multi-View Canvas:** Swaps cleanly between 5 full-page views (`Home`, `Business`, `Learn`, `Stocks`, `Settings`) without page reloads.  
3. **Right Retractable Sim Assistant (`390px` on Desktop / Slide-Over Sheet on Mobile):**

   * Collapses smoothly via CSS width transitions (`w-0` vs `lg:w-[390px]`), using a fixed-width inner container so text never squishes mid-animation.  
   * **Interactive Chat Stream:** Supports user prompts, Coach Tip callout cards, and **1-click action buttons** inside chat bubbles (e.g., *Apply \$2.60 Price Now*) that directly mutate app state and trigger a toast confirmation.

---

## 2\. Interactive & Power-User Features

* **Command Palette (`Cmd+K` / `Ctrl+K`):** A centered modal over a blurred glass backdrop (`backdrop-filter: blur(4px)`) with real-time command filtering, section jumps, and quick simulation actions (`Simulate Next Day`, `Apply AI Recommended Price`, `Toggle Sim Assistant`). Closes on `ESC` or backdrop click.  
* **Global Number Key Shortcuts (`1`–`4`):** Pressing `1` (Home), `2` (Business), `3` (Learn), or `4` (Stocks) switches views immediately whenever the user is not typing inside an `<input>` or `<textarea>`.  
* **Live Simulation Loop:**  
  * Clicking **Simulate Next Day** calculates daily units sold based on current unit pricing (`6 units` if price $\le \$2.60$, otherwise `3 units`), increments the day counter and wallet balance, prepends a log card to **Recent Store Events**, and triggers a slide-up **Toast Notification** in the bottom-left corner.

---

## 3\. Ready-to-Paste Prompt for Claude

Copy and paste the prompt below directly into Claude to generate an identical single-file HTML prototype:

> Build a single-file, responsive HTML web application using Tailwind CSS (via CDN), Inter font, and Lucide icons for a business simulation dashboard called **Spendly**.

> **Visual Style & Layout Rules:**

> - Use a pure blank white (`#FFFFFF`) background across the entire app with clean `1px solid #E5E7EB` borders (no gray page backgrounds or dotted grids).  
> - **Left Navigation Rail:** Create a thin `60px` wide Railway-style icon sidebar on desktop (`#FFFFFF`, right border `#E5E7EB`) that converts into a bottom navigation bar on mobile (`< 768px`). Include icons for **Home \[1\]**, **Business \[2\]**, **Learn \[3\]** (with a blue unread notification dot), **Stocks \[4\]**, a **Search \[⌘K\]** trigger, and bottom-anchored **Settings** \+ **User Avatar (JD)**. Add dark hover tooltips on desktop showing the label and number shortcut.  
> - **Top Global Header (`64px` height):** Left side shows `Spendly`, active section breadcrumb, Wallet pill (`$100.00`), and Day pill (`Day 1 of 30`). Right side shows a `Game path` / `Real-life path` toggle, a `⌘K` button, and a `Sim Assistant` button (with a pulsing notification badge when collapsed).  
> - **Center Full-Page Workspace:** Build switchable views for Home (3 KPI cards: Today's sales `+$9.30` with `Kevin: screens` and `Ethan: numbers` badges, Lessons passed `2 of 9` with progress bar, Active Unit Price `$3.10`, plus a 30-Day Revenue Trajectory panel, Recent Store Events feed, and a **Simulate Next Day** button), Business (interactive pricing slider `$1.00–$6.00` and inventory card), Learn (3 course cards), Stocks (2 simulated tickers), and Settings.  
> - **Right Retractable Sim Assistant (`390px` wide):** A collapsible right-hand chat drawer with a fixed-width inner wrapper so content doesn't squish when toggled. Include a sample conversation where the AI suggests lowering the unit price to `$2.60` with a **1-click action button (`Apply $2.60 Price Now`)** inside the message bubble that updates the app's active price, updates the Business slider, and triggers a bottom-left slide-up **Toast Notification**.  
> - **Command Palette (`Cmd+K` / `Ctrl+K`) & Shortcuts:** Pressing `Cmd+K` or `Ctrl+K` opens a glass-backdrop search modal to filter and run navigation or simulation commands (`ESC` closes it). Pressing `1`, `2`, `3`, or `4` switches sections when not focused in an input field.