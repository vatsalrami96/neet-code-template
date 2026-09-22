---
name: drill
description: Light-day and warm-up drills. Template typing from memory (reference/templates), a longer pattern-recognition set, and Python fluency spot checks. Trigger on "drill", "templates", "recognition", or /drill.
---

# drill

Ask which one, or run all three on the light day (about 40 minutes total).

## Scope rule (applies to every drill below)

Drills only cover ground they have already solved. Never reach forward into an unsolved section: a drill is warm-up on
what they own, not a preview. Get the covered sections first and do not go outside them:

```
python3 -c "import json;ps=json.load(open('plan/problems.json'))['problems'];print(sorted({p['section'] for p in ps if p['status'] in ('solved','verified')}))"
```

`solved_unverified` does not count as covered. Those verifies are done from memory, so drilling them hands the candidate the answer.

If a drill has nothing in scope yet (early days, no template exists for a covered section), say so in one line and skip
that drill. Skipping is correct; substituting something forward-looking is not.

## Template drill (15 to 20 minutes)
1. Pick two or three from `reference/templates/` **whose pattern belongs to a covered section**. Rotate within that set.
   Sections 01 and 02 have no template file, so this drill does not run until they have cleared a section that does.
2. For each: say the name only ("binary search, first_true form"). They type it from memory into `resolves/drill-<date>-<name>.py`. Three minutes each.
3. Compare with the reference file: correctness of the invariant, the classic bug named in the file's docstring, loop bounds. Say pass or the bug in one line.
4. Record: `python3 scripts/plan.py drill --type template --score <passed> --total <n>`.

## Recognition drill (10 minutes)
1. **Source: problems that are not in `plan/problems.json` at all.** Every id in that file is either scheduled or awaiting
   a verify, including the twelve in `99-amazon-gap`; using one burns their first real attempt at it. Check before writing
   a statement:

   ```
   python3 -c "import json,sys;ids={p['id'] for p in json.load(open('plan/problems.json'))['problems']};print([s for s in sys.argv[1:] if s in ids] or 'all clear')" <slug> <slug> ...
   ```

   Draw from the wider LeetCode pool instead: other problems on the Amazon six-month tag, or variants of the same pattern.
2. Ten paraphrased statements, two lines each, no titles. **All ten sit inside covered sections.** Include one trap: a
   statement that looks like a pattern they know but breaks its precondition (negative numbers under a sliding window,
   an unsorted array under two pointers). The trap must also be within covered ground.
3. State a constraint with each one. They answer with the pattern, one line of approach, and time and space.
4. Grade right/wrong. Record: `plan.py drill --type recognition --score <right> --total 10`.
   If they stop early, record what they actually attempted (`--score 1 --total 2`), not the full ten.
5. For the wrong ones, one sentence each on the tell they missed.
6. Complexity counts as a graded half. A right pattern with a wrong bound is wrong, and is tagged `complexity`.

## Python fluency (5 minutes)
Three quick questions from `reference/python-fluency.md` (a gotcha, a stdlib call, a cost). Not recorded; just say which they should re-read.

Rules: no code shown before they attempt. Keep it brisk. The drill is warm-up, not a lesson.

End with: `Next: say "re-solves", "start", or "done for today".`
