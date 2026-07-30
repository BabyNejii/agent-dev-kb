#!/usr/bin/env python3
"""Regenerate index/index.json from every technique file's frontmatter.

The markdown files are the source of truth; index.json is a disposable, flat
list for fast filtering (by category, maturity, ecosystem, etc.).

Usage:  python tools/build_index.py
Requires: PyYAML  (pip install pyyaml)
"""
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required. Install with:  pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
TECH_DIR = ROOT / "techniques"
OUT = ROOT / "index" / "index.json"

FRONTMATTER_KEYS = {
    "id", "title", "category", "ecosystems", "problem", "maturity",
    "confidence", "effort_to_adopt", "works_with", "supersedes",
    "sources", "added", "updated",
}


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return yaml.safe_load(text[3:end])


def main():
    entries, problems = [], []
    for path in sorted(TECH_DIR.rglob("*.md")):
        if path.name.startswith("_"):  # skip _TEMPLATE.md
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            where = f" (line {mark.line + 1})" if mark else ""
            problems.append(f"{rel}: YAML error{where} — {getattr(e, 'problem', e)}")
            continue
        if not fm:
            problems.append(f"{rel}: no valid frontmatter")
            continue
        if fm.get("id") != path.stem:
            problems.append(f"{rel}: id '{fm.get('id')}' != filename '{path.stem}'")
        entry = {k: fm.get(k) for k in FRONTMATTER_KEYS}
        entry["path"] = rel
        entries.append(entry)

    OUT.parent.mkdir(exist_ok=True)
    # default=str renders YAML-parsed dates (datetime.date) as ISO strings
    OUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"Indexed {len(entries)} entries -> {OUT.relative_to(ROOT).as_posix()}")
    by_cat = {}
    for e in entries:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:14} {n}")
    if problems:
        print("\nWARNINGS:")
        for p in problems:
            print(f"  ! {p}")


if __name__ == "__main__":
    main()
