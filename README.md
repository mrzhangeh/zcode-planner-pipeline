# ZCode Planner Pipeline

A two-model development workflow for [ZCode]: a **strong (expensive) model plans** and writes a machine-readable contract; a **cheap model implements** it task by task, gated by tests.

[简体中文](README.zh-CN.md)

```
User request
    │
    ▼
/plan-z  (strong model)   ──►  .plan/<feature>/  plan.md + tasks.json + status.json
    │                          (stops for your confirmation)
    ▼
/dev-z   (cheap model)    ──►  for each task: implement → run tests → update status.json
    │                          (never commits or pushes automatically)
    ▼
/review-z (cheap model)   ──►  checks the diff against the acceptance criteria,
    │                          writes review: pass|fail into status.json
    │                          (fail → /dev-z reworks, review_note is the fix spec)
    ▼
you review → merge
```

## Why

- **Spend expensive tokens once**, on reasoning and architecture (the planner), instead of on every edit attempt.
- **Let a cheap model do the cheap iterations** (coding, fixing, re-running tests).
- The machine-readable contract (`tasks.json`) plus a test gate are what make a weak model reliable.

See [docs/FLOW.md](docs/FLOW.md) for the full design, [docs/MODELS.md](docs/MODELS.md) for choosing and switching models, [docs/ROADMAP.md](docs/ROADMAP.md) for the v2 plans, and [docs/USAGE.md](docs/USAGE.md) for step-by-step setup and troubleshooting.

## Why the `-z` suffix

The commands are named `/plan-z`, `/dev-z`, `/review-z`, `/pipeline-z` so they never collide with built-in CLI commands — the `-z` suffix space is reserved for this workflow.

## Requirements

- [ZCode] with slash-command support
- A git repository in your project (the flow relies on `git diff`; commits are always manual)
- Two model endpoints: a strong planner and a cheap coder (e.g. via [OpenRouter])

## Install

Pick one:

**Option A — per project** (recommended: versioned with your repo, shareable with a team)

```bash
# from this repo, into your project root
cp -r .zcode /path/to/your-project/
```

> Note: subagents (`coder-z`, `reviewer-z`) are user-level — to enable automatic model routing (`driver: subagent`) also copy `.zcode/agents/*.md` to `~/.zcode/agents/` (Option B, last step).

**Option B — user scope** (available in every project you open)

```bash
mkdir -p ~/.zcode/commands ~/.zcode/agents
cp .zcode/commands/*.md ~/.zcode/commands/
cp .zcode/pipeline.json ~/.zcode/pipeline.json
cp .zcode/agents/*.md ~/.zcode/agents/   # v2: pinned coder/reviewer subagents (needed for automatic model routing)
```

## Configure models

`pipeline.json` is the single place that maps roles to models — switch to a newer/cheaper model by editing one file:

```json
"roles": {
  "planner":  { "provider": "openrouter", "model": "openai/gpt-5.6-luna" },
  "coder":    { "provider": "openrouter", "model": "deepseek/deepseek-v4-flash-0731" },
  "reviewer": { "provider": "openrouter", "model": "deepseek/deepseek-v4-flash-0731" }
}
```

The commands read `.zcode/pipeline.json` inside your project, falling back to `~/.zcode/pipeline.json` when the project has none.

## Usage

You select the session model **once** — the planner model (`roles.planner`); coder and reviewer run as pinned subagents.

1. Set the session model to the **planner** model (`roles.planner`).
2. Run `/plan-z <feature>`. It explores the repo and writes `.plan/<feature>/` (`plan.md`, `tasks.json`, `status.json`), then **stops** — review the plan before implementing.
3. Run `/dev-z <feature>`. It executes `tasks.json` in dependency order; each task is implemented by the `coder-z` subagent (pinned cheap model), tested, and left uncommitted for your review. It never commits, pushes, or merges automatically.
4. Run `/review-z <feature>` (optional but recommended). The read-only `reviewer-z` subagent checks the diff against the acceptance criteria and scope; verdicts land in status.json as `review: pass|fail` + `review_note`. On any fail, re-run `/dev-z <feature>` — the feedback is the fix spec.
5. Review the diff yourself, then commit and push manually — the pipeline never commits or pushes for you.

**One-shot:** run `/pipeline-z <feature>` to chain the three stages — it stops at each checkpoint and never auto-merges.

See [docs/CONTRACT.md](docs/CONTRACT.md) for the `tasks.json` schema and [examples/payment](examples/payment/) for a worked example.

## License

MIT — see [LICENSE](LICENSE).

[ZCode]: https://github.com/zcode
[OpenRouter]: https://openrouter.ai
