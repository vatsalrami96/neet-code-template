#!/usr/bin/env python3
"""Generate AGENTS.md and .agents/skills/ from CLAUDE.md and .claude/skills/.

Codex reads AGENTS.md, Claude Code reads CLAUDE.md. They are the same manual with two names, so
only the .claude/ copies are edited by hand; run this after any change to them.
    python3 scripts/sync_agents.py [--check]
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = "--check" in sys.argv

# Identifiers that merely contain the word "claude" and must survive untouched: MCP tool names,
# the artifact host, the product name. A naive global replace mangles these - it is what turned
# `.claude/skills/` into `.Codex/skills/` by hand.
PROTECT = re.compile(r"mcp__[A-Za-z0-9_-]+|claude\.ai|Claude Code")
PATHS = [("CLAUDE.md", "AGENTS.md"), (".claude/skills/", ".agents/skills/"), (".claude/", ".agents/")]
AGENT = re.compile(r"\bClaude\b")


def convert(text):
    held = []

    def stash(m):
        held.append(m.group(0))
        return f"\0{len(held) - 1}\0"

    text = PROTECT.sub(stash, text)
    for a, b in PATHS:
        text = text.replace(a, b)
    text = AGENT.sub("Codex", text)
    for i, s in enumerate(held):
        text = text.replace(f"\0{i}\0", s)
    return text


def emit(src, dst):
    out = convert(open(src).read())
    if CHECK:
        cur = open(dst).read() if os.path.exists(dst) else None
        if cur != out:
            print(f"STALE: {os.path.relpath(dst, ROOT)}")
            return False
        return True
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(out)
    return True


ok = emit(os.path.join(ROOT, "CLAUDE.md"), os.path.join(ROOT, "AGENTS.md"))
src_dir = os.path.join(ROOT, ".claude", "skills")
dst_dir = os.path.join(ROOT, ".agents", "skills")
if not CHECK and os.path.isdir(dst_dir):
    shutil.rmtree(dst_dir)
n = 0
for name in sorted(os.listdir(src_dir)):
    s = os.path.join(src_dir, name, "SKILL.md")
    if os.path.exists(s):
        ok &= emit(s, os.path.join(dst_dir, name, "SKILL.md"))
        n += 1
if CHECK:
    print("AGENTS.md and .agents/ are in sync" if ok else "run: python3 scripts/sync_agents.py")
    sys.exit(0 if ok else 1)
print(f"wrote AGENTS.md and {n} skills to .agents/skills/")
