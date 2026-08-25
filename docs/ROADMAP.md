# Roadmap

## v1 — done

- Commands: `/plan-z`, `/dev-z`, `/review-z`, `/pipeline-z` (YAML-safe frontmatter)
- Contract: `plan.md` / `tasks.json` / `status.json` (incl. `review` / `review_note`)
- Config: `pipeline.json` is the single routing contract; `driver = self` (manual session-model switching)
- Docs: `CONTRACT.md` / `FLOW.md` / `MODELS.md`, `examples/payment`, README (EN + zh-CN)

## v2 — implemented: automatic model routing via subagents

**Mechanism (confirmed by ZCode docs)**: subagent files at `~/.zcode/agents/<name>.md` support a `model` frontmatter field; launched via the Agent tool, with independent context, `tools` / `disallowedTools`, and `maxTurns`.

- **G1 ✅** coder/reviewer as pinned subagents (`~/.zcode/agents/coder-z.md`, `reviewer-z.md`); main session stays on the planner model — one model selection per feature.
- **G2 ✅** context isolation — subagent independent context; only the task slice + relevant files are passed.
- **G3 ✅** review loop — reviewer subagent read-only (`disallowedTools: Write, Edit`); `review: fail` → bounded rework; re-plan manual.
- **G4 ✅** guardrails — `maxTurns` (coder 30 / reviewer 20), `max_task_retries`, test gate unchanged.
- **G5 ✅** single config — `pipeline.json` `driver: subagent`; subagent `model` fields match `roles.coder/reviewer` (ids verified in the ZCode model selector: `deepseek-v4-flash-0731`, `deepseek-v4-flash`).
- Command bodies updated: `/dev-z`, `/review-z`, `/pipeline-z` delegate via the Agent tool.

Smoke tests (2026-08-24): Round 1 — full loop passed (6/6 done, 16 tests, 0 retries, traps missed). Round 2 — T06 stop verified (CONTRACT_ISSUE → failed + blocked, no force-through); T05 still 0 retries (deterministic spec check holds, retry loop unobserved); metrics sane (attempts ≥ turns). Evidence: docs/SMOKE_TEST.md.

Decision (2026-08-24): the retry loop is accepted as a known-unobserved path (bounded by `max_task_retries`; no fault-injection run planned).

P4 done (2026-08-24): single driver (`self` removed, `execution.driver: subagent` enforced by validate.py), `scripts/sync_agents.py` (pipeline.json → agent frontmatter), command slimming (dev-z / review-z / pipeline-z now orchestration-only).

## v3 — future

- Automated escalation: review fails N times → auto re-plan (SWE-AF three-ring, simplified)
- Hook hard gate for tests (fail → block commit)
- Optional MCP router as fallback for providers not registered in ZCode
