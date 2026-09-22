#!/usr/bin/env python3
"""Plan engine. Single source of truth is plan/problems.json; this file is the only writer.

Usage (run from repo root):
  plan.py init [--start-date D] [--light-day Sunday] [--daily-minutes 240] [--new-per-day 3]
                                         create plan/problems.json from data/catalogue.json (run once)
  plan.py import-solved FILE [--source leetcode|neetcode] [--dry-run]
                                         mark problems already accepted, so they queue as verifies
  plan.py today [--date D] [--json]      what is due today (closes earlier open days first)
  plan.py start ID [--date D]            log start time for a problem
  plan.py hint ID LEVEL                  log a hint (1..3, or 'solution')
  plan.py record ID --type new|verify|resolve --result clean|sloppy|wrong|solution
            [--minutes M] [--explain clean|sloppy|wrong] [--errors a,b] [--note TEXT] [--date D]
  plan.py close [--date D] [--summary TEXT]   close the day, append log, regenerate schedule
  plan.py schedule [--date D]            projection -> plan/schedule.md, prints finish date
  plan.py set-date YYYY-MM-DD|none       set interview date (drives compression)
  plan.py meta KEY VALUE                 set a meta field (insight, complexity... use 'note')
  plan.py note ID FIELD TEXT             set insight|complexity|alternatives|explanation on a problem
  plan.py mock --format oa|phone|onsite|design --problems a,b --score N --notes TEXT
  plan.py drill --type recognition|template --score N --total N
  plan.py stats [--json]                 weekly signals
  plan.py status                         counts
  plan.py validate                       schema checks
  plan.py show ID                        one problem
  plan.py flag ID add|remove FLAG        add/remove a flag (e.g. other-lang, no-lc-accept)
"""
import argparse, json, os, sys, statistics
from datetime import date, datetime, timedelta
from copy import deepcopy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "plan", "problems.json")
SCHEDULE_MD = os.path.join(ROOT, "plan", "schedule.md")
LOG_MD = os.path.join(ROOT, "plan", "log.md")

COST_VERIFY = 15
COST_NEW = {"Easy": 30, "Medium": 50, "Hard": 80}
DRILL_MIN = 10
RESOLVE_BUDGET_MIN = 45       # minutes per day reserved for re-solves
RESOLVE_COST = {"code": 12, "explain": 5}
VERIFY_CAP = 10
# re-solve tiers: interval days per stage, and whether each stage is a full re-code or an explain-only recall
TIERS = {
    "A": {"intervals": [3, 7, 21], "kinds": ["code", "code", "explain"]},   # amazon >= 50, or flagged weak
    "B": {"intervals": [3, 10],    "kinds": ["code", "explain"]},           # amazon 30..50
    "C": {"intervals": [4],        "kinds": ["code"]},                      # amazon < 30 or unknown
}
INTERLEAVE_START_DAY = 8      # day index (1-based) from which interleave items may appear
INTERLEAVE_GAP_DAYS = 5       # days after a section finishes before its held-back item is released
PREP_DAYS = 3                 # days before an interview reserved for prep
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---------- io ----------
def load():
    with open(DATA) as f:
        return json.load(f)


def save(d):
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, DATA)


def D(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def S(d):
    return d.strftime("%Y-%m-%d")


def today_arg(args):
    return D(args.date) if getattr(args, "date", None) else date.today()


# ---------- helpers ----------
def by_id(d):
    return {p["id"]: p for p in d["problems"]}


def sec_order(d):
    return {s["id"]: s["order"] for s in d["sections"]}


def sec_name(d):
    return {s["id"]: s["name"] for s in d["sections"]}


def freq(p):
    return p.get("amazon_freq") or 0.0


def tier(p):
    if any(f in p["flags"] for f in ("weak", "solution-needed", "explain-failed", "failed-verify")):
        return "A"
    f = freq(p)
    return "A" if f >= 50 else ("B" if f >= 30 else "C")


def resolve_kind(p):
    t = TIERS[tier(p)]
    st = min(p.get("resolve_stage", 0), len(t["kinds"]) - 1)
    return t["kinds"][st]


def resolve_intervals(p):
    return TIERS[tier(p)]["intervals"]


def is_light(d, day):
    return WEEKDAYS[day.weekday()] == d["meta"]["light_day"]


def day_index(d, day):
    return (day - D(d["meta"]["start_date"])).days + 1


def prereq_bases(problems):
    """titles that are a prefix of another title in the same section (X vs X II)."""
    bases = set()
    for a in problems:
        for b in problems:
            if a is b or a["section"] != b["section"]:
                continue
            ta, tb = a["title"].lower(), b["title"].lower()
            if tb.startswith(ta) and len(tb) > len(ta):
                bases.add(a["id"])
    return bases


def interleave_ids(d):
    """Held-back problem per section, persisted as the 'interleave' flag (see assign_interleave)."""
    return {p["section"]: p["id"] for p in d["problems"] if "interleave" in p["flags"]}


def assign_interleave(d):
    """One held-back problem per section from section 3 on: the non-prerequisite todo with lowest Amazon score.
    Runs once; existing flags are kept."""
    so = sec_order(d)
    bases = prereq_bases(d["problems"])
    have = interleave_ids(d)
    picked = []
    for s in d["sections"]:
        if so[s["id"]] < 3 or s["id"].startswith("99") or s["id"] in have:
            continue
        cands = [p for p in d["problems"] if p["section"] == s["id"] and p["id"] not in bases and p["status"] == "todo"]
        if len(cands) < 2:
            continue
        pick = min(cands, key=lambda p: (freq(p), -p["order"]))
        pick["flags"].append("interleave"); picked.append(pick["id"])
    return picked


def section_finished_on(d, sec, exclude=()):
    """date the section's last non-excluded item was done, or None."""
    items = [p for p in d["problems"] if p["section"] == sec and p["id"] not in exclude and "deferred" not in p["flags"]]
    if any(p["status"] in ("todo", "solved_unverified") for p in items):
        return None
    dates = []
    for p in items:
        for a in p["attempts"]:
            if a["type"] in ("new", "verify"):
                dates.append(D(a["date"]))
    # nothing left in the section (all deferred, or none had attempts): treat as finished long ago
    return max(dates) if dates else date(2000, 1, 1)


def work_queue(d):
    """Ordered list of (problem, kind) still to do: verify then new, per section, NeetCode order.
    Interleave items are returned separately."""
    so = sec_order(d)
    inter = interleave_ids(d)
    inter_set = set(inter.values())
    main, held = [], []
    for s in sorted(d["sections"], key=lambda s: s["order"]):
        ps = sorted([p for p in d["problems"] if p["section"] == s["id"] and "deferred" not in p["flags"]],
                    key=lambda p: p["order"])
        for p in ps:
            if p["status"] == "solved_unverified":
                main.append((p, "verify"))
        for p in ps:
            if p["status"] == "todo":
                (held if p["id"] in inter_set else main).append((p, "new"))
    return main, held


def due_resolves(d, day):
    out = [p for p in d["problems"] if p.get("next_resolve") and D(p["next_resolve"]) <= day
           and p["status"] in ("solved", "verified")]
    out.sort(key=lambda p: (0 if tier(p) == "A" and "weak" in p["flags"] else 1, -freq(p), D(p["next_resolve"])))
    return out


def eligible_interleave(d, day, held):
    if day_index(d, day) < INTERLEAVE_START_DAY:
        return []
    out = []
    for p, kind in held:
        fin = section_finished_on(d, p["section"], exclude=(p["id"],))
        if fin and (day - fin).days >= INTERLEAVE_GAP_DAYS:
            out.append((p, kind))
    return out


def plan_day(d, day, done_ids=()):
    """Compute the day's plan from current state. Pure function of state."""
    m = d["meta"]
    light = is_light(d, day)
    resolves, rmin = [], 0
    rbudget = RESOLVE_BUDGET_MIN * (2 if light else 1)
    for p in due_resolves(d, day):
        if p["id"] in done_ids:
            continue
        c = RESOLVE_COST[resolve_kind(p)]
        if rmin + c > rbudget:
            continue
        resolves.append(p); rmin += c
    plan = {"date": S(day), "weekday": WEEKDAYS[day.weekday()], "light": light,
            "resolve": [p["id"] for p in resolves], "resolve_kinds": {p["id"]: resolve_kind(p) for p in resolves},
            "verify": [], "new": [], "interleave": []}
    if light or m.get("mode") == "maintenance":
        return plan
    budget = m["daily_minutes"] - DRILL_MIN - rmin
    main, held = work_queue(d)
    main = [(p, k) for p, k in main if p["id"] not in done_ids]
    new_left = m["new_per_day"]
    # interleave slot first
    for p, k in eligible_interleave(d, day, [(p, k) for p, k in held if p["id"] not in done_ids]):
        cost = COST_NEW[p["difficulty"]]
        if new_left and cost <= budget:
            plan["interleave"].append(p["id"]); budget -= cost; new_left -= 1
            break
    verify_left = VERIFY_CAP
    for p, k in main:
        if k == "verify":
            if verify_left and COST_VERIFY <= budget:
                plan["verify"].append(p["id"]); budget -= COST_VERIFY; verify_left -= 1
            else:
                break
        else:
            cost = COST_NEW[p["difficulty"]]
            if new_left and cost <= budget:
                plan["new"].append(p["id"]); budget -= cost; new_left -= 1
            elif new_left and not plan["new"] and not plan["verify"] and not plan["interleave"]:
                plan["new"].append(p["id"]); budget -= cost; new_left -= 1   # never an empty day
            else:
                break
    return plan


# ---------- projection ----------
def simulate(d, start, max_days=200):
    """Assume everything planned gets done cleanly. Returns (days list, finish_date or None)."""
    sim = deepcopy(d)
    ids = by_id(sim)
    day = start
    days = []
    finish = None
    for _ in range(max_days):
        plan = plan_day(sim, day)
        days.append(plan)
        for pid in plan["resolve"]:
            p = ids[pid]
            p["resolve_stage"] += 1
            iv = resolve_intervals(p)
            p["next_resolve"] = S(day + timedelta(days=iv[p["resolve_stage"]])) if p["resolve_stage"] < len(iv) else None
        for pid in plan["verify"]:
            p = ids[pid]; p["status"] = "verified"; p["resolve_stage"] = 0
            p["next_resolve"] = S(day + timedelta(days=resolve_intervals(p)[0]))
            p["attempts"].append({"date": S(day), "type": "verify", "result": "clean"})
        for pid in plan["new"] + plan["interleave"]:
            p = ids[pid]; p["status"] = "solved"; p["resolve_stage"] = 0
            p["next_resolve"] = S(day + timedelta(days=resolve_intervals(p)[0]))
            p["attempts"].append({"date": S(day), "type": "new", "result": "clean"})
        main, held = work_queue(sim)
        if not main and not held and finish is None:
            finish = day
        if finish and not plan["resolve"] and not due_resolves(sim, day + timedelta(days=1)):
            # stop once nothing is pending
            if all(p.get("next_resolve") is None for p in sim["problems"]):
                break
        if finish and (day - finish).days > 30:
            break
        day += timedelta(days=1)
    return days, finish


def compress_for_deadline(d, start):
    """If an interview date is set and the projection overruns, defer lowest-value tail items."""
    m = d["meta"]
    if not m.get("interview_date"):
        return []
    deadline = D(m["interview_date"]) - timedelta(days=PREP_DAYS)
    dropped = []
    bases = prereq_bases(d["problems"])
    for _ in range(200):
        _, finish = simulate(d, start)
        if finish is None or finish <= deadline:
            break
        # candidates: last remaining todo (by order) in each section, not a prereq base
        cands = []
        for s in d["sections"]:
            todos = [p for p in d["problems"] if p["section"] == s["id"] and p["status"] == "todo" and "deferred" not in p["flags"]]
            if not todos:
                continue
            tail = max(todos, key=lambda p: p["order"])
            if tail["id"] in bases:
                continue
            cands.append(tail)
        if not cands:
            break
        pick = min(cands, key=lambda p: (freq(p), -sec_order(d)[p["section"]]))
        pick["flags"].append("deferred"); dropped.append(pick["id"])
    return dropped


def write_schedule(d, start):
    sn = sec_name(d); ids = by_id(d)
    days, finish = simulate(d, start)
    lines = ["# Schedule", "", f"Generated {S(start)}. Projection assumes every planned item gets done cleanly.",
             f"Start date {d['meta']['start_date']}. Light day {d['meta']['light_day']}. "
             f"Interview date {d['meta'].get('interview_date') or 'not set'}.", ""]
    if finish:
        lines.append(f"**Projected finish of new problems: {S(finish)} ({WEEKDAYS[finish.weekday()]}, day {day_index(d, finish)}).**")
    deferred = [p for p in d["problems"] if "deferred" in p["flags"]]
    if deferred:
        lines.append(f"Deferred to after the interview ({len(deferred)}): " + ", ".join(p["title"] for p in deferred))
    lines.append("")
    cur_week = None
    for pl in days:
        day = D(pl["date"])
        wk = (day_index(d, day) - 1) // 7 + 1
        if wk != cur_week:
            cur_week = wk; lines.append(f"## Week {wk}"); lines.append("")
        tag = " (light day)" if pl["light"] else ""
        lines.append(f"### Day {day_index(d, day)} · {pl['weekday']} {pl['date']}{tag}")
        def fmt(pid):
            p = ids[pid]; a = f" · amz {p['amazon_freq']:.0f}" if p.get("amazon_freq") else ""
            return f"- [ ] {p['title']} ({p['difficulty']}, {sn[p['section']]}{a})"
        if pl["verify"]:
            lines.append("Verify from memory:"); lines += [fmt(x) for x in pl["verify"]]
        if pl["new"] or pl["interleave"]:
            lines.append("New:"); lines += [fmt(x) for x in pl["new"]]
            lines += [f"- [ ] (mixed) {ids[x]['title']} ({ids[x]['difficulty']})" for x in pl["interleave"]]
        if pl["resolve"]:
            rk = pl.get("resolve_kinds", {})
            lines.append(f"Re-solves ({len(pl['resolve'])}): " + ", ".join(ids[x]["title"] + (" (explain)" if rk.get(x) == "explain" else "") for x in pl["resolve"]))
        if not (pl["verify"] or pl["new"] or pl["interleave"] or pl["resolve"]):
            lines.append("Nothing due. Drill only.")
        lines.append("")
        if finish and day > finish + timedelta(days=7):
            lines.append("_Re-solves continue on their own schedule after this point (maintenance mode)._")
            break
    with open(SCHEDULE_MD, "w") as f:
        f.write("\n".join(lines) + "\n")
    return finish


# ---------- mutations ----------
def ensure_day(d, day):
    key = S(day)
    if key not in d["days"]:
        d["days"][key] = {"planned": None, "done": [], "closed": False, "light": is_light(d, day), "summary": "",
                          "drill": None}
    return d["days"][key]


def close_day(d, day, summary=""):
    rec = ensure_day(d, day)
    if rec["closed"]:
        return rec
    planned = rec["planned"] or plan_day(d, day)
    done_ids = {x["id"] for x in rec["done"]}
    left = [x for x in planned["verify"] + planned["new"] + planned["interleave"] + planned["resolve"] if x not in done_ids]
    rec["closed"] = True
    rec["leftover"] = left
    rec["summary"] = summary
    ids = by_id(d)
    n_new = sum(1 for x in rec["done"] if x["type"] in ("new",))
    n_ver = sum(1 for x in rec["done"] if x["type"] == "verify")
    n_res = sum(1 for x in rec["done"] if x["type"] == "resolve")
    with open(LOG_MD, "a") as f:
        f.write(f"## Day {day_index(d, day)} · {WEEKDAYS[day.weekday()]} {S(day)}\n")
        f.write(f"New {n_new}, verify {n_ver}, re-solve {n_res}. Leftover {len(left)}.\n")
        for x in rec["done"]:
            p = ids[x["id"]]
            extra = []
            if x.get("minutes"): extra.append(f"{x['minutes']} min")
            if x.get("hints"): extra.append(f"hints {x['hints']}")
            if x.get("explain"): extra.append(f"explain {x['explain']}")
            if x.get("errors"): extra.append("errors " + ",".join(x["errors"]))
            f.write(f"- {x['type']}: {p['title']} → {x['result']}" + (f" ({', '.join(extra)})" if extra else "") + "\n")
        if summary:
            f.write(f"\n{summary}\n")
        f.write("\n")
    return rec


def close_open_days_before(d, day):
    closed = []
    for key in sorted(d["days"]):
        if D(key) < day and not d["days"][key]["closed"]:
            close_day(d, D(key), summary="(auto-closed)")
            closed.append(key)
    return closed


def record_attempt(d, pid, typ, result, day, minutes=None, hints=None, explain=None, errors=None, note=""):
    ids = by_id(d)
    p = ids[pid]
    ip = d.get("inprogress", {}).pop(pid, None)
    if minutes is None and ip and ip.get("start"):
        try:
            minutes = int((datetime.now() - datetime.fromisoformat(ip["start"])).total_seconds() // 60)
        except Exception:
            minutes = None
    if hints is None and ip:
        hints = ip.get("hints", 0)
    if hints is None:
        hints = 0
    att = {"date": S(day), "type": typ, "result": result, "minutes": minutes, "hints": hints,
           "explain": explain, "errors": errors or [], "note": note}
    p["attempts"].append(att)
    if typ in ("new", "verify"):
        if typ == "verify" and result == "wrong":
            p["status"] = "todo"; p["flags"].append("failed-verify"); p["next_resolve"] = None
        else:
            p["status"] = "verified" if typ == "verify" else "solved"
            p["resolve_stage"] = 0
            if result == "solution" or hints == "solution" or (isinstance(hints, int) and hints >= 3):
                if "solution-needed" not in p["flags"]: p["flags"].append("solution-needed")
            p["next_resolve"] = S(day + timedelta(days=resolve_intervals(p)[0]))
    elif typ == "resolve":
        if result == "clean":
            p["resolve_stage"] += 1
            iv = resolve_intervals(p)
            p["next_resolve"] = S(day + timedelta(days=iv[p["resolve_stage"]])) if p["resolve_stage"] < len(iv) else None
            if p["next_resolve"] is None and "mastered" not in p["flags"]: p["flags"].append("mastered")
        else:
            p["resolve_stage"] = 0
            if "weak" not in p["flags"]: p["flags"].append("weak")
            p["next_resolve"] = S(day + timedelta(days=resolve_intervals(p)[0]))
    if explain == "wrong" and "explain-failed" not in p["flags"]:
        p["flags"].append("explain-failed")
    rec = ensure_day(d, day)
    if rec["planned"] is None:
        rec["planned"] = plan_day(d, day)
    rec["done"].append({"id": pid, "type": typ, "result": result, "minutes": minutes, "hints": hints,
                        "explain": explain, "errors": errors or []})
    return att


# ---------- stats ----------
def stats(d, upto=None):
    upto = upto or date.today()
    week_start = upto - timedelta(days=6)
    atts = []
    for p in d["problems"]:
        for a in p["attempts"]:
            atts.append((p, a))
    def wk(a): return week_start <= D(a["date"]) <= upto
    res = [a for p, a in atts if a["type"] == "resolve"]
    res_wk = [a for a in res if wk(a)]
    new = [a for p, a in atts if a["type"] in ("new", "verify")]
    new_wk = [a for a in new if wk(a)]
    med = [a["minutes"] for p, a in atts if a["type"] == "new" and p["difficulty"] == "Medium" and a.get("minutes") and wk(a)]
    errs = {}
    for p, a in atts:
        if wk(a):
            for e in a.get("errors") or []:
                errs[e] = errs.get(e, 0) + 1
    planned = done = 0
    for key, rec in d["days"].items():
        if week_start <= D(key) <= upto and rec.get("planned"):
            pl = rec["planned"]
            planned += len(pl["verify"]) + len(pl["new"]) + len(pl["interleave"]) + len(pl["resolve"])
            done += len(rec["done"])
    def rate(xs, ok=("clean",)):
        return round(100 * sum(1 for a in xs if a["result"] in ok) / len(xs)) if xs else None
    explain = [a["explain"] for p, a in atts if a.get("explain") and wk(a)]
    hints = [a["hints"] for a in new_wk if isinstance(a.get("hints"), int)]
    total = len([p for p in d["problems"] if not p["gap"]])
    done_ids = [p for p in d["problems"] if p["status"] in ("solved", "verified")]
    unver = [p for p in d["problems"] if p["status"] == "solved_unverified"]
    streak = 0
    day = upto
    while S(day) in d["days"] and d["days"][S(day)]["done"]:
        streak += 1; day -= timedelta(days=1)
    return {
        "as_of": S(upto),
        "resolve_clean_rate_week": rate(res_wk), "resolve_clean_rate_all": rate(res),
        "resolves_week": len(res_wk),
        "explain_clean_rate_week": round(100 * explain.count("clean") / len(explain)) if explain else None,
        "hints_per_new_week": round(sum(hints) / len(hints), 2) if hints else None,
        "median_medium_minutes_week": statistics.median(med) if med else None,
        "error_categories_week": dict(sorted(errs.items(), key=lambda kv: -kv[1])),
        "planned_week": planned, "done_week": done,
        "adherence_week": round(100 * done / planned) if planned else None,
        "solved_or_verified": len(done_ids), "unverified": len(unver), "total_core": total,
        "weak": [p["title"] for p in d["problems"] if "weak" in p["flags"] or "solution-needed" in p["flags"] or "explain-failed" in p["flags"] or "failed-verify" in p["flags"]],
        "streak": streak,
    }


# ---------- commands ----------
def cmd_today(args):
    d = load(); day = today_arg(args)
    closed = close_open_days_before(d, day)
    rec = ensure_day(d, day)
    done_ids = {x["id"] for x in rec["done"]}
    plan = plan_day(d, day, done_ids)
    rec["planned"] = plan if rec["planned"] is None else _merge_plan(rec["planned"], plan, done_ids)
    save(d)
    ids = by_id(d); sn = sec_name(d)
    out = {"day": day_index(d, day), "date": S(day), "weekday": plan["weekday"], "light": plan["light"],
           "auto_closed": closed, "done_today": rec["done"],
           "first_of_section": None, "items": []}
    def item(pid, kind):
        p = ids[pid]
        return {"id": pid, "kind": kind, "title": p["title"], "difficulty": p["difficulty"], "section": sn[p["section"]],
                "section_id": p["section"], "lc_url": p["lc_url"], "nc_url": p["nc_url"], "amazon_freq": p["amazon_freq"],
                "premium": p["premium"], "resolve_stage": p["resolve_stage"], "flags": p["flags"],
                "resolve_kind": resolve_kind(p) if kind == "resolve" else None, "tier": tier(p)}
    for pid in rec["planned"]["interleave"]:
        if pid not in done_ids: out["items"].append(item(pid, "mixed"))
    for pid in rec["planned"]["verify"]:
        if pid not in done_ids: out["items"].append(item(pid, "verify"))
    for pid in rec["planned"]["new"]:
        if pid not in done_ids: out["items"].append(item(pid, "new"))
    for pid in rec["planned"]["resolve"]:
        if pid not in done_ids: out["items"].append(item(pid, "resolve"))
    # first problem of a section?
    for it in out["items"]:
        if it["kind"] in ("verify", "new"):
            sec = it["section_id"]
            started = any(p["section"] == sec and p["attempts"] for p in d["problems"])
            if not started:
                out["first_of_section"] = {"id": sec, "name": it["section"], "primer": f"primers/{sec}.md"}
            break
    out["stats"] = stats(d, day)
    _, finish = simulate(d, day)
    out["projected_finish"] = S(finish) if finish else None
    if args.json:
        print(json.dumps(out, indent=1)); return
    print(f"Day {out['day']} · {plan['weekday']} {S(day)}" + (" · LIGHT DAY (re-solves and drill only)" if plan["light"] else ""))
    if closed: print(f"Auto-closed earlier open day(s): {', '.join(closed)}")
    if out["first_of_section"]:
        print(f"First problem of {out['first_of_section']['name']} today → read {out['first_of_section']['primer']} and do its warm-ups first.")
    for it in out["items"]:
        tag = {"verify": "VERIFY", "new": "NEW", "mixed": "NEW (mixed, section hidden)",
               "resolve": f"RE-SOLVE {it['resolve_kind']} s{it['resolve_stage']}"}[it["kind"]]
        sec = "" if it["kind"] == "mixed" else f" · {it['section']}"
        amz = f" · amz {it['amazon_freq']:.0f}" if it["amazon_freq"] else ""
        print(f"  [{tag}] {it['title']} ({it['difficulty']}{sec}{amz})\n      {it['lc_url']}")
    if rec["done"]:
        print(f"Done today: " + ", ".join(f"{ids[x['id']]['title']} ({x['type']}:{x['result']})" for x in rec["done"]))
    st = out["stats"]
    print(f"Progress {st['solved_or_verified']}/{st['total_core']} verified-or-solved, {st['unverified']} unverified · streak {st['streak']} · projected finish {out['projected_finish']}")


def _merge_plan(old, new, done_ids):
    """Keep already-planned items (minus done), add newly-due ones, never duplicate."""
    out = deepcopy(new)
    for k in ("verify", "new", "interleave", "resolve"):
        seen = set(out[k])
        for pid in old.get(k, []):
            if pid not in seen and pid not in done_ids:
                out[k].append(pid); seen.add(pid)
    return out


def cmd_start(args):
    d = load(); ids = by_id(d)
    if args.id not in ids: sys.exit(f"unknown id {args.id}")
    ip = d.setdefault("inprogress", {}).setdefault(args.id, {"start": None, "hints": 0})
    ip["start"] = datetime.now().isoformat(timespec="seconds")
    save(d)
    kept = f" · hints kept at {ip['hints']}" if ip.get("hints") else ""
    print(f"started {ids[args.id]['title']} at {ip['start']}{kept}")


def cmd_stop(args):
    d = load(); ids = by_id(d)
    if args.id not in ids: sys.exit(f"unknown id {args.id}")
    ip = d.get("inprogress", {}).get(args.id)
    if not ip:
        print(f"{ids[args.id]['title']} was not in progress"); return
    started = ip.get("start")
    elapsed = ""
    if started:
        mins = (datetime.now() - datetime.fromisoformat(started)).total_seconds() / 60
        elapsed = f" after {mins:.0f} min"
    ip["start"] = None
    save(d)
    hints = ip.get("hints", 0)
    print(f"stopped {ids[args.id]['title']}{elapsed} · clock cleared, hints kept at {hints}")


def cmd_hint(args):
    d = load(); ids = by_id(d)
    if args.id not in ids: sys.exit(f"unknown id {args.id}")
    ip = d.setdefault("inprogress", {}).setdefault(args.id, {"start": None, "hints": 0})
    lvl = args.level
    ip["hints"] = "solution" if lvl == "solution" else max(int(ip["hints"]) if isinstance(ip["hints"], int) else 3, int(lvl))
    save(d); print(f"hint level now {ip['hints']} for {ids[args.id]['title']}")


def cmd_record(args):
    d = load(); day = today_arg(args); ids = by_id(d)
    if args.id not in ids: sys.exit(f"unknown id {args.id}")
    errors = [e.strip() for e in args.errors.split(",")] if args.errors else []
    att = record_attempt(d, args.id, args.type, args.result, day, minutes=args.minutes, hints=args.hints,
                         explain=args.explain, errors=errors, note=args.note or "")
    save(d)
    p = ids[args.id]
    print(f"recorded {args.type}:{args.result} for {p['title']} · status {p['status']} · next re-solve {p['next_resolve']} · flags {p['flags']}")


def cmd_close(args):
    d = load(); day = today_arg(args)
    rec = close_day(d, day, args.summary or "")
    finish = write_schedule(d, day + timedelta(days=1))
    save(d)
    print(f"closed {S(day)} · done {len(rec['done'])} · leftover {len(rec.get('leftover', []))} · projected finish {S(finish) if finish else 'n/a'}")


def cmd_schedule(args):
    d = load(); day = today_arg(args)
    assign_interleave(d)
    dropped = compress_for_deadline(d, day)
    finish = write_schedule(d, day)
    save(d)
    print(f"schedule written · projected finish {S(finish) if finish else 'n/a'}" + (f" · deferred {len(dropped)}" if dropped else ""))


def cmd_set_date(args):
    d = load()
    d["meta"]["interview_date"] = None if args.date_value.lower() == "none" else S(D(args.date_value))
    if d["meta"]["interview_date"] is None:
        for p in d["problems"]:
            p["flags"] = [f for f in p["flags"] if f != "deferred"]
    save(d)
    day = date.today()
    dropped = compress_for_deadline(d, day)
    finish = write_schedule(d, day)
    save(d)
    print(f"interview date {d['meta']['interview_date']} · projected finish {S(finish) if finish else 'n/a'} · deferred {len(dropped)}")


def cmd_meta(args):
    d = load(); v = args.value
    if v.isdigit(): v = int(v)
    elif v.lower() in ("true", "false"): v = v.lower() == "true"
    elif v.lower() in ("none", "null"): v = None
    d["meta"][args.key] = v; save(d); print(f"meta.{args.key} = {v}")


def cmd_note(args):
    d = load(); ids = by_id(d)
    if args.id not in ids: sys.exit("unknown id")
    if args.field not in ("insight", "complexity", "alternatives", "explanation"): sys.exit("bad field")
    ids[args.id][args.field] = args.text; save(d); print("ok")


def cmd_mock(args):
    d = load()
    d["mocks"].append({"date": S(date.today()), "format": args.format, "problems": args.problems.split(",") if args.problems else [],
                       "score": args.score, "notes": args.notes or ""})
    save(d); print(f"mock recorded ({len(d['mocks'])} total)")


def cmd_drill(args):
    d = load()
    d["drills"].append({"date": S(date.today()), "type": args.type, "score": args.score, "total": args.total})
    save(d); print("drill recorded")


def cmd_stats(args):
    d = load(); st = stats(d, today_arg(args))
    if args.json: print(json.dumps(st, indent=1)); return
    for k, v in st.items(): print(f"{k}: {v}")


def cmd_status(args):
    d = load(); sn = sec_name(d)
    from collections import Counter
    c = Counter(p["status"] for p in d["problems"])
    print(dict(c))
    for s in sorted(d["sections"], key=lambda s: s["order"]):
        ps = [p for p in d["problems"] if p["section"] == s["id"]]
        done = sum(1 for p in ps if p["status"] in ("solved", "verified"))
        unv = sum(1 for p in ps if p["status"] == "solved_unverified")
        print(f"  {s['name']:28s} {done}/{len(ps)} done, {unv} unverified")


def cmd_validate(args):
    d = load(); errs = []
    ids = [p["id"] for p in d["problems"]]
    if len(ids) != len(set(ids)): errs.append("duplicate ids")
    core = [p for p in d["problems"] if not p["gap"]]
    if len(core) != 150: errs.append(f"core count {len(core)} != 150")
    secs = {s["id"] for s in d["sections"]}
    for p in d["problems"]:
        for k in ("id", "lc_id", "title", "section", "order", "difficulty", "lc_url", "status", "attempts", "flags"):
            if k not in p: errs.append(f"{p.get('id')}: missing {k}")
        if p["section"] not in secs: errs.append(f"{p['id']}: bad section")
        if p["difficulty"] not in COST_NEW: errs.append(f"{p['id']}: bad difficulty {p['difficulty']}")
        if p["status"] not in ("todo", "solved_unverified", "solved", "verified"): errs.append(f"{p['id']}: bad status")
        if not p["gap"] and not p.get("nc_url"): errs.append(f"{p['id']}: no nc_url")
    for s in secs:
        orders = sorted(p["order"] for p in d["problems"] if p["section"] == s)
        if orders != list(range(1, len(orders) + 1)): errs.append(f"{s}: order gaps")
    print("OK" if not errs else "\n".join(errs))
    sys.exit(1 if errs else 0)


def cmd_flag(args):
    d = load(); ids = by_id(d)
    if args.id not in ids: sys.exit("unknown id")
    p = ids[args.id]
    if args.op == "add" and args.flag not in p["flags"]: p["flags"].append(args.flag)
    if args.op == "remove": p["flags"] = [f for f in p["flags"] if f != args.flag]
    save(d); print(f"{p['title']} flags {p['flags']}")


def cmd_show(args):
    d = load(); ids = by_id(d)
    print(json.dumps(ids.get(args.id, {"error": "unknown id"}), indent=1))


# ---------- bootstrap ----------
CATALOGUE = os.path.join(ROOT, "data", "catalogue.json")

FRESH = {"status": "todo", "attempts": [], "resolve_stage": 0, "next_resolve": None,
         "insight": "", "complexity": "", "alternatives": "", "explanation": "", "flags": []}


def cmd_init(args):
    """Create plan/problems.json from data/catalogue.json. Run once, before day 1."""
    if os.path.exists(DATA) and not args.force:
        sys.exit(f"{DATA} already exists. Refusing to overwrite (use --force to start over).")
    if not os.path.exists(CATALOGUE):
        sys.exit(f"missing {CATALOGUE}")
    cat = json.load(open(CATALOGUE))
    start = D(args.start_date) if args.start_date else date.today()
    if args.light_day not in WEEKDAYS + ["none"]:
        sys.exit(f"--light-day must be one of {', '.join(WEEKDAYS)} or none")
    d = {
        "meta": {
            "start_date": start.isoformat(),
            "light_day": args.light_day,
            "daily_minutes": args.daily_minutes,
            "new_per_day": args.new_per_day,
            "resolve_per_day": args.resolve_per_day,
            "resolve_intervals": TIERS["A"]["intervals"],
            "target_company": "amazon",
            "level": args.level,
            "premium": bool(args.premium),
            "user_name": args.name or "",
            "interview_date": None,
            "mode": "active",
            "created": date.today().isoformat(),
            "notes": cat.get("source", ""),
        },
        "sections": [dict(s) for s in cat["sections"]],
        "problems": [dict(pr, **deepcopy(FRESH),
                          solved_on={"neetcode": False, "leetcode": False}) for pr in cat["problems"]],
        "days": {}, "mocks": [], "start_times": {}, "drills": [], "inprogress": {},
    }
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    save(d)
    os.makedirs(os.path.dirname(LOG_MD), exist_ok=True)
    if not os.path.exists(LOG_MD):
        with open(LOG_MD, "w") as f:
            f.write("# Daily log\n\nAppended by `plan.py close`. One entry per day.\n")
    print(f"{DATA}: {len(d['problems'])} problems, {len(d['sections'])} sections")
    print(f"start {start.isoformat()} ({WEEKDAYS[start.weekday()]}), light day {args.light_day}, "
          f"{args.daily_minutes} min/day, {args.new_per_day} new/day, "
          f"Premium {'yes' if args.premium else 'no'}")
    print("Next: `plan.py import-solved FILE` if you have LeetCode history, then `plan.py schedule`.")


LANG_PY = {"python", "python3", "py"}


def parse_solved(path):
    """Accept any of: a JSON map {slug: {lang,...}} (leetcode.js codesFor), a JSON list of slugs,
    or a text file with one slug, 'id|title' line, or problem URL per line."""
    raw = open(path).read().strip()
    if not raw:
        return {}
    if raw[0] in "[{":
        obj = json.loads(raw)
        if isinstance(obj, str):
            obj = json.loads(obj)
        if isinstance(obj, dict):
            return {k: (v.get("lang") if isinstance(v, dict) else None) for k, v in obj.items()}
        return {s: None for s in obj}
    out = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:                      # "1|Two Sum" from acceptedList()
            line = line.split("|", 1)[1].strip().lower().replace(" ", "-")
        if "/problems/" in line:             # a pasted URL
            line = line.split("/problems/")[1].strip("/").split("/")[0]
        out[line] = None
    return out


def cmd_import_solved(args):
    """Mark problems already accepted elsewhere, so they enter the verify queue instead of the new queue."""
    d = load(); ids = by_id(d)
    found = parse_solved(args.file)
    hit, miss, skip = [], [], []
    for slug, lang in found.items():
        p = ids.get(slug)
        if not p:
            miss.append(slug); continue
        if p["status"] in ("solved", "verified"):
            skip.append(slug); continue
        p["solved_on"][args.source] = True
        p["status"] = "solved_unverified"
        if args.source == "leetcode" and lang and lang.lower() not in LANG_PY:
            if "other-lang" not in p["flags"]:
                p["flags"].append("other-lang")
        if args.source == "neetcode" and not p["solved_on"]["leetcode"]:
            if "no-lc-accept" not in p["flags"]:
                p["flags"].append("no-lc-accept")
        hit.append(slug)
    if args.dry_run:
        print(f"dry run: would mark {len(hit)} solved_unverified via {args.source}")
    else:
        save(d)
        print(f"marked {len(hit)} as solved_unverified via {args.source}")
    other = [s for s in hit if "other-lang" in ids[s]["flags"]]
    if other:
        print(f"  {len(other)} accepted in another language - verify in Python: {', '.join(other[:8])}"
              + (" ..." if len(other) > 8 else ""))
    if skip:
        print(f"  {len(skip)} already solved/verified here, left alone")
    if miss:
        print(f"  {len(miss)} not in the catalogue (outside the 150), ignored: {', '.join(sorted(miss)[:8])}"
              + (" ..." if len(miss) > 8 else ""))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init"); s.add_argument("--start-date"); s.add_argument("--light-day", default="Sunday")
    s.add_argument("--daily-minutes", type=int, default=240); s.add_argument("--new-per-day", type=int, default=3)
    s.add_argument("--resolve-per-day", type=int, default=4); s.add_argument("--level", default="SDE2")
    s.add_argument("--premium", action="store_true", help="LeetCode Premium: unlocks the Premium-only problems")
    s.add_argument("--name"); s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_init)
    s = sub.add_parser("import-solved"); s.add_argument("file")
    s.add_argument("--source", default="leetcode", choices=["leetcode", "neetcode"])
    s.add_argument("--dry-run", action="store_true"); s.set_defaults(fn=cmd_import_solved)
    s = sub.add_parser("today"); s.add_argument("--date"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_today)
    s = sub.add_parser("start"); s.add_argument("id"); s.add_argument("--date"); s.set_defaults(fn=cmd_start)
    s = sub.add_parser("stop"); s.add_argument("id"); s.set_defaults(fn=cmd_stop)
    s = sub.add_parser("hint"); s.add_argument("id"); s.add_argument("level"); s.set_defaults(fn=cmd_hint)
    s = sub.add_parser("record"); s.add_argument("id"); s.add_argument("--type", required=True, choices=["new", "verify", "resolve"])
    s.add_argument("--result", required=True, choices=["clean", "sloppy", "wrong", "solution"]); s.add_argument("--minutes", type=int)
    s.add_argument("--hints", type=int); s.add_argument("--explain", choices=["clean", "sloppy", "wrong"]); s.add_argument("--errors")
    s.add_argument("--note"); s.add_argument("--date"); s.set_defaults(fn=cmd_record)
    s = sub.add_parser("close"); s.add_argument("--date"); s.add_argument("--summary"); s.set_defaults(fn=cmd_close)
    s = sub.add_parser("schedule"); s.add_argument("--date"); s.set_defaults(fn=cmd_schedule)
    s = sub.add_parser("set-date"); s.add_argument("date_value"); s.set_defaults(fn=cmd_set_date)
    s = sub.add_parser("meta"); s.add_argument("key"); s.add_argument("value"); s.set_defaults(fn=cmd_meta)
    s = sub.add_parser("note"); s.add_argument("id"); s.add_argument("field"); s.add_argument("text"); s.set_defaults(fn=cmd_note)
    s = sub.add_parser("mock"); s.add_argument("--format", required=True); s.add_argument("--problems"); s.add_argument("--score", type=int); s.add_argument("--notes"); s.set_defaults(fn=cmd_mock)
    s = sub.add_parser("drill"); s.add_argument("--type", required=True); s.add_argument("--score", type=int); s.add_argument("--total", type=int); s.set_defaults(fn=cmd_drill)
    s = sub.add_parser("stats"); s.add_argument("--date"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_stats)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("validate"); s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("flag"); s.add_argument("id"); s.add_argument("op", choices=["add", "remove"]); s.add_argument("flag"); s.set_defaults(fn=cmd_flag)
    args = ap.parse_args(); args.fn(args)


if __name__ == "__main__":
    main()
