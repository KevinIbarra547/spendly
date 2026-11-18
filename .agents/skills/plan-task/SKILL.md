---
name: plan-task
description: Turn an idea, bug or request into a Spendly task card (GitHub issue). Use when the user says /plan-task, asks for something without a task card, or a card is missing fields.
---

# /plan-task "<request>"

You are the planner. You do not write code in this skill.

1. **Find the rule.** Search `SPEC.md` for the feature (IDs like BU6, S3, L1) and read only those sections.
   If the request needs a rule, value or API field the spec does not have, say so: that becomes a spec-change card
   (A.24 change control) owned by the area owner, not a coding card.
2. **Find the owner** from the `AGENTS.md` ownership table. One card = one owner = one area.
   If the request spans areas, split it into several cards and list which one must come first (contract-first).
3. **Size it.** A card should fit in one PR that a teammate can review in about 15 minutes. Split bigger work.
4. **Check the phase.** Look at `docs/harness/BUILD_PHASES.md`. If the card belongs to a later phase, mark it Backlog.
5. **Write the card** in the Task template format:
   - Title (verb first) · Owner · Phase
   - Scope: folders/files allowed
   - Spec sections to read
   - Acceptance checks (observable, 2–6 bullets)
   - Test plan (exact commands or manual steps)
   - Dependencies (or "None") · Protected flows touched (or "None") · Missing information (or "None")
6. **Create it** with `gh issue create` if available, or give the user the filled card to paste into
   GitHub → Issues → New issue → Task.
