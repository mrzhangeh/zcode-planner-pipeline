#!/usr/bin/env python3
"""Scope check: ensure all working-tree changes stay inside the union of task files.

Usage:  python scripts/scope_check.py --plan .plan/<feature>/tasks.json [--cwd <git dir>]
Exit 0 = ok, 1 = violations found, 2 = usage/git error.
Paths under .plan/ (pipeline artifacts) are ignored.
"""
import argparse
import json
import pathlib
import subprocess
import sys

IGNORED_PREFIXES = (".plan/",)


def changed_files(cwd: str) -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True
    )
    if proc.returncode != 0:
        print(f"error: not a git repository in {cwd}: {proc.stderr.strip()}")
        sys.exit(2)
    result: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:  # rename: "R  old -> new"
            path = path.split(" -> ")[-1].strip()
        if path:
            result.append(path)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", required=True, help="path to tasks.json")
    ap.add_argument("--cwd", default=".", help="git working directory (default: current)")
    args = ap.parse_args()

    try:
        tasks = json.loads(pathlib.Path(args.plan).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"error: cannot read {args.plan}: {exc}")
        return 2

    allowed = set()
    for t in tasks.get("tasks", []):
        allowed.update(t.get("files", []))

    changed = [f for f in changed_files(args.cwd) if not f.startswith(IGNORED_PREFIXES)]
    violations = [f for f in changed if f not in allowed]

    if violations:
        print("Scope violation:")
        for f in sorted(violations):
            print(f"  ✗ {f} (not in any task.files)")
        return 1
    print(f"Scope OK: {len(changed)} changed file(s), all within task boundaries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
