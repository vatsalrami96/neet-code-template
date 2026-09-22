---
name: sync
description: After LeetCode accepts a solution. Confirms the accept through the browser, runs the explain-back and checks, reviews the code, saves it to solutions/, and records the attempt. Trigger on "accepted", "done with it", "passed", "solved it", "sync", or /sync.
---

# sync

## 1. Which problem
The problem in progress (`inprogress` in `plan/problems.json`), or the one they name. If several are claimed, handle them one at a time, in the order they did them.

## 2. Confirm on LeetCode
In their Chrome LeetCode tab (see "LeetCode access" in CLAUDE.md - Chrome, not the built-in pane) run (from `scripts/leetcode.js`)
`latestAccepted([<slug>], <start time as unix seconds>)`. **Always pass the logged `start`** - without it the failure count goes
back years and silently grades a clean attempt as `sloppy`. Accept only if `id` is set and `acceptedSince` is true (or, with no
logged start, `ts` is today).
- Not accepted: say so, do not record anything, offer `hint`.
- Browser unavailable: say so, ask them to paste the accepted code, continue. Note "unverified by browser" in the record note.
Keep `failedSince` (failures in THIS attempt - this is the one that grades) and the timestamps. `failedAllTime` is context only;
if it is higher, that is old history, so do not hold it against them.
This is submission history only. LeetCode stores no run-code history, so failures against the sample cases with the Run button
are invisible - never state or imply that a `failedSince` of 0 means they had no trouble, only that they made no failed submissions.

## 3. Explain-back (before any review, no exceptions)
Ask: "Explain it as if I'm the interviewer: what the problem asks, your approach, why it's correct, time and space, and one trade-off." Two to five sentences, dictated or typed.
Grade against `reference/interview-process.md`: **clean** (all five present, correct, concise), **sloppy** (missing one or vague on why it's correct), **wrong** (approach or complexity misstated).
A trade-off that describes only the solution they built - "we use a map to get O(n)", "I could have used a different
delimiter", "we avoid recomputing" - is not present, it is missing. See the "Trade-offs" section of that file for the
required shape and the list of non-trade-offs.
Then ask, if not already covered:
- "Why is it correct?" (the invariant). One follow-up question at most.
- "Which edge cases did you check?" Compare with `reference/edge-cases.md`; name one they missed if any.
- If `failedBefore > 0`: "What was the failing case and how did you find it?" Tag the error: misread, off-by-one, wrong-ds, edge-case, tle, syntax, logic, complexity.

## 4. Fetch and save the code
Run `submissionCode(<id>)` (or `codesFor([<slug>])`). Write `solutions/<section>/<lcid padded to 4>-<slug>.py` with the header format from `CLAUDE.md`
(insight in their words from the explain-back, complexity, alternatives, verbatim explanation, history line). Then the code unchanged.
Record notes: `python3 scripts/plan.py note <id> insight "..."`, and likewise `complexity`, `alternatives`, `explanation`.

## 5. Review (short, specific)
- Complexity: confirm or correct their stated time and space.
- One edge case the code does not handle, if any, with the failing input.
- A cleaner version only if theirs is materially messier: show the diff in words or a five-line snippet, not a rewrite.
- Top-solution comparison: one sentence on what the canonical solution does differently, if anything.
- Alternatives: for Amazon score >= 40, one alternative approach and its trade-off, plus one follow-up variation an interviewer would ask ("what if it's a stream", "no extra space", "k of them").
- One thing they did well, specifically.

## 6. Record
Decide the type: `verify` if the problem's status was `solved_unverified`, else `new`.
Result:
- `clean`: hints 0 or 1, explain clean, at most one failed submission (`failedSince`).
- `sloppy`: hint level 2, or explain sloppy, or two or more failed submissions (`failedSince`).
- `solution`: hint level was `solution` (or 3 and they say they effectively needed it).
- For `verify` with hint level 3 or solution: result `wrong` (it goes back to `todo`).
Minutes: from `start` to accept timestamp if a start was logged, else from their estimate.
```
python3 scripts/plan.py record <id> --type <new|verify> --result <r> --minutes <m> --hints <n> --explain <clean|sloppy|wrong> [--errors a,b] [--note "..."]
```
Say what was recorded in one line, including the next re-solve date.

## 7. Next problem
Run `python3 scripts/plan.py today --json`; if there is a next `mixed`/`verify`/`new` item, open it in the browser.

**Do not start the clock.** They are still reading the review, and that reading time would land in the recorded minutes -
the one number `median_medium_minutes_week` depends on. Open the tab, name the problem, and let them start it.

End with: `Next: say "start" when you are ready, or "re-solves" / "done for today".`

If they say "accepted" on a problem whose clock was never started, or whose `start` is much older than the work
(they stepped away, or read a long review), do not silently trust the gap. Say the elapsed figure, ask whether it
reflects real solving time, and record their number.
