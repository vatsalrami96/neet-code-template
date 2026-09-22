#!/usr/bin/env python3
"""Rebuild data/catalogue.json from plan/problems.json, dropping everything personal.

The catalogue is the shareable half of the state file: the problem list, section order,
difficulty, URLs and Amazon frequency. No status, attempts, notes or flags.
    python3 scripts/make_catalogue.py
"""
import json, os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = ("id", "lc_id", "title", "section", "order", "difficulty", "lc_url", "nc_url", "premium",
        "amazon_freq", "gap")

d = json.load(open(os.path.join(ROOT, "plan", "problems.json")))
cat = {
    "schema": 1,
    "generated": date.today().isoformat(),
    "source": "NeetCode 150, sections reordered: Intervals after Tries, Greedy after Advanced Graphs.",
    "amazon_freq_pulled": "2026-09-17",
    "amazon_freq_note": "LeetCode company tag, six-month list. Re-pull if it is more than a few months stale.",
    "sections": sorted(d["sections"], key=lambda s: s["order"]),
    "problems": [{k: p[k] for k in KEEP} for p in d["problems"]],
}
out = os.path.join(ROOT, "data", "catalogue.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(cat, f, indent=1)
core = sum(1 for p in cat["problems"] if not p["gap"])
print(f"{out}: {len(cat['problems'])} problems ({core} core, {len(cat['problems']) - core} gap), "
      f"{len(cat['sections'])} sections")
