# Models — configuring and switching

## The single switch point

`.zcode/pipeline.json` maps roles to models:

```json
"roles": {
  "planner":  { "provider": "基元", "model": "deepseek-v4-flash-0731" },
  "coder":    { "provider": "基元", "model": "deepseek-v4-flash" },
  "reviewer": { "provider": "基元", "model": "deepseek-v4-flash" }
}
```

When a newer/cheaper model appears, you change **one `model` field** — nothing else.

Config resolution order (per command body): project `.zcode/pipeline.json` → `~/.zcode/pipeline.json`.

## How the models are actually invoked

`execution.driver` in `pipeline.json` decides:

- `subagent` (v2, current) — coder/reviewer run as pinned subagents: `~/.zcode/agents/coder-z.md` and `~/.zcode/agents/reviewer-z.md` carry `model: deepseek-v4-flash`. The main session stays on `roles.planner` for the whole cycle and delegates via the Agent tool — one manual model selection per feature.
- `self` (v1) — the session model is the role model; switch manually between stages (planner → `/plan-z`, coder → `/dev-z`, reviewer → `/review-z`).

Keep `roles.coder` / `roles.reviewer` in `pipeline.json` in sync with the subagent `model` fields — the config is the contract, the subagent files are the mechanism.

## Upgrade paths (v2)

- **Subagent driver (chosen — confirmed by ZCode docs)**: subagent files at `~/.zcode/agents/<name>.md` support a `model` frontmatter field (`inherit` or a concrete model) and are launched by the main agent via the Agent tool, with independent context, `tools`/`disallowedTools` and `maxTurns`. This gives automatic model routing plus enforced context isolation. See `docs/ROADMAP.md`.
- **Command-level pinning**: the frontmatter `model` key on commands — a lighter fallback if subagents are not available.
- **MCP driver**: a small MCP proxy that calls the provider API with the task slice — fallback for providers not registered in ZCode, or when enforced task slices are needed without subagents.

## Choosing models

| Role | Wants | Advice |
|---|---|---|
| Planner | strongest reasoning, big context | spend here; it reads the whole request/context once |
| Coder | cheap, good instruction-following, accepts `diff`-style edits | DeepSeek-class models work well as editors (Aider's finding); quality is gated by contract density, not raw strength |
| Reviewer | cheap, reliable at checklist-style checks | never let it replace the test gate |

Provider ids: `model` values are the ids shown in the ZCode model selector (e.g. `deepseek-v4-flash-0731`); `provider` is the provider name as configured in ZCode (e.g. `基元`).
