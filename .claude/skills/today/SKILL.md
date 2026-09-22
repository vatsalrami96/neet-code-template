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
8. **Pre-flight** (`new` and `verify` only, never re-solves). Before the clock, walk the first five steps of
   `reference/interview-process.md`. Steps 1 to 3 carry no algorithmic information, so answer them like an
   interviewer would; steps 4 and 5 you log and say nothing about.
   - **1 Restate** - correct a misread. Factual only.
   - **2 Constraints** - answer them; they are on the page. Then ask for the target complexity that follows
     ("Constraints to complexity" in that file). The target is an output of this step, not of step 5.
   - **3 Example** - the candidate walks one small case by hand and states the expected output. Confirm or
     correct it. This is the example they dry-run in step 7, so keep it.
   - **4 Brute force + cost** and **5 Pattern + invariant + target complexity, and why over brute force** -
     **log verbatim and give no signal at all.** No nod, no correction, no "interesting", no follow-up question.
     Confirming an approach here is a free level-2 hint and it destroys the measurement.
   ```
   python3 scripts/plan.py preflight <id> "<steps 4 and 5, their words, verbatim>"
   ```
   Keep it to about five minutes - an interview budgets roughly that for steps 1 to 5, and the gap between
   `preflight` and `start` is recorded, so a twenty-minute think shows up. Say the elapsed figure at sync,
   do not police it live.
   Log it **before** `plan.py start`. The command warns if the clock is already running, and a late pre-flight
   scores 0 - it cannot show the thinking came before the coding, which is the only thing it measures.
   If they want to skip it, that is their call: say "skipped, scores 0" in three words and move on. Do not argue.
9. State the time cap: 30 minutes for Easy/Medium, 20 minutes for Hard before hints start. For `verify`, 15 minutes and it must be from memory.
10. Show progress and projected finish from `stats` / `projected_finish` in one line.

End with: `Next: say "ready" to start the clock, or "re-solves" to switch.`

## During the solve (not part of the morning run)

These fire later, on their own, once the morning list is done. Do not say them during steps 1 to 10.

- When they say they are starting (`ready`, `starting`, `go`): run `python3 scripts/plan.py start <id>`, confirm
  in one line with the cap, and nothing else.
- **Before they submit**, once: dry-run the step-3 example through the code they wrote, then one edge case, then
  state final time and space read off the code, not off the step-5 prediction. Say nothing about whether the
  trace is right. If they have already submitted when they tell you, skip it - do not ask them to pretend.

Never show any solution code in this skill.
