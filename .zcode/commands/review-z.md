---
description: Review completed task diffs against the done_when criteria in tasks.json
argument-hint: <feature>
---
# /review-z — Reviewer stage

You are the SECOND gate; the test runner is the first. You do **contract review**, not logic proof: you check `done_when`, scope, and `verify` — you do not try to prove the code is bug-free. Review is delegated to the read-only `reviewer-z` subagent (model pinned in `~/.zcode/agents/reviewer-z.md`). You only review — you never commit or push.

## Preflight

- Feature name: `$1` — if empty, ask the user before continuing.
1. Load the pipeline config: project `.zcode/pipeline.json`, falling back to `~/.zcode/pipeline.json`.
2. Read `.plan/<feature>/tasks.json` and `status.json`; if missing, stop and tell the user to run `/plan-z` first.
3. The project must be a git repository.

## Review (each task with state = `done` and `review` != `pass`)

1. Inspect the changes: `git diff` (working tree), or the user's manual commits (`git log` / `git show`) if already committed. Attribute changes to tasks by `files`.
2. Check against `done_when` and `steps`:
   - every `done_when` criterion is verifiably met
   - only files in `task.files` were touched (no scope creep)
   - `verify` is green — or `"manual"` (then flag "manual verification required", do not pretend it passed)
   - no obvious contract violations (signatures/fields present, no leftover TODOs)
3. Re-run the task's `verify` unless the full suite was just run and is green.
4. Delegate to the `reviewer-z` subagent via the Agent tool. Its prompt must contain ONLY: the task slice (files, steps, done_when) + the diff output (`git diff`) + the `verify` result. Collect its verdict + `review_note`, then write `review: pass|fail` + `review_note` into status.json yourself. Update `metrics.reviewer_turns` += 1.

## Output

- A table: task | verdict | note.
- All pass → the changes are ready — the user reviews and commits manually.
- Any fail → tell the user to re-run `/dev-z <feature>` (feedback is in `review_note`); if `done_when` is impossible or contradictory, tell the user to re-run `/plan-z` instead.

## Constraints

- NEVER modify code. Only status.json and the report.
- Never run `git commit` / `git push` / `git merge`.
- `review_note` contains only verifiable facts against `tasks.json`.
