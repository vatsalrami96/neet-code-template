#!/usr/bin/env python3
"""Render dashboard/index.html from plan/problems.json.   python3 dashboard/build.py [--date YYYY-MM-DD]"""
import json, os, sys, html, statistics
from datetime import date, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import plan as P

OUT = os.path.join(ROOT, "dashboard", "index.html")
today = P.D(sys.argv[sys.argv.index("--date") + 1]) if "--date" in sys.argv else date.today()
d = P.load()
ids = P.by_id(d); sn = P.sec_name(d)
st = P.stats(d, today)
rec = d["days"].get(P.S(today))
done_ids = {x["id"] for x in rec["done"]} if rec else set()
plan = P.plan_day(d, today, done_ids)
days, finish = P.simulate(d, today)
E = html.escape

# ---------- pieces ----------
def chip(kind, extra=""):
    label = {"verify": "Verify", "new": "New", "mixed": "New · mixed", "resolve": "Re-solve"}[kind]
    return f'<span class="chip chip-{kind}">{label}{extra}</span>'

def row(pid, kind):
    p = ids[pid]
    extra = ""
    if kind == "resolve":
        extra = f" · {P.resolve_kind(p)} s{p['resolve_stage']}"
    sec = "" if kind == "mixed" else f'<span class="sec">{E(sn[p["section"]])}</span>'
    amz = f'<span class="amz" title="Amazon frequency">amz {p["amazon_freq"]:.0f}</span>' if p.get("amazon_freq") else '<span class="amz dim">amz –</span>'
    done = ' class="done"' if pid in done_ids else ""
    return (f'<li{done}>{chip(kind, extra)}<a href="{E(p["lc_url"])}" target="_blank" rel="noopener">{E(p["title"])}</a>'
            f'<span class="diff diff-{p["difficulty"].lower()}">{p["difficulty"]}</span>{sec}{amz}</li>')

today_items = [row(x, "mixed") for x in plan["interleave"]] + [row(x, "verify") for x in plan["verify"]] + \
              [row(x, "new") for x in plan["new"]] + [row(x, "resolve") for x in plan["resolve"]]
done_rows = ""
if rec and rec["done"]:
    done_rows = "".join(f'<li class="done">{chip(x["type"] if x["type"] != "new" else "new")}<span>{E(ids[x["id"]]["title"])}</span>'
                        f'<span class="result r-{x["result"]}">{x["result"]}</span></li>' for x in rec["done"])
light_note = '<p class="note">Light day. Re-solves and drill only.</p>' if plan["light"] else ""
if not today_items and not done_rows:
    today_items = ['<li class="empty">Nothing due. Drill, or say "start" to pull the next problems.</li>']

# progress per section
prog = []
for s in sorted(d["sections"], key=lambda s: s["order"]):
    ps = [p for p in d["problems"] if p["section"] == s["id"]]
    n = len(ps)
    ver = sum(1 for p in ps if p["status"] == "verified")
    sol = sum(1 for p in ps if p["status"] == "solved")
    unv = sum(1 for p in ps if p["status"] == "solved_unverified")
    todo = n - ver - sol - unv
    hi = sum(1 for p in ps if p["status"] in ("todo", "solved_unverified") and (p.get("amazon_freq") or 0) >= 50)
    def seg(k, cls): return f'<i class="{cls}" style="flex:{k}"></i>' if k else ""
    prog.append(f'<div class="prow"><span class="pname">{E(s["name"])}</span>'
                f'<span class="pbar">{seg(ver, "s-ver")}{seg(sol, "s-sol")}{seg(unv, "s-unv")}{seg(todo, "s-todo")}</span>'
                f'<span class="pnum">{ver + sol}<span class="dim">/{n}</span></span>'
                f'<span class="phi">{("★ " + str(hi)) if hi else ""}</span></div>')

# re-solve queue, next 7 days from projection
queue = []
for pl in days[:7]:
    day = P.D(pl["date"])
    items = pl["resolve"]
    rk = pl.get("resolve_kinds", {})
    lis = "".join(f'<li><span>{E(ids[x]["title"])}</span><em>{rk.get(x, "code")}</em></li>' for x in items) or '<li class="empty">–</li>'
    cls = " today" if day == today else (" light" if pl["light"] else "")
    queue.append(f'<div class="qday{cls}"><h4>{pl["weekday"][:3]} <span>{day.day}</span></h4><ul>{lis}</ul></div>')

# trends by week
def week_of(ds): return (P.D(ds) - P.D(d["meta"]["start_date"])).days // 7 + 1
weeks = {}
for p in d["problems"]:
    for a in p["attempts"]:
        w = weeks.setdefault(week_of(a["date"]), {"res": [], "hints": [], "med": [], "exp": [], "pf": []})
        if a["type"] == "resolve": w["res"].append(a["result"] == "clean")
        if a["type"] in ("new", "verify"):
            if isinstance(a.get("hints"), int): w["hints"].append(a["hints"])
            if a.get("explain"): w["exp"].append(a["explain"] == "clean")
            if a.get("preflight") and a["preflight"].get("score") is not None:
                w["pf"].append(a["preflight"]["score"])
        if a["type"] == "new" and p["difficulty"] == "Medium" and a.get("minutes"): w["med"].append(a["minutes"])
def series(key, fn):
    return [(wk, fn(v[key])) for wk, v in sorted(weeks.items()) if v[key]]
def pct(xs): return round(100 * sum(xs) / len(xs))
S_res = series("res", pct); S_exp = series("exp", pct)
S_h = series("hints", lambda xs: round(sum(xs) / len(xs), 2)); S_m = series("med", lambda xs: statistics.median(xs))
S_pf = series("pf", lambda xs: round(sum(xs) / len(xs), 1))

def bars(ser, unit, vmax=None, good_high=True):
    if not ser:
        return '<p class="empty">No data yet. Fills in from the first week.</p>'
    vmax = vmax or max(v for _, v in ser) or 1
    W, H, bw = 220, 64, 22
    parts = []
    for i, (wk, v) in enumerate(ser):
        h = max(2, round(v / vmax * (H - 18)))
        x = 8 + i * (bw + 8)
        parts.append(f'<rect x="{x}" y="{H - 14 - h}" width="{bw}" height="{h}" rx="2" class="bar"/>'
                     f'<text x="{x + bw / 2}" y="{H - 14 - h - 3}" class="val">{v}{unit}</text>'
                     f'<text x="{x + bw / 2}" y="{H - 2}" class="wk">w{wk}</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="spark" role="img" aria-label="weekly values">{"".join(parts)}</svg>'

trend_cards = [
    ("Re-solve clean rate", "target ≥ 80%", bars(S_res, "%", 100)),
    ("Explain-back clean rate", "target consistently clean", bars(S_exp, "%", 100)),
    ("Pre-flight score", "steps 1-5, out of 10, before the clock", bars(S_pf, "", 10)),
    ("Hints per new problem", "should trend down", bars(S_h, "", None)),
    ("Median Medium solve, minutes", "target ≈ 25 by week 4", bars(S_m, "m", None)),
]
trends = "".join(f'<div class="tcard"><h4>{t}<span>{s}</span></h4>{b}</div>' for t, s, b in trend_cards)

errs = st["error_categories_week"]
err_html = "".join(f'<li><span>{E(k)}</span><b>{v}</b></li>' for k, v in errs.items()) or '<li class="empty">No errors tagged this week.</li>'
weak = [p for p in d["problems"] if any(f in p["flags"] for f in ("weak", "solution-needed", "explain-failed", "failed-verify"))]
weak_html = "".join(f'<li><a href="{E(p["lc_url"])}" target="_blank" rel="noopener">{E(p["title"])}</a>'
                    f'<span class="flags">{" ".join(f"<i>{E(f)}</i>" for f in p["flags"] if f in ("weak","solution-needed","explain-failed","failed-verify"))}</span></li>'
                    for p in sorted(weak, key=lambda p: -(p.get("amazon_freq") or 0))) or '<li class="empty">None flagged yet. That changes.</li>'
mocks = d.get("mocks", [])
mock_html = "".join(f'<li><span>{m["date"]}</span><span>{E(m["format"])}</span><b>{m.get("score") if m.get("score") is not None else "–"}/14</b></li>' for m in mocks[-5:]) or '<li class="empty">No mocks yet. First one in week two.</li>'

day_n = P.day_index(d, today)
interview = d["meta"].get("interview_date")
sub = f'Day {day_n} · {today.strftime("%A %d %b %Y")} · Amazon SDE2 · Python'
finish_txt = f'{finish.strftime("%d %b")} (day {P.day_index(d, finish)})' if finish else "–"
deferred = sum(1 for p in d["problems"] if "deferred" in p["flags"])
rate = st["resolve_clean_rate_week"]
pf = st.get("preflight_score_week")
tr = st.get("traced_rate_week")
tiles = [
    ("Owned", f'{st["solved_or_verified"]}<small>/{st["total_core"]}</small>', "solved or verified, NeetCode 150"),
    ("Unverified", str(st["unverified"]), "solved before, not yet re-proven"),
    ("Streak", f'{st["streak"]}<small> d</small>', "days with any recorded work"),
    ("Re-solve clean", f'{rate if rate is not None else "–"}<small>{"%" if rate is not None else ""}</small>', "this week; the number that matters"),
    ("Pre-flight", f'{pf if pf is not None else "–"}<small>{"/10" if pf is not None else ""}</small>',
     f'steps 1-5 before coding; {tr}% traced before submit' if tr is not None else "steps 1-5, stated before coding"),
    ("Projected finish", finish_txt, f'{deferred} deferred' if deferred else ("interview " + interview if interview else "no interview date set")),
]
tiles_html = "".join(f'<div class="tile"><span class="tl">{t}</span><span class="tv">{v}</span><span class="td">{E(sd)}</span></div>' for t, v, sd in tiles)

CSS = r"""
:root{
  --bg:#F5F7F4; --surface:#FFFFFF; --ink:#1B2430; --ink-2:#4A5560; --muted:#7A8590; --line:#DDE3DD; --line-2:#EAEEE9;
  --accent:#0F6E56; --accent-ink:#0B5643; --accent-soft:#DDF0E8; --amber:#B8781A; --amber-soft:#F7ECD6;
  --crit:#B0413E; --crit-soft:#F6E0DF; --blue:#2F5F8F; --blue-soft:#E1EAF3;
  --todo:#E3E8E2; --unv:#E9D9B5; --ver:#0F6E56; --sol:#5FAE8F;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#12181D; --surface:#1A2229; --ink:#E7ECE6; --ink-2:#B9C2BB; --muted:#8A949C; --line:#2A353D; --line-2:#222C33;
  --accent:#3FB88F; --accent-ink:#7CD3B4; --accent-soft:#173A31; --amber:#E0A33B; --amber-soft:#3A2E17;
  --crit:#E06A66; --crit-soft:#3E2323; --blue:#7FA9D6; --blue-soft:#1E2E3E;
  --todo:#26313A; --unv:#5A4A28; --ver:#3FB88F; --sol:#2E7D62;
}}
:root[data-theme="dark"]{
  --bg:#12181D; --surface:#1A2229; --ink:#E7ECE6; --ink-2:#B9C2BB; --muted:#8A949C; --line:#2A353D; --line-2:#222C33;
  --accent:#3FB88F; --accent-ink:#7CD3B4; --accent-soft:#173A31; --amber:#E0A33B; --amber-soft:#3A2E17;
  --crit:#E06A66; --crit-soft:#3E2323; --blue:#7FA9D6; --blue-soft:#1E2E3E;
  --todo:#26313A; --unv:#5A4A28; --ver:#3FB88F; --sol:#2E7D62;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:15px;line-height:1.5;padding-inline:20px;padding-block:28px 48px}
a{color:inherit;text-decoration:none;border-bottom:1px solid var(--line)} a:hover{border-color:var(--accent);color:var(--accent-ink)}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1080px;margin:0 auto;display:grid;gap:36px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 24px;border-bottom:1px solid var(--line);padding-bottom:16px}
h1{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;font-weight:600;font-size:30px;letter-spacing:-.01em;margin:0;text-wrap:balance}
header p{margin:0;color:var(--ink-2);font-variant-numeric:tabular-nums}
h2{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;font-weight:600;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}
h4{margin:0 0 6px;font-size:14px;font-weight:600}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px;display:grid;gap:2px}
.tl{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.tv{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}
.tv small{font-size:14px;color:var(--muted)} .td{font-size:12px;color:var(--ink-2)}
ul{list-style:none;margin:0;padding:0}
.today li{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;padding:10px 0;border-bottom:1px solid var(--line-2)}
.today li a{font-weight:500} .today li.done{opacity:.55} .today li.done a{text-decoration:line-through}
.chip{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;letter-spacing:.04em;padding:2px 8px;border-radius:3px;background:var(--line-2);color:var(--ink-2);min-width:64px;text-align:center}
.chip-new{background:var(--accent-soft);color:var(--accent-ink)} .chip-mixed{background:var(--blue-soft);color:var(--blue)}
.chip-verify{background:var(--amber-soft);color:var(--amber)} .chip-resolve{background:var(--line-2);color:var(--ink-2)}
.diff{font-size:12px;color:var(--muted)} .diff-hard{color:var(--crit)} .diff-medium{color:var(--amber)} .diff-easy{color:var(--accent)}
.sec{font-size:12px;color:var(--muted)} .amz{margin-left:auto;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--ink-2);font-variant-numeric:tabular-nums} .dim{color:var(--muted)}
.result{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px} .r-clean{color:var(--accent)} .r-sloppy{color:var(--amber)} .r-wrong,.r-solution{color:var(--crit)}
.note,.empty{color:var(--muted);font-size:14px;margin:4px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:6px 32px}
.prow{display:grid;grid-template-columns:minmax(120px,160px) 1fr 52px 34px;align-items:center;gap:10px;padding:5px 0;font-size:13px}
.pname{white-space:nowrap;overflow:hidden;text-overflow:ellipsis} .pbar{display:flex;height:8px;border-radius:2px;overflow:hidden;background:var(--todo);gap:1px}
.pbar i{display:block} .s-ver{background:var(--ver)} .s-sol{background:var(--sol)} .s-unv{background:var(--unv)} .s-todo{background:transparent}
.pnum{font-family:"IBM Plex Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;text-align:right} .phi{color:var(--amber);font-size:12px;white-space:nowrap}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--muted);margin-top:8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.queue{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}
.qday{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:10px;min-height:96px}
.qday.today{border-color:var(--accent)} .qday.light{background:transparent;border-style:dashed}
.qday h4{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em} .qday h4 span{color:var(--ink)}
.qday li{display:flex;justify-content:space-between;gap:6px;font-size:12px;padding:3px 0;border-bottom:1px solid var(--line-2)} .qday li em{font-style:normal;color:var(--muted);font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px}
.trends{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.tcard{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px} .tcard h4 span{display:block;font-weight:400;font-size:12px;color:var(--muted)}
.spark{width:100%;height:auto;display:block} .spark .bar{fill:var(--accent)} .spark text{fill:var(--ink-2);font-size:9px;text-anchor:middle;font-family:"IBM Plex Mono",ui-monospace,monospace} .spark .wk{fill:var(--muted)}
.three{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:24px}
.three li{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--line-2);font-size:14px}
.flags i{font-style:normal;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;color:var(--crit);margin-left:6px}
footer{color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
@media (max-width:760px){.grid2{grid-template-columns:1fr}.queue{grid-template-columns:repeat(2,1fr)}.three{grid-template-columns:1fr}.prow{grid-template-columns:minmax(100px,140px) 1fr 48px 30px}}
@media (prefers-reduced-motion:no-preference){.pbar i{transition:flex .3s}}
"""

page = f"""<title>NeetCode 150 Ledger</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header><h1>NeetCode 150 Ledger</h1><p>{E(sub)}</p></header>

<section><div class="tiles">{tiles_html}</div></section>

<section class="today"><h2>Today</h2>{light_note}<ul>{"".join(today_items)}</ul>
{('<h2 style="margin-top:18px">Done today</h2><ul>' + done_rows + '</ul>') if done_rows else ''}</section>

<section><h2>Progress by section</h2><div class="grid2">{"".join(prog)}</div>
<div class="legend"><span><i style="background:var(--ver)"></i>verified</span><span><i style="background:var(--sol)"></i>solved</span>
<span><i style="background:var(--unv)"></i>solved before, unverified</span><span><i style="background:var(--todo)"></i>to do</span><span>★ n = Amazon-priority problems left (score ≥ 50)</span></div></section>

<section><h2>Re-solve queue, next seven days</h2><div class="queue">{"".join(queue)}</div></section>

<section><h2>Trends by week</h2><div class="trends">{trends}</div></section>

<section class="three">
<div><h2>Weak spots</h2><ul>{weak_html}</ul></div>
<div><h2>Errors this week</h2><ul>{err_html}</ul></div>
<div><h2>Mocks</h2><ul>{mock_html}</ul></div>
</section>

<footer>Generated {today.isoformat()} from plan/problems.json · Amazon frequency from LeetCode's six-month company tag (2026-09-17) · tiers: A ≥ 50 → re-solve at 3, 7, 21 days; B 30–50 → 3, 10; C &lt; 30 → 4</footer>
</div>
"""
open(OUT, "w").write(page)
print(OUT)
