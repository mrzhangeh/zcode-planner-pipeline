#!/usr/bin/env python3
"""Validate the planner-pipeline repo: JSON, YAML frontmatter, schemas, model sync.

Usage:  python scripts/validate.py
Exit 0 on success, 1 on any hard failure. File-existence issues are warnings.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMMANDS = ROOT / ".zcode" / "commands"
AGENTS = ROOT / ".zcode" / "agents"
EXAMPLE = ROOT / "examples" / "payment"

errors: list[str] = []
warnings: list[str] = []
files_checked = 0


def fail(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def check_json(path: pathlib.Path, required: tuple[str, ...] = ()):
    global files_checked
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        files_checked += 1
    except Exception as exc:  # noqa: BLE001
        fail(f"{path.relative_to(ROOT)}: JSON parse error — {exc}")
        return None
    for key in required:
        if key not in data:
            fail(f"{path.relative_to(ROOT)}: missing key '{key}'")
    return data


def check_frontmatter(path: pathlib.Path, required: tuple[str, ...] = ()):
    global files_checked
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return {}
    front = text.split("---", 2)[1]
    try:
        import yaml  # optional dependency

        data = yaml.safe_load(front) or {}
    except ImportError:
        data = {}
        for line in front.splitlines():
            m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if m:
                data[m.group(1)] = m.group(2).strip()
    files_checked += 1
    for key in required:
        if key not in data or data[key] in (None, ""):
            fail(f"{path.relative_to(ROOT)}: frontmatter missing/empty '{key}'")
    return data


def check_no_bom(path: pathlib.Path) -> None:
    if path.read_bytes()[:3] == b"\xef\xbb\xbf":
        fail(f"{path.relative_to(ROOT)}: UTF-8 BOM present")


def main() -> int:
    # 1. pipeline.json
    pipe = check_json(ROOT / ".zcode" / "pipeline.json", required=("roles", "execution"))
    check_no_bom(ROOT / ".zcode" / "pipeline.json")
    if pipe:
        driver = (pipe.get("execution") or {}).get("driver")
        if driver != "subagent":
            fail(f"pipeline.json: execution.driver must be 'subagent' (single-driver design), got '{driver}'")

    # 2. commands + agents frontmatter
    for f in sorted(COMMANDS.glob("*.md")):
        check_frontmatter(f, required=("description", "argument-hint"))
        check_no_bom(f)
    agent_models: dict[str, str] = {}
    for f in sorted(AGENTS.glob("*.md")):
        fm = check_frontmatter(f, required=("name", "description", "model"))
        check_no_bom(f)
        agent_models[f.stem] = str(fm.get("model", ""))

    # 3. model sync: agent model == pipeline.json roles.coder/reviewer
    if pipe:
        roles = pipe.get("roles", {})
        for agent, role in (("coder-z", "coder"), ("reviewer-z", "reviewer")):
            expected = (roles.get(role) or {}).get("model")
            actual = agent_models.get(agent)
            if expected and actual and actual != expected:
                fail(f"model drift: {agent}.md model '{actual}' != pipeline.json roles.{role}.model '{expected}'")

    # 4. example tasks.json schema + Plan Lint hard rules
    tasks_path = EXAMPLE / ".plan" / "payment" / "tasks.json"
    tasks_data = check_json(tasks_path)
    if tasks_data is not None:
        seen: set[str] = set()
        all_ids = {t.get("id") for t in tasks_data.get("tasks", [])}
        for t in tasks_data.get("tasks", []):
            tid = t.get("id")
            if tid in seen:
                fail(f"{tasks_path.relative_to(ROOT)}: duplicate task id {tid}")
            seen.add(tid)
            for key in ("id", "title", "steps", "files", "verify", "done_when"):
                if not t.get(key):
                    fail(f"{tasks_path.relative_to(ROOT)} task {tid}: missing/empty '{key}'")
            if not isinstance(t.get("verify"), str):
                fail(f"{tasks_path.relative_to(ROOT)} task {tid}: verify must be a command string or 'manual'")
            if t.get("verify") == "manual":
                warn(f"{tasks_path.relative_to(ROOT)} task {tid}: manual verification required")
            for dep in t.get("depends_on", []):
                if dep not in all_ids:
                    fail(f"{tasks_path.relative_to(ROOT)} task {tid}: depends_on references unknown '{dep}'")
            for f in t.get("files", []):
                if not (EXAMPLE / f).exists():
                    warn(f"{tasks_path.relative_to(ROOT)} task {tid}: file '{f}' does not exist yet (task may create it)")

    # 5. example status.json schema
    status_path = EXAMPLE / ".plan" / "payment" / "status.json"
    status_data = check_json(status_path, required=("feature", "status", "tasks"))
    if status_data is not None:
        for tid, tv in status_data.get("tasks", {}).items():
            for key in ("state", "retries", "note", "review", "review_note"):
                if key not in tv:
                    fail(f"{status_path.relative_to(ROOT)}: task {tid} missing '{key}'")

    # 6. summary
    for w in warnings:
        print(f"  ⚠ {w}")
    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"Validation passed: {files_checked} files checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
