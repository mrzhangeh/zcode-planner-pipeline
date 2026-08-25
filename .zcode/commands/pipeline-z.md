---
description: Run the full pipeline (plan, dev, review) for one feature
argument-hint: <feature>
---
# /pipeline-z — full pipeline orchestrator

Chains the three stages for one feature. You are the ORCHESTRATOR — the actual planning, coding, and reviewing follow the `/plan-z`, `/dev-z`, `/review-z` procedures exactly. Git operations stay manual: nothing is committed, pushed, or merged automatically.

## Preflight

1. Feature name: `$1` — if empty, ask the user before continuing.
2. Load the pipeline config: project `.zcode/pipeline.json`, falling back to `~/.zcode/pipeline.json`. Note `roles.planner` and `execution.driver`:
   - `driver: subagent` (v2) — the main session stays on the planner model for the whole cycle; coder/reviewer run as pinned subagents (`coder-z`, `reviewer-z`).
   - `driver: self` (v1, legacy) — switch the session model between stages.
3. The project must be a git repository.

## Stages (stop at every checkpoint — never skip them)

1. **Planner** — confirm the current session model is `roles.planner` (remind the user if not). Run the `/plan-z` procedure exactly: explore the repo, run Plan Lint, write `.plan/<feature>/` (`plan.md`, `tasks.json`, `status.json`).
2. **STOP 1** — print the plan summary + lint result and wait for the user to confirm. (driver `self` only: also ask the user to switch the session model to `roles.coder`.)
3. **Executor** — run the `/dev-z` procedure exactly: task by task, delegate to `coder-z` (subagent) or implement in-session (self) → run `verify` → update status.json. After all tasks: full suite + **Scope Check**. **Never commit or push.**
4. **STOP 2** — after all tasks, print the scope-check result + `git diff --stat` (the uncommitted changes); ask whether to proceed to review.
5. **Reviewer** — run the `/review-z` procedure exactly: delegate to `reviewer-z` (subagent) or review in-session (self); write `review: pass|fail` + `review_note` into status.json.
6. If any task is `review: fail` → tell the user to re-run `/dev-z <feature>` (feedback is in `review_note`), then `/review-z <feature>` again. If `done_when` is impossible or contradictory, tell the user to re-run `/plan-z` instead.
7. All pass → final summary: scope-check result, `git diff --stat`, review table. Remind the user to review the diff and commit/push manually.

## Constraints

- Never skip the STOP points.
- **Never run `git commit` / `git push` / `git merge`** — git is the user's manual responsibility.
- Never skip tests, never redesign the plan.
- Write files as UTF-8 without BOM.
