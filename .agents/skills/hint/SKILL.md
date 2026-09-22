---
name: hint
description: Give the next tiered hint for the problem in progress without spoiling it. Level 1 names the stuck-protocol move, level 2 gives the key observation, level 3 gives the approach in words. Full solution only on explicit request, and it is logged. Trigger on "stuck", "hint", "nudge", "I don't get it", or /hint.
---

# hint

1. Find the problem in progress: read `inprogress` from `plan/problems.json` (`python3 -c "import json;print(json.load(open('plan/problems.json')).get('inprogress'))"`).
   If more than one or none, ask which problem in one line.
2. Current hint level is `inprogress[id].hints` (0 to 3, or "solution"). The next level is one higher, unless they ask for a specific level.
3. Give exactly one level:
   - **Level 1**: which move from `reference/stuck-protocol.md` applies, in one sentence, plus the pattern *family* if they have done that section (e.g. "this is a stack section problem; ask what you need to know at each index"). No observation, no approach.
   - **Level 2**: the key observation, one to three sentences. The fact that unlocks the problem, not how to use it. Example for Trapping Rain Water: "water above i depends only on the smaller of the max-to-the-left and max-to-the-right."
   - **Level 3**: the approach in words. Data structure, loop shape, invariant, complexity. Still no code. No variable names.
   - **Solution**: only if they explicitly say "show me the solution" or equivalent. Show clean Python with a two-line explanation.
     Then tell them to close it and re-implement from memory before submitting. This attempt will be recorded as `solution`.
4. Log it: `python3 scripts/plan.py hint <id> <level|solution>`.
5. If they are on a `verify` item, state the cost of the next rung accurately. `sync` step 6 is what actually writes the
   state, so quote its thresholds, not a stricter guess:
   - **level 1** - no effect on the grade. `clean` allows hints 0 or 1.
   - **level 2** - the attempt is recorded `sloppy`. It still counts as verified and does not come back as a new problem.
   - **level 3 or solution** - result `wrong`: the problem goes back to `todo` with `failed-verify` and is re-solved from
     scratch (AGENTS.md, "Attempt types and statuses").
   Never overstate this. Telling them a level-2 hint costs them verify status makes them push on alone against a penalty
   that does not exist, and the minutes that buys are wasted.
6. Time check: if they have been on a Medium for more than 35 minutes or a Hard for more than 25 with level 3 given, suggest taking the solution, re-implementing, and moving on. The re-solve in three days is where it sticks.

End with: `Next: say "stuck" again for the next level, "accepted" when it passes, or "show me the solution".`

Never give code below the solution level. Never give level 3 wording that is effectively code.
