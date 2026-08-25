---
description: Run the full pipeline (plan, dev, review) for one feature
argument-hint: <feature>
---
# /pipeline-z — full pipeline orchestrator

Chains the three stages for one feature, following the `/plan-z`, `/dev-z`, `/review-z` procedures exactly. Git operations stay manual: nothing is committed, pushed, or merged automatically. Coder/reviewer run as pinned subagents; the main session stays on the planner model (`roles.planner`) for the whole cycle.

## Preflight

1. Feature name: `$1` — if empty, ask the user before continuing.
2. Load the pipeline config: project `.zcode/pipeline.json`, falling back to `~/.zcode/pipeline.json`. Note `roles.planner`.
3. The project must be a git repository.

## Stages (stop at every checkpoint — never skip them)

1. **Planner** — confirm the current session model is `roles.planner` (remind the user if not). Run the `/plan-z` procedure: explore the repo, run Plan Lint, write `.plan/<feature>/` (`plan.md`, `tasks.json`, `status.json`).
2. **STOP 1** — print the plan summary + lint result; wait for the user to confirm.
3. **Executor** — run the `/dev-z` procedure: task by task via `coder-z` → `verify` → update status.json; after all tasks, full suite + **Scope Check**. Never commit or push.
4. **STOP 2** — print the scope-check result + `git diff --stat` (the uncommitted changes); ask whether to proceed to review.
5. **Reviewer** — run the `/review-z` procedure via `reviewer-z`; write `review: pass|fail` + `review_note` into status.json.
6. Any task is `review: fail` → tell the user to re-run `/dev-z <feature>` then `/review-z <feature>`; impossible `done_when` → re-run `/plan-z`.
7. All pass → final summary: scope-check result, `git diff --stat`, review table. Remind the user to review the diff and commit/push manually.

## Constraints

- Never skip the STOP points.
- **Never run `git commit` / `git push` / `git merge`** — git is the user's manual responsibility.
- Never skip tests, never redesign the plan.
- Write files as UTF-8 without BOM.
