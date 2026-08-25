# Contract — the three artifacts

This is the core of the design. `/plan-z` produces three files under `.plan/<feature>/`; `/dev-z` consumes them; `/review-z` annotates them. The contract's density determines whether a cheap coder model can execute it reliably.

## 1. `plan.md` — for humans

Background, approach, key trade-offs, risks, affected files. Keep it short; the machine-readable detail belongs in `tasks.json`. Its main job: let a human (or the planner on a re-plan) understand *why*, so the *what* in `tasks.json` can be trusted.

## 2. `tasks.json` — for the machine

The coder's **only** execution input. Schema:

```json
{
  "feature": "payment",
  "summary": "Add credit-card payment with webhook verification",
  "tasks": [
    {
      "id": "T01",
      "title": "PaymentService argument validation",
      "depends_on": [],
      "steps": [
        "In PaymentService.pay(): raise ValueError when amount_cents <= 0 or card_token is empty (current code returns an error result — change it to raise)",
        "Add test_pay_rejects_invalid_args to tests/test_payment.py covering both cases",
        "Do not touch app/webhook.py or app/utils.py"
      ],
      "files": ["app/payment.py", "tests/test_payment.py"],
      "verify": "python -m pytest -q tests/test_payment.py",
      "done_when": [
        "amount_cents <= 0 raises ValueError",
        "empty card_token raises ValueError",
        "valid args still return ok=True",
        "app/webhook.py and app/utils.py are unchanged"
      ]
    }
  ]
}
```

### Fields

| Field | Meaning | Requirement |
|---|---|---|
| `id` | unique task id (e.g. `T01`) | required |
| `title` | short title | required |
| `depends_on` | task ids that must be done first | required (may be `[]`) |
| `steps` | contract-level steps: signatures, fields, edge cases, error handling | required, non-empty |
| `files` | the ONLY files the coder may modify | required, non-empty |
| `verify` | a command that must pass, or the literal `"manual"` | required, non-empty |
| `done_when` | verifiable completion criteria — the reviewer's checklist and the human's manual-verification checklist | required, non-empty |

### `verify` modes

- **command** (a string, e.g. `"python -m pytest -q tests/test_payment.py"`) — the coder must run it and it must pass. It may be any check: pytest, a linter, or a dedicated behavior-check script (e.g. under `spec/`) that asserts the real contract deterministically, so the coder cannot bypass it by writing its own tests.
- **`"manual"`** — no command exists (no test framework, config-only change, etc.). The task is marked done with an explicit `manual verification required` note and the human checks `done_when` by hand. Never silently treated as PASS.

### Rules

| Rule | Why |
|---|---|
| `steps` must be contract-level: signatures, fields, edge cases, error handling | An abstract step ("implement login") forces the weak model to design → it silently drifts or fails |
| Keep each task small (one file or one module) | A weak model can finish and verify it alone; the diff stays reviewable |
| Every task has `verify` | Without a runnable gate, the coder has no definition of done |
| Every task has `done_when` | The reviewer needs a checklist; the human needs a manual checklist |
| `depends_on` expresses ordering | `/dev-z` executes in topological order |
| Only the task's `files` may be modified | Prevents scope creep from the cheap model; enforced by Scope Check |

### Bad vs good `steps`

- Bad: `Implement the login endpoint`
- Good: `Add POST /auth/login to auth.py; request body {"email": str, "password": str}; validate email format and 8-char min password; on success return {"token": <jwt>, "expires_in": 3600}; on invalid credentials return 401 {"error": "invalid_credentials"}; never leak whether the email exists`

## Plan Lint — structural checks only

Run by `/plan-z` **before** human approval. Hard failures must be fixed by the planner; soft items are warnings for the human.

**Hard (fail → fix the plan):**

- every task has `id`, `title`, `steps`, `files`, `verify`, `done_when`, all non-empty
- task ids are unique
- every `depends_on` id exists
- `verify` is a non-empty string (a command or `"manual"`)

**Soft (warn, don't fail):**

- `steps` has more than 6 items, or `files` more than 8
- abstract step wording ("optimize", "improve", "handle exceptions", "refactor")
- `verify` is `"manual"` → warn "manual verification required"
- duplicate `title`s

No semantic judgment ("is this plan good?") — the lint only answers "is this plan structurally executable?".

## 3. `status.json` — progress, review, resume, metrics

```json
{
  "feature": "payment",
  "status": "planned",
  "created": "2026-08-24",
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

- top-level `status`: `planned | in_progress | done | blocked`
- `current_task`: the task being worked on (resume point)
- `last_error`: the last failure message (null when clean)
- `metrics`: `planner_turns` (planning invocations), `coder_turns` (tasks executed), `reviewer_turns` (review invocations), `coder_attempts` (total `verify` runs, including retries — every attempt counts, minimum 1 per task). Record tokens only if the environment exposes them.
- per-task `state`: `pending | in_progress | done | failed`
- per-task `review`: `pending | pass | fail` — set by `/review-z`
- per-task `note`: the reason when a task ends up `failed` after `max_task_retries`
- per-task `review_note`: actionable, contract-level fix feedback from `/review-z` (facts only, no style opinions)

State flow: `/dev-z` skips tasks that are `done` with `review: pass`, reworks `review: fail` tasks (fixing per `review_note`, then resetting `review` to `pending`), skips `failed` tasks (they need a re-plan via `/plan-z`), and continues from `in_progress`.

## Encoding

All artifacts must be UTF-8 **without BOM** (Windows GBK environments corrupt BOM/encoding otherwise).
