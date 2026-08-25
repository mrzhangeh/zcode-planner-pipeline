# examples/payment — pipeline test range

A deliberately small Python app used as the **real acceptance target** for the planner pipeline. The baseline is green; the six tasks in `.plan/payment/tasks.json` are engineered to probe each pipeline capability — including the failure paths (retry, scope check).

## Structure

```
examples/payment/
├── app/            # payment.py (service), webhook.py (HMAC), utils.py (constant-time)
├── tests/          # test_payment.py, test_webhook.py (baseline, green)
├── spec/           # deterministic behavior-check scripts (trap verify targets, not collected by pytest)
├── requirements.txt
├── README.md
└── .plan/payment/  # plan.md, tasks.json (6 tasks), status.json — the contract (/plan-z regenerates it)
```

## Baseline

```bash
cd examples/payment
pip install -r requirements.txt
python -m pytest -q        # must be green before any task runs
```

## Run the pipeline on it

1. From `examples/payment`, run `/plan-z payment`, confirm the plan.
2. Run `/dev-z payment` — tasks are executed by the `coder-z` subagent, verified per task.
3. Run `/review-z payment`.
4. Review the working-tree diff, then commit/push manually.

## Expected outcomes (the traps)

| Task | Trap | Expected behaviour |
|---|---|---|
| T01 | empty-token case easy to miss | verify fails → retry → pass |
| T02 | must create new files | coder stays inside `files` and creates app/refund.py + tests/test_refund.py |
| T03 | steps forbid touching payment.py | file-boundary respected |
| T04 | tests/test_utils.py does not exist | verify fails until the coder creates it |
| T05 | **deterministic** — verify is the pre-written `spec/t05_currency_check.py`; the coder cannot bypass it by writing its own tests | naive impl fails the spec → retry → pass |
| T06 | **scope trap** — `done_when` requires MAX_AMOUNT_CENTS in app/utils.py but `files` excludes it | the contract is unsatisfiable inside `files`: expected STOP (scope violation or CONTRACT_ISSUE), never a silent pass |

The pipeline never commits: after `/dev-z` the changes stay in the working tree for human review.
