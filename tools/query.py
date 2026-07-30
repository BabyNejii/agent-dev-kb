#!/usr/bin/env python3
"""Filter and list knowledge-base entries from index/index.json.

Reads the generated index, so run tools/build_index.py first if entries changed.

Examples:
  python tools/query.py --category eval --confidence verified
  python tools/query.py --ecosystem antigravity
  python tools/query.py --search worktree --full
  python tools/query.py --stats
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index" / "index.json"

# Ordered worst -> best so --min-confidence can threshold.
CONFIDENCE_ORDER = ["speculative", "reported", "verified"]


def load_entries():
    if not INDEX.exists():
        sys.exit("index/index.json not found — run: python tools/build_index.py")
    return json.loads(INDEX.read_text(encoding="utf-8"))


def matches(entry, args):
    if args.category and entry.get("category") != args.category:
        return False
    if args.confidence and entry.get("confidence") != args.confidence:
        return False
    if args.maturity and entry.get("maturity") != args.maturity:
        return False
    if args.effort and entry.get("effort_to_adopt") != args.effort:
        return False
    if args.ecosystem and args.ecosystem not in (entry.get("ecosystems") or []):
        return False
    if args.min_confidence:
        threshold = CONFIDENCE_ORDER.index(args.min_confidence)
        actual = entry.get("confidence")
        if actual not in CONFIDENCE_ORDER or CONFIDENCE_ORDER.index(actual) < threshold:
            return False
    if args.search:
        needle = args.search.lower()
        haystack = " ".join(str(entry.get(k, "")) for k in ("id", "title", "problem", "category"))
        if needle not in haystack.lower():
            return False
    return True


def print_stats(entries):
    print(f"{len(entries)} entries\n")
    for field in ("category", "confidence", "maturity", "effort_to_adopt"):
        counts = {}
        for e in entries:
            counts[e.get(field)] = counts.get(e.get(field), 0) + 1
        print(f"{field}:")
        for key, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {str(key):16} {n}")
        print()
    eco = {}
    for e in entries:
        for name in (e.get("ecosystems") or []):
            eco[name] = eco.get(name, 0) + 1
    print("ecosystems:")
    for key, n in sorted(eco.items(), key=lambda kv: -kv[1]):
        print(f"  {key:16} {n}")


def main():
    p = argparse.ArgumentParser(description="Query the agent-dev-kb index.")
    p.add_argument("--category")
    p.add_argument("--confidence", choices=CONFIDENCE_ORDER)
    p.add_argument("--min-confidence", choices=CONFIDENCE_ORDER,
                   help="include this confidence level and better")
    p.add_argument("--maturity", choices=["experimental", "emerging", "established", "deprecated"])
    p.add_argument("--effort", choices=["low", "medium", "high"])
    p.add_argument("--ecosystem", help="e.g. claude-code, antigravity, mcp, generic")
    p.add_argument("--search", help="substring match on id/title/problem")
    p.add_argument("--full", action="store_true", help="also print the problem line and path")
    p.add_argument("--paths", action="store_true", help="print only file paths (pipe-friendly)")
    p.add_argument("--stats", action="store_true", help="show distribution summary and exit")
    args = p.parse_args()

    entries = load_entries()
    if args.stats:
        print_stats(entries)
        return

    hits = sorted((e for e in entries if matches(e, args)),
                  key=lambda e: (e.get("category") or "", e.get("id") or ""))

    if args.paths:
        for e in hits:
            print(e.get("path"))
        return

    if not hits:
        print("no matches")
        return

    for e in hits:
        print(f"[{e.get('confidence','?'):11}] {e.get('category',''):14} {e.get('id','')}")
        if args.full:
            print(f"                 {e.get('problem','')}")
            print(f"                 {e.get('path','')}\n")
    print(f"\n{len(hits)} of {len(entries)} entries")


if __name__ == "__main__":
    main()
