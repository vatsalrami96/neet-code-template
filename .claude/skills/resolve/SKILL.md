---
name: resolve
description: Run the day's re-solves one at a time: fresh attempt from memory, diff against the saved solution, grade, reschedule. Explain-only re-solves are a two-minute spoken recall. Trigger on "re-solves", "review time", "the old ones", or /resolve.
---

# resolve

1. `python3 scripts/plan.py today --json`. Take the `resolve` items in order. If none are due, say so and offer `drill`.
2. For each item, one at a time:

   **kind `code`** (12 minutes):
   - Say the title and difficulty only. No hints, no section name, no link to the old solution.
   - Create `resolves/<YYYY-MM-DD>-<slug>.py` containing only a one-line comment with the title and the LeetCode signature if they ask for it.
   - They write it from memory in that file (or on LeetCode; their choice). Timer 12 minutes.
   - When they say done: read their file (or fetch from LeetCode if they submitted) and read `solutions/<section>/<lcid>-<slug>.py`.
     Compare approach and complexity, then correctness by walking two inputs (one normal, one edge) through their code by hand.
   - Grade: **clean** (correct, same or better complexity, under 12 minutes, no peeking), **sloppy** (correct but slow, messy, or needed a nudge),
     **wrong** (incorrect or gave up). Say which and why in two lines. If wrong, show *their* bug, not the full solution; they can reopen the saved file themselves.

   **kind `explain`** (5 minutes):
   - "In two to three sentences: approach, the invariant, time and space." Grade clean/sloppy/wrong the same way.

3. Record each: `python3 scripts/plan.py record <id> --type resolve --result <clean|sloppy|wrong> [--minutes m] [--errors ...]`.
   Append a `History:` entry to the solution file's header.
4. After all items: one line per problem with the result and the next re-solve date, and the running weekly re-solve clean rate from `python3 scripts/plan.py stats`.

Rules: they may not open the old solution during a code re-solve. If they say they peeked, grade it sloppy at best and say why.
Wrong re-solves are useful data, not failures; say that once, not every time.

End with: `Next: say "start" to go back to new problems, or "done for today".`
