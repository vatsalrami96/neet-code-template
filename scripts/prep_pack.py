#!/usr/bin/env python3
"""Generate the night-before pack from the repo's own data.  python3 scripts/prep_pack.py [--out prep/pack-DATE.md]"""
import json, os, sys, glob
from datetime import date
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "plan", "problems.json")))
sn = {s["id"]: s["name"] for s in d["sections"]}
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "prep", f"pack-{date.today()}.md")
L = [f"# Night-before pack · {date.today()}", "", "Read once, slowly. Then stop. Sleep matters more than one more problem.", ""]
weak = [p for p in d["problems"] if any(f in p["flags"] for f in ("weak", "solution-needed", "explain-failed", "failed-verify"))]
L += ["## Weak spots (re-read your insight, do not re-solve)", ""]
for p in sorted(weak, key=lambda p: -(p.get("amazon_freq") or 0)):
    L.append(f"- **{p['title']}** ({sn[p['section']]}) · {p.get('insight') or 'no insight recorded'}")
L += ["", "## Amazon top problems you own (one line each)", ""]
top = [p for p in d["problems"] if p["status"] in ("solved", "verified") and (p.get("amazon_freq") or 0) >= 50]
for p in sorted(top, key=lambda p: -p["amazon_freq"]):
    L.append(f"- {p['title']} · amz {p['amazon_freq']:.0f} · {p.get('insight') or '-'} · {p.get('complexity') or ''}")
L += ["", "## Not done (know the pattern name at least)", ""]
for p in d["problems"]:
    if p["status"] in ("todo", "solved_unverified") and (p.get("amazon_freq") or 0) >= 40:
        L.append(f"- {p['title']} ({sn[p['section']]}) · amz {p['amazon_freq']:.0f}")
for name in ("interview-process.md", "stuck-protocol.md", "edge-cases.md"):
    L += ["", f"## {name}", "", open(os.path.join(ROOT, "reference", name)).read()]
L += ["", "## Templates", ""]
for f in sorted(glob.glob(os.path.join(ROOT, "reference", "templates", "*.py"))):
    L += [f"### {os.path.basename(f)}", "```python", open(f).read().rstrip(), "```", ""]
L += ["## Leadership Principles story index", "", open(os.path.join(ROOT, "amazon", "leadership-principles.md")).read().split("## Story index")[-1]]
mocks = d.get("mocks", [])
if mocks:
    L += ["", "## Mock history", ""] + [f"- {m['date']} {m['format']} score {m.get('score')} · {m.get('notes','')}" for m in mocks]
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w").write("\n".join(L) + "\n")
print(out)
