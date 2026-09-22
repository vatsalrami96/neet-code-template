---
name: today
description: Start the day. Shows what is due (new problems, verifies, re-solves), shows the primer if a section starts, runs a five-minute recognition drill, opens the first problem in the browser, and logs the start time. Trigger on "start", "what's today", "morning", "let's go", or /today.
---

# today

1. Run `python3 scripts/plan.py today --json` from the repo root. Read the JSON.
2. If `auto_closed` is non-empty, say in one line that yesterday was closed automatically and how many items rolled forward.
3. If `light` is true: say it is the light day. Only re-solves and drill today. Offer `resolve` and `drill` and stop.
4. If `first_of_section` is set:
   - If `primers/<section_id>.md` does not exist, write it now following `primers/README.md` (all seven sections, under two screens, real invariants).
   - Show a three-line summary of the primer and the two warm-up questions. Wait for their answers. Grade them in one line each.
     If both are wrong, spend up to 20 minutes on the fundamentals in chat before continuing.
5. Print the due list in this order: mixed, verify, new, resolve. For each: tag, title, difficulty, section (omit the section for `mixed`),
   Amazon score if any, and the LeetCode URL. For resolves show the kind (`code` or `explain`) and stage.
   Mark Premium-locked problems; those only open with LeetCode Premium (see `meta.premium` in `plan/problems.json`).
6. Recognition drill, five minutes, unless they say "skip drill". Same scope and source rules as the `drill` skill - read them there
   and do not restate them loosely here. In short: five paraphrased statements, no titles, **all inside sections they have already
   solved**, and **none of them a problem that appears anywhere in `plan/problems.json`** (that includes today's list and the
   twelve in `99-amazon-gap`) - using one burns their first real attempt at it. Never reach into a section they have not covered.
   They answer with the pattern, one line of approach, and the target complexity. Grade each right/wrong; a right pattern with a
   wrong bound is wrong. Then `python3 scripts/plan.py drill --type recognition --score <right> --total 5`.
   If the legal pool is too thin to build five honest statements (early days, when the queue covers most of what they know),
   say so in one line and skip the drill. Skipping is correct; spoiling a queued problem is not.
7. Open the first `mixed`/`verify`/`new` problem's `lc_url` in their Chrome LeetCode tab (see "LeetCode access" in CLAUDE.md -
   Chrome, not the built-in pane, because they solve in their own editor setup).
   **Do not start the clock.** They are still reading the due list, the primer and the drill, and that reading time would land in
   the recorded minutes. Name the problem and let them start it.
8. State the time cap: 30 minutes for Easy/Medium, 20 minutes for Hard before hints start. For `verify`, 15 minutes and it must be from memory.
9. Show progress and projected finish from `stats` / `projected_finish` in one line.

End with: `Next: say "start" when you are ready, or "re-solves" to switch.`

Never show any solution code in this skill.
