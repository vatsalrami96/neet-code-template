---
name: done
description: Close the day. Writes the log, regenerates the schedule, rebuilds and republishes the dashboard, commits, and gives a three-line summary (weekly stats on the light day). Trigger on "done for today", "stopping", "that's it", "wrapping up", or /done.
---

# done

1. If a problem is still in progress (`inprogress` non-empty) ask in one line whether it was accepted (then run `sync`) or abandoned (clear it: it just stays in the queue).
2. Write a one-line summary of the day yourself: what they did, the one thing to remember (an insight or a mistake pattern). Then:
   ```
   python3 scripts/plan.py close --summary "<that line>"
   python3 scripts/plan.py stats --json
   python3 dashboard/build.py
   ```
3. Publish the dashboard with the `Artifact` tool, `file_path: dashboard/index.html`.
   - If `dashboard/ARTIFACT_URL` exists, pass its contents as `url` so it republishes in place. Do not change the icon.
   - If it does not (first close), publish without `url`, icon `chart`, then write the returned URL to `dashboard/ARTIFACT_URL` and give it to them once.
4. Commit: `git add -A && git commit -q -m "day <N>: <n> new, <n> verify, <n> re-solve"` (include the attribution line from the session reminder if one is present).
5. Summary, three lines max:
   - what got done vs planned (and what rolled forward, without apology),
   - the number that moved (re-solve clean rate, hints per problem, median Medium time, or streak),
   - tomorrow's first item.
6. On the light day (Sunday) or every seventh day, add the weekly review: the stats table (re-solve clean rate, explain clean rate, hints per new, median Medium minutes, adherence, top error category), the weak-spot list, and one adjustment you recommend (slow down, cut something unused, add a mock). Ask nothing; state it.
7. Leadership Principles nudge on Tuesday and Friday: "20 minutes on one story in amazon/leadership-principles.md, which principle?" Skip if they already did one this week.

End with: `Tomorrow: say "start".`
