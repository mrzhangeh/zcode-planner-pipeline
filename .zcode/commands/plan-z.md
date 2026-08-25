---
description: Plan a feature, explore the repo, and write the plan contract (plan.md, tasks.json, status.json)
argument-hint: <feature>
---
# /plan-z — Planner (architect) stage

You are the architect role. The current session should be the strong model (see `roles.planner` in the pipeline config).

## Input

- Feature name: `$1` (e.g. `payment`). If `$1` is empty, ask the user for the feature name before doing anything.
- The user may add requirement details. If you only have a feature name and it is under-specified, ask the user to clarify scope / stack / constraints before continuing.

## Steps

1. **Explore the repo**: read AGENTS.md / README; use `git ls-files` (or walk the filesystem if there are no commits yet) to find related code, the stack, and conventions. Plan against real code — never design from imagination.
2. **Load the pipeline config**: project `.zcode/pipeline.json`, falling back to `~/.zcode/pipeline.json`. If neither exists, stop and tell the user to install it (see README).
3. Create `.plan/<feature>/` and write three files:
   - `plan.md` — human-readable: background, approach, key trade-offs, risks, affected files.
   - `tasks.json` — machine-readable, exactly per the schema below; this is the coder's only execution input.
   - `status.json` — progress + metrics initialized (every task `pending`, `current_task` = first task).
4. **Run Plan Lint** (structural checks below) **before** showing the plan to the user:
   - Hard failures → fix the plan yourself and re-lint until clean.
   - Soft warnings → keep them and report them in the summary.
5. Print a summary (approach in one line + task count + lint result + warnings), then **stop and wait for the user's confirmation — do not start implementing**.

## tasks.json schema (must follow exactly)

```json
{
  "feature": "<feature>",
  "summary": "one line",
  "tasks": [
    {
      "id": "T01",
      "title": "short title",
      "depends_on": [],
      "steps": ["contract-level: function signatures, fields, error handling, edge cases — the coder must not need to design"],
      "files": ["relative/path"],
      "verify": "test command that must pass once this task is done, or \"manual\"",
      "done_when": ["verifiable completion criteria — the reviewer's checklist"]
    }
  ]
}
```

## status.json schema

```json
{
  "feature": "<feature>",
  "status": "planned",
  "created": "YYYY-MM-DD",
  "current_task": "T01",
  "last_error": null,
  "metrics": {
    "planner_turns": 1,
    "coder_turns": 0,
    "reviewer_turns": 0,
    "coder_attempts": 0
  },
  "tasks": {
    "T01": { "state": "pending", "retries": 0, "note": "", "review": "pending", "review_note": "" }
  }
}
```

`review` / `review_note` are filled by `/review-z` and consumed by `/dev-z` (rework) — initialize them as shown.

## Plan Lint rules

**Hard (fail → fix before showing the plan):**

- every task has `id`, `title`, `steps`, `files`, `verify`, `done_when` — all non-empty
- task ids are unique; every `depends_on` id exists
- `verify` is a non-empty string (a command or the literal `"manual"`)

**Soft (warn, don't fail):**

- `steps` > 6 items or `files` > 8 items
- abstract step wording ("optimize", "improve", "handle exceptions", "refactor")
- `verify` is `"manual"` → warn "manual verification required"
- duplicate titles

Do NOT judge plan quality semantically — only structural executability.

## Rules

- `steps` must be contract-level: "implement the login endpoint" is not enough — write signatures, fields, edge cases, error handling.
- Keep each task small (one file or one module) so a weak model can finish and test it on its own.
- Every task needs `verify` (a command, or `"manual"` if no test harness exists) and `done_when`.
- Express dependencies between tasks with `depends_on`; `/dev-z` executes them in topological order.
- Write files as UTF-8 without BOM (Windows GBK environments — see AGENTS.md).
