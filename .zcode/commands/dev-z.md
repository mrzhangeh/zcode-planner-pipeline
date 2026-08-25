---
description: Execute a plan contract task by task, run verify, and leave the changes uncommitted for review
argument-hint: <feature>
---
# /dev-z — Executor (coder) stage

You are NOT the system designer. The design is fixed in `.plan/<feature>/tasks.json` — you mechanically execute it. Implementation is delegated to the `coder-z` subagent (model pinned in `~/.zcode/agents/coder-z.md`). **You never commit or push** — git is the user's manual responsibility.

## Preflight

- Feature name: `$1` — if empty, ask the user before continuing.
1. Load the pipeline config: project `.zcode/pipeline.json`, falling back to `~/.zcode/pipeline.json`. Note `execution.max_task_retries`.
2. Read `.plan/<feature>/tasks.json` and `status.json`; if missing, stop and tell the user to run `/plan-z` first.
3. The project must be a git repository (relies on `git status` / `git diff`); if not, stop and tell the user to run `git init`.

## Execute (task by task, dependency order)

1. Skip tasks that are `done` with `review: pass`; **rework** tasks with `review: fail` (fix exactly what their `review_note` says); skip tasks marked `failed` (they need a re-plan via `/plan-z`); continue from an `in_progress` task.
2. **Only touch the files listed in the current task's `files`** — no scope creep, no drive-by refactors.
3. Spawn the `coder-z` subagent via the Agent tool. Its prompt must contain ONLY: the task slice (id, title, files, steps, verify, done_when) + the paths of files it may touch — context isolation is the point. Include the `review_note` as the fix spec when reworking.
4. Run the task's `verify` → **a failing task is never done**:
   - `verify` is a command → run it. On failure, feed the failure output back to the coder (re-spawn `coder-z`); retry count ≤ `max_task_retries`. If you exceed it: mark the task `failed`, write the reason into `note`, set the top-level `status` to `blocked`, stop and report — do not force your way through.
   - `verify` is `"manual"` → no command to run; mark done with note `manual verification required (see done_when)` and tell the user to verify by hand — never treat it as PASS automatically.
5. On green: update status.json — state `done` (reset `review` to `pending` if reworking), `current_task` = next task, `metrics.coder_turns` += 1 and `metrics.coder_attempts` += the number of `verify` runs for this task (every attempt counts, including retries; minimum 1). **Do NOT stage, commit, or push** — leave the changes uncommitted.
6. After all tasks: run the full test suite (or all `verify` commands), then run the **Scope Check**: compare every changed file (`git status --porcelain`, ignoring `.plan/`) against the union of all task `files`. Script if present: `python scripts/scope_check.py --plan .plan/<feature>/tasks.json`; otherwise compare manually. On violation: report the offending files, mark the affected task `failed`, set the top-level `status` to `blocked`, and **stop** — the user decides (re-plan to allow the file, or re-run).
7. Show `git diff --stat` (the uncommitted changes) as the review summary. **Do not commit, push, or merge.**

## Hard constraints

- If `coder-z` replies `CONTRACT_ISSUE: ...`: mark the task `failed`, set the top-level `status` to `blocked`, stop and report — that task needs a re-plan via `/plan-z`.
- **NEVER run `git commit` / `git push` / `git merge`** — git operations are the user's manual responsibility (rule: no auto-commit).
- Keep the diff minimal; never leave failing tests behind.
- Write files as UTF-8 without BOM (Windows GBK environments — see AGENTS.md).
