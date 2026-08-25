#!/usr/bin/env python3
"""Sync agent `model` fields from pipeline.json (the single source of truth).

Usage:  python scripts/sync_agents.py

Patches ONLY the `model:` line in the frontmatter of
.zcode/agents/coder-z.md and .zcode/agents/reviewer-z.md to match
pipeline.json roles.coder / roles.reviewer. Everything else is preserved.
Run scripts/validate.py afterwards to confirm no drift remains.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPE = ROOT / ".zcode" / "pipeline.json"
AGENTS = ROOT / ".zcode" / "agents"

MAPPING = {"coder-z": "coder", "reviewer-z": "reviewer"}


def main() -> int:
    try:
        pipe = json.loads(PIPE.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"error: cannot read {PIPE}: {exc}")
        return 1

    changed: list[str] = []
    for agent, role in MAPPING.items():
        model = (pipe.get("roles") or {}).get(role, {}).get("model")
        if not model:
            print(f"error: pipeline.json roles.{role}.model is missing")
            return 1
        path = AGENTS / f"{agent}.md"
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^(---\n)(.*?)(\n---)", text, re.S)
        if not m:
            print(f"error: {path} has no frontmatter")
            return 1
        head, fm, tail = m.group(1), m.group(2), m.group(3)
        if not re.search(r"^model:", fm, re.M):
            print(f"error: {path} frontmatter has no model field")
            return 1
        new_fm = re.sub(r"^model:.*$", f"model: {model}", fm, flags=re.M)
        new_text = head + new_fm + tail + text[m.end():]
        if new_text != text:
            path.write_text(new_text, encoding="utf-8", newline="\n")
            changed.append(f"{agent}.md -> {model}")

    if changed:
        print("Synced:")
        for c in changed:
            print(f"  {c}")
    else:
        print("Already in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
