---
name: mock
description: Run a timed mock interview as the interviewer. Rotates formats (online assessment, phone screen, onsite; design once the LLD gate is open), picks unseen problems, probes like Amazon does, scores against the seven-step rubric, and records it. Trigger on "mock", "interview practice", "grill me", or /mock.
---

# mock

## Setup
1. Format: rotate through `oa`, `phone`, `onsite` (check `mocks` in `plan/problems.json` for the last one). Use `design` only if `lld/README.md` has a resource and they ask.
   - `oa`: two problems, 70 minutes total, long story-wrapped statements, no interviewer interaction. Write the statements yourself in OA style (a scenario, then the actual ask, then constraints).
   - `phone`: 5 minutes of one Leadership Principles question, then one Medium in 35 minutes, talk-through required, you probe.
   - `onsite`: 15 minutes of two LP questions, then one Medium or Hard in 35 minutes, then a follow-up variation. Plain editor, no autocomplete: they code in `mocks/<date>-<n>.py`.
2. Pick problems with status `todo` that are not in today's plan, Amazon score >= 40 preferred, at least one Medium. For `oa` prefer one from the Amazon list beyond the 150 (paraphrase from memory; do not name the LeetCode title until the debrief).
3. Say the format, the clock, and the rules once. Then stay in character: neutral, brief, no teaching until the debrief.

## Running it
- They must go through steps 1 to 5 of `reference/interview-process.md` out loud before writing code. If they start coding first, ask "walk me through your approach first" once, then let it go and note it.
- Probe like Amazon: "what's the complexity", "what if the input doesn't fit in memory", "can you do it without the extra array", "what breaks if the values are negative".
- Give nothing away. If they are stuck for 10 minutes, one nudge of the level-1 kind, and note it.
- Time calls at halfway and five minutes left.

## Debrief
1. Score each problem on the seven steps (0 to 2 each, max 14) and say the total and the two weakest steps.
2. Correctness: walk one edge input through their code. Say what fails, if anything.
3. Communication: one specific thing that was clear, one that was not.
4. Record: `python3 scripts/plan.py mock --format <f> --problems <slug,slug> --score <total> --notes "<two weakest steps; nudge used?>"`.
   Also record each problem as an attempt so it enters the re-solve ladder: `plan.py record <id> --type new --result <clean|sloppy|wrong|solution> --minutes <m> --hints <0|1> --explain <grade>`.
   Save their code to `solutions/` with the standard header if it was correct; otherwise leave it in `mocks/`.
5. For `onsite`/`phone`: one line of feedback on the LP answers (STAR present? a number in the result? "I" not "we"?).

End with: `Next: say "start" or "done for today".`
