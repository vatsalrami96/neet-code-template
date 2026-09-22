#!/usr/bin/env python3
"""Write solution files from a JSON map {slug: {code, ts, lang, failedBefore, firstTs}} fetched from LeetCode.
    python3 scripts/write_solutions.py <map.json> [--history "verbatim history line"]
Existing files keep their header fields (insight, complexity, alternatives, explanation); only code and history update.
"""
import json, os, re, sys
from datetime import datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "plan", "problems.json")))
sn = {s["id"]: s["name"] for s in d["sections"]}
ids = {p["id"]: p for p in d["problems"]}

src = sys.argv[1]
raw = open(src).read()
m = json.loads(raw)
if isinstance(m, str):
    m = json.loads(m)
hist_extra = sys.argv[sys.argv.index("--history") + 1] if "--history" in sys.argv else None


def header(p, fields, history):
    amz = f"{p['amazon_freq']:.0f}" if p.get("amazon_freq") else "n/a"
    return (f'"""\n{p["title"]}  |  LeetCode {p["lc_id"]}  |  {p["difficulty"]}  |  {sn[p["section"]]}  |  Amazon {amz}\n'
            f'{p["lc_url"]}\n\n'
            f'Insight: {fields.get("insight", "")}\n'
            f'Complexity: {fields.get("complexity", "")}\n'
            f'Alternatives: {fields.get("alternatives", "-")}\n'
            f'Explanation (verbatim): {fields.get("explanation", "")}\n'
            f'History: {history}\n"""\n')


def parse_existing(path):
    fields, history = {}, ""
    if not os.path.exists(path):
        return fields, history
    txt = open(path).read()
    mm = re.match(r'"""(.*?)"""', txt, re.S)
    if not mm:
        return fields, history
    for line in mm.group(1).splitlines():
        for k in ("Insight", "Complexity", "Alternatives", "Explanation (verbatim)", "History"):
            if line.startswith(k + ":"):
                v = line[len(k) + 1:].strip()
                if k == "History":
                    history = v
                else:
                    fields[{"Explanation (verbatim)": "explanation"}.get(k, k.lower())] = v
    return fields, history


written = []
for slug, v in m.items():
    if not v or slug not in ids:
        continue
    p = ids[slug]
    folder = os.path.join(ROOT, "solutions", p["section"])
    os.makedirs(folder, exist_ok=True)
    lang = (v.get("lang") or "python3").lower()
    ext = "py" if lang.startswith("python") else ("cpp" if lang in ("cpp", "c++") else lang)
    path = os.path.join(folder, f"{p['lc_id']:04d}-{slug}.{ext}")
    fields, history = parse_existing(path)
    for k in ("insight", "complexity", "alternatives", "explanation"):
        if p.get(k):
            fields[k] = p[k]
    when = datetime.fromtimestamp(v["ts"]).strftime("%Y-%m-%d")
    lang_note = "" if lang.startswith("python") else f", in {lang} not Python"
    entry = hist_extra or f"{when} accepted on LeetCode (pre-system, unverified{lang_note}; {v.get('failedBefore', 0)} failed submissions before)"
    if entry not in history:
        history = (history + " | " if history else "") + entry
    code = v["code"].rstrip() + "\n"
    if ext == "py" and not code.startswith("from typing") and "List[" in code:
        code = "from typing import List, Optional\nfrom collections import defaultdict, deque, Counter\nimport heapq\n\n" + code
    hdr = header(p, fields, history)
    if ext != "py":
        hdr = "/*\n" + hdr.replace('"""\n', "", 1).rsplit('"""', 1)[0] + "*/\n"
        if entry.startswith(when) and "not Python" not in history:
            pass
    open(path, "w").write(hdr + "\n" + code)
    written.append(os.path.relpath(path, ROOT))
print("\n".join(written))
