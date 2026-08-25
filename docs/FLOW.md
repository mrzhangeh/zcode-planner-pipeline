# Flow — how the pipeline works

## Stages

Run the three commands in order, or `/pipeline-z <feature>` for a guided one-shot run that stops at each checkpoint. With `driver: subagent` (v2) the session model is selected once (planner); coder/reviewer are pinned subagents (`coder-z`, `reviewer-z`).

```
User request
    │
    ▼
┌─────────────────── /plan-z (strong model) ─────────────────┐
│ 1. explore repo: related code, stack, conventions          │
│ 2. write .plan/<feature>/: plan.md + tasks.json + status.json │
│ 3. STOP — user confirms the plan before any implementation │
└────────────────────────────┬───────────────────────────────┘
                             ▼
┌─────────────────── /dev-z (cheap model) ───────────────────┐
│ for each task (topological order):                         │
│   implement (only task's files) → run verify              │
│   tests red → fix, ≤ max_task_retries                      │
│   tests green → update status.json (never auto-commit) │
│ after all tasks: full test suite, git log/diff summary     │
└────────────────────────────┬───────────────────────────────┘
                             ▼
┌─────────────────── /review-z (cheap model) ────────────────┐
│ for each done task: inspect the diff vs acceptance/scope │
│ write review: pass|fail + review_note into status.json     │
│ any fail → /dev-z reworks (review_note is the fix spec)    │
└────────────────────────────┬───────────────────────────────┘
                             ▼
   user reviews → commits → pushes → merge (all manual)
```

## Role boundaries

| Role | Model | Does | Must NOT do |
|---|---|---|---|
| Planner (`/plan-z`) | strong | explore, design, write the contract | implement |
| Coder (`/dev-z`) | cheap (`coder-z` subagent) | mechanically execute tasks; rework `review: fail` tasks | redesign, scope-creep |
| Reviewer (`/review-z`) | cheap (`reviewer-z` subagent) | check diffs vs acceptance, scope, minimality | modify code, replace the test gate |

> With `execution.driver: subagent` (v2) the Coder/Reviewer are pinned subagents (`~/.zcode/agents/coder-z.md`, `reviewer-z.md`) launched via the Agent tool; with `driver: self` (v1) they are the session model.

## Gates

1. **Test gate (primary)**: nothing ships with red tests. The cheapest reliable "reviewer" is the test runner.
2. **User confirmation after `/plan-z`**: catches a misunderstood requirement before any money is spent.
3. **Reviewer (`/review-z`)**: LLM review only *after* tests are green; checks the diff against the task's acceptance criteria and scope, writes `review: pass|fail` + `review_note` into status.json. Never replaces the test gate.
4. **No auto-commit**: `/dev-z` leaves changes in the working tree; you review, commit, and push manually.

## Failure handling

- Task fails after `max_task_retries` → marked `failed` with the reason in `status.json`; `/dev-z` stops and reports. The task needs a re-plan via `/plan-z`.
- `review: fail` → `/dev-z` reworks the task using `review_note` as the fix spec; `/review-z` re-checks. This is the coder↔reviewer loop.
- Re-planning stays manual: when a task is `failed` or the acceptance criteria are impossible/contradictory, the user re-runs `/plan-z`. A future v3 may automate the escalation (SWE-AF's three-ring, simplified).

## When NOT to use this pipeline

- **Small or one-off tasks**: the planner's context-reading overhead exceeds the savings.
- **Context-heavy work**: if the strong model must read the whole codebase anyway, a single model is cheaper (orchestration is token-expensive — Anthropic measured multi-agent systems at ~15× the tokens of a chat).
- **Exploratory design**: when the design genuinely needs to emerge during implementation, a fixed plan hurts more than it helps.
- **No test harness possible**: without any runnable gate, the weak coder has no definition of done and quality collapses.

## Evidence this is grounded in

- AgentCoder (planner + coder + tester): HumanEval pass@1 96.3% at 56.9K tokens vs 90.2% at 138.2K tokens for the prior single-agent SOTA — a good split can be *better and cheaper*.
- MetaGPT: HumanEval 85.9% vs GPT-4 baseline 67%.
- Aider's architect mode: DeepSeek is "surprisingly effective" as the editor model.
- Anthropic (multi-agent research system, 2025): +90.2% on internal evals, but ~15× tokens vs chat — the cost risk is planner context, not the coder.
- SWE-AF: runs the whole loop on haiku-class models (~$20 on its Node CLI benchmark), the closest full implementation of this idea.
