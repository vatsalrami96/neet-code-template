#!/usr/bin/env python3
"""Invariant tests for the plan engine.

Runs against a temp copy of plan/problems.json that is rewound to a pristine day-0 state
(see `pristine`), so the suite stays green no matter how much real progress has been
recorded. Only the build-time shape of the file - sections, problem order, difficulties,
Amazon scores, interleave/other-lang/no-lc-accept flags - is taken from the live file.
`TestLiveState` is the one place the real, un-rewound file is checked.

    python3 scripts/test_plan.py
"""
import argparse, json, os, shutil, sys, tempfile, unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, "plan", "problems.json")
START = date(2026, 9, 18)

# Flags the engine awards while work happens. Build-time and import flags (interleave, other-lang,
# no-lc-accept) describe the problem itself and must survive the rewind.
EARNED_FLAGS = {"weak", "mastered", "failed-verify", "solution-needed", "explain-failed", "deferred"}

# Inverse of record_attempt's status transitions: verify -> verified, new -> solved,
# verify+wrong -> todo with failed-verify.
REWIND_STATUS = {"verified": "solved_unverified", "solved": "todo"}


def pristine(d):
    """Rewind a loaded state to day 0, in place. Keeps the build-time shape, drops all progress."""
    for p in d["problems"]:
        if p["status"] == "todo" and "failed-verify" in p["flags"]:
            p["status"] = "solved_unverified"
        else:
            p["status"] = REWIND_STATUS.get(p["status"], p["status"])
        p["attempts"] = []
        p["resolve_stage"] = 0
        p["next_resolve"] = None
        p["flags"] = [f for f in p["flags"] if f not in EARNED_FLAGS]
        for field in ("insight", "complexity", "alternatives", "explanation"):
            p[field] = ""
    d["days"] = {}
    d["mocks"] = []
    d["drills"] = []
    d["start_times"] = {}
    d["inprogress"] = {}
    d["meta"]["start_date"] = P.S(START)
    d["meta"]["mode"] = "active"
    d["meta"]["interview_date"] = None
    return d


def core_in_progress(d):
    """Any todo problem, for populating `inprogress` in tests."""
    return next(p["id"] for p in d["problems"] if p["status"] == "todo")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "plan"))
        P.DATA = os.path.join(self.tmp, "plan", "problems.json")
        P.SCHEDULE_MD = os.path.join(self.tmp, "plan", "schedule.md")
        P.LOG_MD = os.path.join(self.tmp, "plan", "log.md")
        if os.path.exists(LIVE):
            shutil.copy(LIVE, P.DATA)
        else:
            # fresh clone, before `plan.py init` has ever run: build the fixture from the catalogue
            P.cmd_init(argparse.Namespace(start_date=P.S(START), light_day="Sunday", daily_minutes=240,
                                          new_per_day=3, resolve_per_day=4, level="SDE2", premium=False, name=None, force=True))
        d = pristine(P.load()); P.assign_interleave(d); P.save(d)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def sim(self):
        d = P.load()
        return d, P.simulate(d, START)

    def _seed(self):
        """Force a handful of problems into the states _progress needs, so the suite behaves the
        same on a freshly initialised repo and on one with months of recorded work. Idempotent."""
        d = P.load()
        core = sorted((p for p in d["problems"] if not p["gap"]), key=lambda p: (p["section"], p["order"]))
        picks = core[:4]
        for p in picks:
            p["attempts"] = []; p["resolve_stage"] = 0; p["next_resolve"] = None; p["flags"] = []
        for p in picks[:3]:
            p["status"] = "solved_unverified"; p["solved_on"] = {"neetcode": True, "leetcode": True}
        picks[3]["status"] = "todo"
        d["days"] = {}; d["mocks"] = []; d["drills"] = []; d["start_times"] = {}; d["inprogress"] = {}
        P.save(d)
        self.seeded = [p["id"] for p in picks]
        return self.seeded


class TestSchedule(Base):
    def test_every_problem_scheduled_once(self):
        d, (days, finish) = self.sim()
        seen = {}
        for pl in days:
            for pid in pl["verify"] + pl["new"] + pl["interleave"]:
                seen[pid] = seen.get(pid, 0) + 1
        expected = {p["id"] for p in d["problems"] if "deferred" not in p["flags"]}
        self.assertEqual(set(seen), expected)
        self.assertTrue(all(v == 1 for v in seen.values()))
        self.assertIsNotNone(finish)

    def test_neetcode_order_within_section(self):
        d, (days, _) = self.sim()
        ids = P.by_id(d)
        first = {}
        for i, pl in enumerate(days):
            for pid in pl["verify"] + pl["new"]:
                first[pid] = i
        for s in d["sections"]:
            ps = [p for p in d["problems"] if p["section"] == s["id"] and "interleave" not in p["flags"]]
            verify = sorted([p for p in ps if p["status"] == "solved_unverified"], key=lambda p: p["order"])
            new = sorted([p for p in ps if p["status"] == "todo"], key=lambda p: p["order"])
            for group in (verify, new):
                days_idx = [first[p["id"]] for p in group]
                self.assertEqual(days_idx, sorted(days_idx), f"order broken in {s['id']}")
            if verify and new:
                self.assertLessEqual(max(first[p["id"]] for p in verify), min(first[p["id"]] for p in new))

    def test_prerequisites(self):
        d, (days, _) = self.sim()
        ids = P.by_id(d)
        first = {}
        seq = 0
        for pl in days:
            for pid in pl["interleave"] + pl["verify"] + pl["new"]:
                first[pid] = seq; seq += 1
        bases = P.prereq_bases(d["problems"])
        for b in bases:
            base = ids[b]
            for p in d["problems"]:
                if p["section"] == base["section"] and p["title"].lower().startswith(base["title"].lower()) and p["id"] != b:
                    self.assertLess(first[b], first[p["id"]], f"{base['title']} must precede {p['title']}")

    def test_daily_budget_and_light_day(self):
        d, (days, _) = self.sim()
        ids = P.by_id(d)
        for pl in days:
            day = P.D(pl["date"])
            if pl["light"]:
                self.assertEqual(pl["verify"] + pl["new"] + pl["interleave"], [])
                continue
            cost = P.DRILL_MIN + len(pl["verify"]) * P.COST_VERIFY
            cost += sum(P.COST_NEW[ids[x]["difficulty"]] for x in pl["new"] + pl["interleave"])
            cost += sum(P.RESOLVE_COST[k] for k in pl.get("resolve_kinds", {}).values())
            self.assertLessEqual(cost, d["meta"]["daily_minutes"] + 30, f"{pl['date']} over budget: {cost}")
            self.assertLessEqual(len(pl["new"]) + len(pl["interleave"]), d["meta"]["new_per_day"])

    def test_interleave_timing(self):
        d, (days, _) = self.sim()
        for i, pl in enumerate(days):
            if pl["interleave"]:
                self.assertGreaterEqual(P.day_index(d, P.D(pl["date"])), P.INTERLEAVE_START_DAY)
                self.assertLessEqual(len(pl["interleave"]), 1)
        self.assertTrue(any(pl["interleave"] for pl in days))

    def test_light_day_is_sunday(self):
        d, (days, _) = self.sim()
        for pl in days:
            self.assertEqual(pl["light"], pl["weekday"] == "Sunday")

    def test_deterministic(self):
        d1, (a, f1) = self.sim()
        d2, (b, f2) = self.sim()
        self.assertEqual(a, b); self.assertEqual(f1, f2)


class TestFlows(Base):
    def _rec(self, pid, typ, result, day, **kw):
        d = P.load(); P.record_attempt(d, pid, typ, result, day, **kw); P.save(d); return P.by_id(P.load())[pid]

    def test_new_clean_schedules_resolve_by_tier(self):
        p = self._rec("lru-cache", "new", "clean", START)              # tier A (79.6)
        self.assertEqual(p["status"], "solved"); self.assertEqual(p["next_resolve"], P.S(START + timedelta(days=3)))
        p = self._rec("design-twitter", "new", "clean", START)         # tier C (14.3)
        self.assertEqual(p["next_resolve"], P.S(START + timedelta(days=4)))

    def test_resolve_progression_and_failure(self):
        self._rec("lru-cache", "new", "clean", START)
        p = self._rec("lru-cache", "resolve", "clean", START + timedelta(days=3))
        self.assertEqual(p["resolve_stage"], 1); self.assertEqual(p["next_resolve"], P.S(START + timedelta(days=10)))
        p = self._rec("lru-cache", "resolve", "wrong", START + timedelta(days=10))
        self.assertEqual(p["resolve_stage"], 0); self.assertIn("weak", p["flags"])
        self.assertEqual(p["next_resolve"], P.S(START + timedelta(days=13)))
        p = self._rec("lru-cache", "resolve", "clean", START + timedelta(days=13))
        p = self._rec("lru-cache", "resolve", "clean", START + timedelta(days=20))
        p = self._rec("lru-cache", "resolve", "clean", START + timedelta(days=41))
        self.assertIsNone(p["next_resolve"]); self.assertIn("mastered", p["flags"])

    def test_verify_wrong_reenters_queue_as_new(self):
        p = self._rec("two-sum", "verify", "wrong", START)
        self.assertEqual(p["status"], "todo"); self.assertIn("failed-verify", p["flags"])
        d = P.load(); main, _ = P.work_queue(d)
        kinds = {pid: k for (q, k) in main for pid in [q["id"]]}
        self.assertEqual(kinds["two-sum"], "new")
        self.assertEqual(P.tier(p), "A")  # flagged -> full re-solve ladder

    def test_solution_needed_flag(self):
        p = self._rec("coin-change", "new", "solution", START)
        self.assertIn("solution-needed", p["flags"]); self.assertEqual(p["status"], "solved")

    def test_today_idempotent_and_close_rolls_forward(self):
        class A: date = P.S(START); json = True
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): P.cmd_today(A)
        one = json.loads(buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): P.cmd_today(A)
        two = json.loads(buf.getvalue())
        self.assertEqual([i["id"] for i in one["items"]], [i["id"] for i in two["items"]])
        # do one item, close, next day: the rest come back, nothing duplicated
        first = one["items"][0]["id"]
        self._rec(first, "verify", "clean", START)
        d = P.load(); P.close_day(d, START); P.save(d)
        self.assertTrue(P.load()["days"][P.S(START)]["closed"])
        class B: date = P.S(START + timedelta(days=1)); json = True
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): P.cmd_today(B)
        nxt = json.loads(buf.getvalue())
        ids = [i["id"] for i in nxt["items"]]
        self.assertNotIn(first, ids); self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(i["id"] for i in one["items"][1:]) <= set(ids))

    def test_auto_close_previous_day(self):
        class A: date = P.S(START); json = True
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()): P.cmd_today(A)
        class B: date = P.S(START + timedelta(days=2)); json = True
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): P.cmd_today(B)
        out = json.loads(buf.getvalue())
        self.assertIn(P.S(START), out["auto_closed"])

    def test_start_twice_no_duplication(self):
        d = P.load(); d.setdefault("inprogress", {})["two-sum"] = {"start": "2026-09-18T09:00:00", "hints": 0}
        d["inprogress"]["two-sum"] = {"start": "2026-09-18T09:05:00", "hints": 0}
        self.assertEqual(len(d["inprogress"]), 1)

    def test_compression_defers_tail_never_prereq_base(self):
        d = P.load(); d["meta"]["interview_date"] = P.S(START + timedelta(days=24)); P.save(d)
        d = P.load(); dropped = P.compress_for_deadline(d, START); P.save(d)
        self.assertTrue(dropped)
        ids = P.by_id(d); bases = P.prereq_bases(d["problems"])
        for pid in dropped:
            self.assertNotIn(pid, bases)
        _, finish = P.simulate(d, START)
        self.assertIsNotNone(finish)
        remaining_todo = [p for p in d["problems"] if p["status"] == "todo" and "deferred" not in p["flags"]]
        exhausted = all(p["id"] in bases for p in remaining_todo)
        self.assertTrue(finish <= START + timedelta(days=24 - P.PREP_DAYS) or exhausted)
        # clearing the date restores everything
        for p in d["problems"]:
            p["flags"] = [f for f in p["flags"] if f != "deferred"]
        self.assertFalse(any("deferred" in p["flags"] for p in d["problems"]))

    def test_maintenance_mode_has_no_new(self):
        d = P.load(); d["meta"]["mode"] = "maintenance"; P.save(d)
        pl = P.plan_day(P.load(), START + timedelta(days=1))
        self.assertEqual(pl["new"] + pl["verify"] + pl["interleave"], [])


class TestRewindIsProgressProof(Base):
    """The suite must stay green as real work accumulates. Record progress, rewind, compare."""

    def test_rewind_survives_recorded_progress(self):
        self._seed()
        baseline = pristine(P.load())
        # simulate a few days of real work of every kind
        self._progress()
        rewound = pristine(P.load())
        self.assertEqual(
            {p["id"]: (p["status"], p["resolve_stage"], p["next_resolve"], sorted(p["flags"]), p["attempts"])
             for p in rewound["problems"]},
            {p["id"]: (p["status"], p["resolve_stage"], p["next_resolve"], sorted(p["flags"]), p["attempts"])
             for p in baseline["problems"]},
        )
        self.assertEqual(rewound["days"], {})
        self.assertEqual(rewound["inprogress"], {})

    def test_schedule_invariants_hold_after_progress(self):
        self._progress()
        d = pristine(P.load()); P.assign_interleave(d); P.save(d)
        d = P.load(); days, finish = P.simulate(d, START)
        seen = [pid for pl in days for pid in pl["verify"] + pl["new"] + pl["interleave"]]
        expected = {p["id"] for p in d["problems"] if "deferred" not in p["flags"]}
        self.assertEqual(set(seen), expected)
        self.assertEqual(len(seen), len(set(seen)))
        self.assertIsNotNone(finish)

    def _progress(self):
        a, b, c, fresh = self._seed()
        d = P.load()
        P.record_attempt(d, a, "verify", "clean", START)
        P.record_attempt(d, b, "verify", "sloppy", START, errors=["complexity"])
        P.record_attempt(d, c, "verify", "wrong", START)                        # -> todo + failed-verify
        P.record_attempt(d, fresh, "new", "solution", START)                    # -> solution-needed
        P.record_attempt(d, a, "resolve", "wrong", START + timedelta(days=3))   # -> weak
        d.setdefault("inprogress", {})[core_in_progress(d)] = {"start": "2026-09-21T09:00:00", "hints": 2}
        P.save(d)
        d = P.load(); P.close_day(d, START); P.save(d)


@unittest.skipUnless(os.path.exists(LIVE), "no plan/problems.json yet - run `plan.py init` first")
class TestLiveState(unittest.TestCase):
    """The one check against the real, un-rewound plan/problems.json. Skipped before `init`."""

    def setUp(self):
        self._data = P.DATA
        P.DATA = LIVE

    def tearDown(self):
        P.DATA = self._data

    def test_live_file_is_valid(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            P.cmd_validate(None)
        self.assertEqual(cm.exception.code, 0, buf.getvalue())

    def test_live_statuses_rewind_cleanly(self):
        with open(LIVE) as fh:
            d = pristine(json.load(fh))
        for p in d["problems"]:
            self.assertIn(p["status"], ("todo", "solved_unverified"),
                          f"{p['id']} did not rewind to a day-0 status")


class TestTimer(Base):
    """start / stop / hint bookkeeping on the inprogress entry."""

    class _Args:
        def __init__(self, **kw): self.__dict__.update(kw)

    def test_stop_clears_clock_and_keeps_hints(self):
        pid = "two-sum"
        P.cmd_start(self._Args(id=pid, date=None))
        P.cmd_hint(self._Args(id=pid, level="2"))
        self.assertEqual(P.load()["inprogress"][pid]["hints"], 2)
        P.cmd_stop(self._Args(id=pid))
        ip = P.load()["inprogress"][pid]
        self.assertIsNone(ip["start"], "stop must clear the clock")
        self.assertEqual(ip["hints"], 2, "stop must not discard the hint count")

    def test_restart_preserves_hints(self):
        pid = "two-sum"
        P.cmd_start(self._Args(id=pid, date=None))
        P.cmd_hint(self._Args(id=pid, level="3"))
        P.cmd_stop(self._Args(id=pid))
        P.cmd_start(self._Args(id=pid, date=None))
        ip = P.load()["inprogress"][pid]
        self.assertIsNotNone(ip["start"], "restart must set a fresh clock")
        self.assertEqual(ip["hints"], 3, "restarting the timer must not zero hints used")

    def test_stop_on_idle_problem_is_harmless(self):
        before = P.load()["inprogress"]
        P.cmd_stop(self._Args(id="two-sum"))
        self.assertEqual(P.load()["inprogress"], before)



class TestBootstrap(Base):
    """init and import-solved: the path a new clone takes before day 1."""

    class A:                      # stand-in for the argparse namespace
        def __init__(self, **kw):
            self.__dict__.update(kw)

    def _init_args(self, **kw):
        base = dict(start_date=P.S(START), light_day="Sunday", daily_minutes=240, new_per_day=3,
                    resolve_per_day=4, level="SDE2", premium=False, name=None, force=False)
        base.update(kw)
        return self.A(**base)

    def test_init_builds_a_valid_state_from_the_catalogue(self):
        os.remove(P.DATA)
        P.cmd_init(self._init_args())
        d = P.load()
        cat = json.load(open(P.CATALOGUE))
        self.assertEqual(len(d["problems"]), len(cat["problems"]))
        self.assertEqual(len(d["sections"]), len(cat["sections"]))
        self.assertEqual({p["status"] for p in d["problems"]}, {"todo"})
        self.assertTrue(all(p["attempts"] == [] and p["flags"] == [] for p in d["problems"]))
        self.assertEqual(d["meta"]["start_date"], P.S(START))
        self.assertEqual(d["days"], {})
        # and the engine can immediately plan a day off it
        pl = P.plan_day(P.load(), START)
        self.assertTrue(pl["new"])

    def test_init_records_premium_so_the_today_skill_can_read_it(self):
        os.remove(P.DATA)
        P.cmd_init(self._init_args())
        self.assertIs(P.load()["meta"]["premium"], False)
        os.remove(P.DATA)
        P.cmd_init(self._init_args(premium=True))
        self.assertIs(P.load()["meta"]["premium"], True)

    def test_init_refuses_to_clobber_existing_state(self):
        with self.assertRaises(SystemExit):
            P.cmd_init(self._init_args())
        P.cmd_init(self._init_args(force=True))          # explicit --force is allowed
        self.assertEqual({p["status"] for p in P.load()["problems"]}, {"todo"})

    def test_init_rejects_a_bad_light_day(self):
        os.remove(P.DATA)
        with self.assertRaises(SystemExit):
            P.cmd_init(self._init_args(light_day="Funday"))

    def _import(self, payload, source="leetcode", name="acc.json"):
        f = os.path.join(self.tmp, name)
        with open(f, "w") as fh:
            fh.write(payload if isinstance(payload, str) else json.dumps(payload))
        P.cmd_import_solved(self.A(file=f, source=source, dry_run=False))
        return P.load()

    def test_import_marks_unverified_and_flags_other_languages(self):
        os.remove(P.DATA); P.cmd_init(self._init_args())
        d = self._import({"two-sum": {"lang": "python3"}, "valid-parentheses": {"lang": "cpp"},
                          "not-a-real-problem": {"lang": "python3"}})
        ids = P.by_id(d)
        self.assertEqual(ids["two-sum"]["status"], "solved_unverified")
        self.assertTrue(ids["two-sum"]["solved_on"]["leetcode"])
        self.assertNotIn("other-lang", ids["two-sum"]["flags"])
        self.assertIn("other-lang", ids["valid-parentheses"]["flags"])
        self.assertNotIn("not-a-real-problem", ids)

    def test_import_accepts_text_lines_and_urls(self):
        os.remove(P.DATA); P.cmd_init(self._init_args())
        d = self._import("1|Two Sum\nhttps://leetcode.com/problems/group-anagrams/\nmerge-two-sorted-lists\n",
                         name="acc.txt")
        ids = P.by_id(d)
        for slug in ("two-sum", "group-anagrams", "merge-two-sorted-lists"):
            self.assertEqual(ids[slug]["status"], "solved_unverified", slug)

    def test_neetcode_only_import_is_flagged_as_never_accepted(self):
        os.remove(P.DATA); P.cmd_init(self._init_args())
        d = self._import("two-sum\n", source="neetcode", name="nc.txt")
        self.assertIn("no-lc-accept", P.by_id(d)["two-sum"]["flags"])

    def test_import_leaves_finished_problems_alone(self):
        os.remove(P.DATA); P.cmd_init(self._init_args())
        d = P.load(); P.record_attempt(d, "two-sum", "new", "clean", START); P.save(d)
        before = P.by_id(P.load())["two-sum"]["status"]
        d = self._import({"two-sum": {"lang": "cpp"}})
        self.assertEqual(P.by_id(d)["two-sum"]["status"], before)
        self.assertNotIn("other-lang", P.by_id(d)["two-sum"]["flags"])

    def test_dry_run_writes_nothing(self):
        os.remove(P.DATA); P.cmd_init(self._init_args())
        f = os.path.join(self.tmp, "acc.json")
        open(f, "w").write(json.dumps({"two-sum": {"lang": "cpp"}}))
        P.cmd_import_solved(self.A(file=f, source="leetcode", dry_run=True))
        self.assertEqual(P.by_id(P.load())["two-sum"]["status"], "todo")



class TestPreflight(Base):
    """Pre-flight (interview-process steps 1-5) is captured before the clock and graded at sync."""

    class A:
        def __init__(self, **kw): self.__dict__.update(kw)

    def _pid(self):
        # _seed puts the first three core problems into solved_unverified, so these tests do not
        # depend on the repo already having history (a fresh `init` has none).
        return self._seed()[0]

    def test_preflight_before_start_is_marked_on_time(self):
        pid = self._pid()
        P.cmd_preflight(self.A(id=pid, text="brute force is every pair O(n^2); two pointers O(n)"))
        ip = P.load()["inprogress"][pid]
        self.assertFalse(ip["preflight"]["late"])
        self.assertTrue(ip["preflight"]["at"])

    def test_preflight_after_start_is_flagged_late(self):
        pid = self._pid()
        P.cmd_start(self.A(id=pid, date=None))
        P.cmd_preflight(self.A(id=pid, text="thought of it afterwards"))
        self.assertTrue(P.load()["inprogress"][pid]["preflight"]["late"])

    def test_preflight_survives_onto_the_attempt(self):
        pid = self._pid()
        P.cmd_preflight(self.A(id=pid, text="set + only start where num-1 absent"))
        d = P.load()
        att = P.record_attempt(d, pid, "verify", "clean", START, preflight=8, traced=True)
        P.save(d)
        self.assertEqual(att["preflight"]["score"], 8)
        self.assertTrue(att["preflight"]["logged"])
        self.assertIn("num-1", att["preflight"]["text"])
        self.assertTrue(att["traced"])
        # and the day record carries the score so close/stats can see it
        done = P.load()["days"][P.S(START)]["done"][-1]
        self.assertEqual(done["preflight"], 8)
        self.assertTrue(done["traced"])

    def test_score_without_a_logged_preflight_is_marked_unlogged(self):
        pid = self._pid()
        d = P.load()
        att = P.record_attempt(d, pid, "verify", "clean", START, preflight=4)
        P.save(d)
        self.assertFalse(att["preflight"]["logged"])

    def test_attempts_without_preflight_stay_unchanged(self):
        pid = self._pid()
        d = P.load()
        att = P.record_attempt(d, pid, "verify", "clean", START)
        P.save(d)
        self.assertNotIn("preflight", att)
        self.assertNotIn("traced", att)

    def test_stats_report_preflight_and_traced(self):
        picks = self._seed()[:2]
        for pid, score, tr in zip(picks, (6, 10), (True, False)):
            P.cmd_preflight(self.A(id=pid, text="x"))
            d = P.load()
            P.record_attempt(d, pid, "verify", "clean", START, preflight=score, traced=tr)
            P.save(d)
        st = P.stats(P.load(), START)
        self.assertEqual(st["preflight_score_week"], 8.0)
        self.assertEqual(st["preflight_logged_rate_week"], 100)
        self.assertEqual(st["traced_rate_week"], 50)

    def test_score_must_be_within_range(self):
        pid = self._pid()
        with self.assertRaises(SystemExit):
            P.cmd_record(self.A(id=pid, type="verify", result="clean", minutes=5, hints=0, explain="clean",
                                errors=None, note=None, date=None, preflight=11, traced=False, not_traced=False))


if __name__ == "__main__":
    unittest.main(verbosity=1)
