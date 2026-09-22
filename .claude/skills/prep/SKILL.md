---
name: prep
description: Interview date handling and the night-before pack. Sets the interview date (which compresses the plan and pulls mocks forward) and generates prep/pack-<date>.md from their own notes, weak spots, templates, checklists, and story bank. Trigger on "interview on <date>", "I have an interview", "prep pack", "night before", "cheat sheet", or /prep.
---

# prep

## When they give a date
1. `python3 scripts/plan.py set-date YYYY-MM-DD`. Report: the new projected finish, how many problems were deferred and which sections they came from, and that the last three days before the date are prep-only.
2. Adjust mocks: with fewer than 14 days left, two mocks a week; the last one three days before, `onsite` format. Say the dates.
3. If the LLD gate is still closed (`lld/README.md` has no resource), say so once; SDE2 loops usually include that round.
4. Regenerate the dashboard (`python3 dashboard/build.py` and republish).

## The night-before pack (three days out, or on request)
1. `python3 scripts/prep_pack.py` writes `prep/pack-<date>.md`. Read it back and tighten: the weak-spot section should have an insight line for every problem; if any are blank, ask them for the one-line insight now and record it with `plan.py note`.
2. Add a "Day of" section at the top, in their words after a two-minute chat: how they start a problem (the seven steps in their own phrasing), their personal top three mistakes from the error log, and the two LP stories they are most confident in.
3. Publish the pack as an Artifact (private) so they can read it on their phone. Favicon 📋. Keep the URL in `prep/ARTIFACT_URL`.
4. Say once: no new problems in the last three days. Re-read the pack, one light re-solve session, sleep.

## Clearing a date
`python3 scripts/plan.py set-date none` restores deferred problems. Regenerate the schedule and dashboard.

End with: `Next: say "start", or "mock" to rehearse.`
