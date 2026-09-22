# NeetCode 150, coached

A prep system for the NeetCode 150, run by Claude Code (or Codex) inside this repo. You solve on LeetCode in your
own browser. The agent keeps the plan, reads your accepted submissions, schedules re-solves at spaced intervals,
makes you explain every solution before it shows you a review, tracks the errors you actually make, and publishes
a dashboard. The two phrases worth remembering are **"start"** in the morning and **"done for today"** at night.

Target is Amazon SDE2 in Python: problem ordering and re-solve frequency are weighted by Amazon's LeetCode company
tag. It works for any company, the priorities are just tuned for that one.

## What you need

- Python 3.9+ (standard library only, no pip install)
- [Claude Code](https://claude.com/claude-code) — or Codex, which reads `AGENTS.md` instead of `CLAUDE.md`
- A LeetCode account, logged in, in Chrome. A few of the 150 need Premium; the system works without it.
- Optional: a NeetCode account, if you want to import problems you have already done
- Optional: the Claude in Chrome extension, so the agent can read your accepted submissions itself. Without it,
  it falls back to its own browser pane, and failing that, asks you to paste your accepted code.

## Setup

```bash
git clone <this repo> my-prep && cd my-prep
python3 scripts/plan.py init --start-date 2026-10-01 --light-day Sunday --daily-minutes 240 --new-per-day 3
```

Add `--premium` if you have LeetCode Premium. Every flag is optional: `init` alone starts today with 4 hours a
day, 3 new problems, Sunday as the light day, no Premium.

**Make it yours.** A clone still points at this repo, which you cannot push to, and your solutions should not live
here anyway:

```bash
git remote remove origin        # or: git remote set-url origin <your own repo>
```

Your progress lives in `plan/problems.json` and `solutions/`. Commit them somewhere private if you commit them at
all — a public repo of your interview solutions is searchable.
Then open the repo in Claude Code and say **"start"**. The agent handles the rest, including asking whether you
have solved any of these before and importing that history if so.

Already solved some? Either let the agent do it, or:

```bash
python3 scripts/plan.py import-solved my-accepted.txt --source leetcode --dry-run
```

Imported problems become `solved_unverified` — you re-solve them from memory once, and only then do they count.
Accepts in a language other than Python are flagged so the verify is done in Python.

## The day

| You say | What happens |
|---|---|
| `start` | due list, section primer if a new section begins, 5-minute recognition drill, first problem opened |
| `stuck` | one rung up a three-level hint ladder — never code unless you ask outright, and it is logged if you do |
| `accepted` | reads the submission off LeetCode, makes you explain it, grades the explanation, then reviews the code and saves it |
| `re-solves` | past problems from memory in a fresh file, diffed against what you wrote last time |
| `done for today` | closes the day, writes the log, regenerates the schedule, rebuilds the dashboard |

Also: `mock` for a timed interview, `drill` for templates and pattern recognition, `interview on <date>` to
compress the whole plan around a real date, `prep pack` for the night before.

## Layout

```
CLAUDE.md / AGENTS.md  the operating manual — the agent reads this, you mostly do not
data/catalogue.json    the 150 + 12 Amazon gap problems, sections, difficulty, company scores
plan/problems.json     your state. Only scripts/plan.py writes it. Never edit it by hand.
plan/schedule.md       day-by-day projection (generated)   plan/log.md   daily log
primers/               one per section, written before you start that section
reference/             process checklist, stuck protocol, edge cases, Python fluency, code templates
solutions/             your accepted code with notes       resolves/     timed re-attempts from memory
amazon/                leadership-principles story bank (empty — fill it in), gap problems
dashboard/build.py     builds a dashboard, published as a private Artifact
```

## Honest limitations

- The Amazon frequency data was pulled 2026-09-17. It ages. Re-pull it from LeetCode's company tag if you care.
- `solutions/` ships empty on purpose. It fills with *your* code, which is the point — the notes attached to a
  solution you wrote are worth more than a reference implementation you read.
- The schedule assumes you actually do the re-solves. Skipping them makes the whole thing a checklist.
