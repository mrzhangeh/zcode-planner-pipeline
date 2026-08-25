---
description: Execute a plan contract task by task, run verify, and leave the changes uncommitted for review
argument-hint: <feature>
---
# /dev-z — Executor (coder) stage

You are NOT the system designer. The design is fixed. Your job is to **mechanically and strictly execute** `.plan/<feature>/tasks.json`. **You never commit or push** — the user reviews the changes and handles git manually.

## Preflight

- Feature name: `$1` — if empty, ask the user before continuing.
1. **Load the pipeline config**: project `.zcode/pipeline.json`, falling back to `~/.zcode/pipeline.json`. Read `execution.driver` and `execution.max_task_retries`:
   - `driver: subagent` (v2) — implementation is delegated to the `coder-z` subagent; its model is pinned in `~/.zcode/agents/coder-z.md` and must match `roles.coder`.
   - `driver: self` (v1, legacy) — this session is the coder model (see `roles.coder`).
2. Read `.plan/<feature>/tasks.json` and `status.json`; if they are missing, stop and tell the user to run `/plan-z` first.
3. The project must be a git repository (this flow relies on `git status` / `git diff`); if not, stop and tell the user to run `git init`.

## Execute (task by task, dependency order)

1. Skip tasks that are `done` with `review: pass`; **rework** tasks with `review: fail` (fix exactly what their `review_note` says); skip tasks marked `failed` (they need a re-plan via `/plan-z`); continue from an `in_progress` task.
2. **Only touch the files listed in the current task's `files`** — no scope creep, no drive-by refactors.
3. Obtain the implementation for the task:
   - `driver: subagent` — spawn the `coder-z` subagent via the Agent tool. Its prompt must contain ONLY: the task slice (id, title, files, steps, verify, done_when) + the paths of files it may touch. Do not paste the whole conversation — context isolation is the point. If a `review_note` exists, include it as the fix spec.
   - `driver: self` — implement directly in this session.
4. Run the task's `verify` → **a failing task is never done**:
   - `verify` is a command → run it. On failure, feed the failure output back to the coder (re-spawn `coder-z` / fix in-session); retry count ≤ `max_task_retries`. If you exceed it, mark the task `failed`, write the reason into status.json's `note`, set the top-level `status` to `blocked`, stop and report — do not force your way through.
   - `verify` is `"manual"` → no command to run. Mark the task `done` with note `manual verification required (see done_when)` and tell the user to verify by hand; never treat it as PASS automatically.
5. On green: update status.json — state `done` (reset `review` to `pending` if reworking a `review: fail` task), `current_task` = next task, `metrics.coder_turns` += 1 and `metrics.coder_attempts` += the number of `verify` runs for this task (every attempt counts, including retries; minimum 1). **Do NOT stage, commit, or push** — leave the changes in the working tree for the user to review.
6. After all tasks: run the project's full test suite (or all `verify` commands combined), then run the **Scope Check**:
   - Compare every changed file (`git status --porcelain`, ignoring `.plan/`) against the **union of all task `files`**. Any changed file outside the union is a scope violation.
   - Script if present: `python scripts/scope_check.py --plan .plan/<feature>/tasks.json` — otherwise do the comparison manually.
   - On violation: report the offending files, mark the affected task `failed` with the reason, and **stop** — do not proceed. The user decides (fix the plan to allow the file, or re-run `/dev-z`).
7. Show `git diff --stat` (the uncommitted changes) as the review summary.
8. **Do not commit, do not push, do not merge**: present the summary and let the user review the diff, then handle git manually.

## Hard constraints

- Do not redesign the architecture or second-guess the plan; if a subagent replies `CONTRACT_ISSUE: ...`, mark the task `failed`, set the top-level `status` to `blocked`, stop and report to the user (that task needs a re-plan via `/plan-z`).
- **NEVER run `git commit` / `git push` / `git merge`** — git operations are the user's manual responsibility (rule: no auto-commit).
- Keep the diff minimal; never leave failing tests behind.
- Write files as UTF-8 without BOM (Windows GBK environments — see AGENTS.md).
