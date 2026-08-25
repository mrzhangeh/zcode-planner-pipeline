# Plan: payment (test range)

## Background

This is a **test range** for the planner pipeline, not a product feature. The app is deliberately small (Python, stdlib + pytest) and the six tasks are engineered to exercise each pipeline capability once — including its failure paths. Run `/plan-z` → `/dev-z` → `/review-z` on this directory and compare the actual behaviour with the expected outcomes below.

## Approach

- Minimal app: `app/payment.py` (PaymentService + provider protocol), `app/webhook.py` (HMAC verification), `app/utils.py` (constant-time compare), `spec/` (deterministic behavior-check scripts).
- Baseline is green (`python -m pytest -q` passes before any task runs; `spec/` is not collected by pytest).
- Tasks build on each other via `depends_on` (T01 → T02/T05, T03 → T04).

## The six tasks and what they probe

| Task | Probes | Expected pipeline behaviour |
|---|---|---|
| T01 pay() argument validation | basic coder | naive implementation misses the empty-token case → verify fails → retry; correct impl passes |
| T02 RefundService | multi-file change | coder must create a new file (app/refund.py + tests/test_refund.py) and stay in files |
| T03 webhook process entry | file boundary | steps forbid touching payment.py; coder must stay inside webhook.py + test_webhook.py |
| T04 constant-time + tests | adding tests | tests/test_utils.py does not exist — verify fails unless the coder creates it |
| T05 currency validation | deterministic retry trap | verify is a pre-written spec script (`spec/t05_currency_check.py`) the coder cannot bypass — a naive impl (missed default currency, wrong error) fails it → retry → pass |
| T06 amount cap | scope trap | `done_when` REQUIRES MAX_AMOUNT_CENTS in app/utils.py, but `files` excludes it — the contract is unsatisfiable within bounds. Expected: the system STOPS (scope violation or CONTRACT_ISSUE) instead of silently resolving |

## Key trade-offs / risks

- T05/T06 are intentionally adversarial — that is the point. T05's spec script must not be modified (scope check would catch it). T06 is designed to be unsatisfiable inside `files`, so a correct outcome is a STOP, not a pass.
- The pipeline never commits: after `/dev-z` the working tree holds everything for human review.
- Baseline tests are correct; the "traps" are in the task design, not in broken tests.

## Affected files

- `app/payment.py`, `app/refund.py` (new), `app/webhook.py`, `app/utils.py`
- `tests/test_payment.py`, `tests/test_webhook.py`, `tests/test_refund.py` (new), `tests/test_utils.py` (new)
- `spec/t05_currency_check.py` (pre-written, must not be modified)
