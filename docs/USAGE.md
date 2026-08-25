# Usage Guide

Setup and daily use of the ZCode Planner Pipeline: install, model configuration, how the AI reads your setup, and troubleshooting.

## 1. What you get

- **Commands** (run in the ZCode input box):
  - `/plan-z <feature>` — the planner: explores the repo and writes the plan contract
  - `/dev-z <feature>` — the executor: implements tasks and runs tests; never commits automatically
  - `/review-z <feature>` — the reviewer: checks diffs against the acceptance criteria
  - `/pipeline-z <feature>` — one-shot chain of the three stages, stopping at each checkpoint
- **Subagents** (v2): `coder-z` and `reviewer-z` — cheap models pinned via their `model` field, launched automatically by the main AI through the Agent tool.
- **Config**: `pipeline.json` — the single model-routing contract.

The `-z` suffix is deliberate: it keeps the command names free of collisions with ZCode's built-in slash commands.

## 2. Requirements

- ZCode with slash-command and subagent support
- A git repository in your project (the flow relies on `git diff`; commits are always manual)
- A model provider registered in ZCode with at least two usable models — e.g. a custom OpenAI-compatible endpoint:
  - Name in ZCode: `基元` | Base URL: `https://tokenrhythm.studio/v1`
  - models: `deepseek-v4-flash-0731` (planner) and `deepseek-v4-flash` (coder/reviewer)

## 3. Install

### Option A — per project (versioned with your repo)

```bash
cp -r .zcode /path/to/your-project/
```

Subagents are user-level; for automatic model routing (`driver: subagent`) also run:

```bash
mkdir -p ~/.zcode/agents
cp .zcode/agents/*.md ~/.zcode/agents/
```

### Option B — user scope (available in every project)

```bash
mkdir -p ~/.zcode/commands ~/.zcode/agents
cp .zcode/commands/*.md ~/.zcode/commands/
cp .zcode/pipeline.json ~/.zcode/pipeline.json
cp .zcode/agents/*.md ~/.zcode/agents/
```

### Verify installation

1. Open a **new session** — commands and subagents are loaded at session start; there is no hot reload.
2. The `/` menu lists `plan-z`, `dev-z`, `review-z`, `pipeline-z`.
3. Settings → Subagents lists `coder-z` and `reviewer-z`.

## 4. Configure models

### 4.1 Register the provider in ZCode

Settings → Models / providers → add a provider:

- Provider name: e.g. `基元`
- Base URL: e.g. `https://tokenrhythm.studio/v1`
- API key: your key

The provider's models then appear in the model selector (`deepseek-v4-flash-0731`, `deepseek-v4-flash`, ...).

### 4.2 `pipeline.json` — the single routing config

```json
"roles": {
  "planner":  { "provider": "基元", "model": "deepseek-v4-flash-0731" },
  "coder":    { "provider": "基元", "model": "deepseek-v4-flash" },
  "reviewer": { "provider": "基元", "model": "deepseek-v4-flash" }
}
```

- `provider` must match the provider name configured in ZCode; `model` must match the id shown in the model selector.
- `execution.driver`: fixed to `subagent` — coder/reviewer run as pinned subagents; there is no other mode.
- `execution.max_task_retries`: how many times the coder retries a failing task before it is marked `failed`.

### 4.3 Subagent `model` fields (keep in sync)

`~/.zcode/agents/coder-z.md` and `~/.zcode/agents/reviewer-z.md` each carry a `model:` field. They must match `roles.coder` / `roles.reviewer` — the config is the contract, the subagent files are the mechanism.

## 5. How the AI reads your setup

- **Commands**: ZCode scans `~/.zcode/commands/` then the project's `.zcode/commands/` (first match wins). A command is a markdown file with a YAML frontmatter (`description`, `argument-hint`). Keep frontmatter values YAML-safe — a `colon-space` inside a value breaks parsing and the command is silently dropped.
- **Config**: the command bodies instruct the AI to read `pipeline.json` — the project's `.zcode/pipeline.json` first, falling back to `~/.zcode/pipeline.json`.
- **Subagents**: loaded from `~/.zcode/agents/<name>.md`; the main AI launches them via the Agent tool with an independent context — only the task slice and the relevant file paths are passed in, which is what keeps the cheap model's context (and cost) small.

## 6. Run a feature

1. Set the session model to the **planner** model (`roles.planner`) — once per feature cycle.
2. `/plan-z <feature>` — reads the repo, writes `.plan/<feature>/` (`plan.md`, `tasks.json`, `status.json`), then **stops** for your confirmation.
3. `/dev-z <feature>` — executes `tasks.json` in dependency order; each task is implemented by `coder-z`, verified (`verify` must pass), and left uncommitted. Never commits, pushes, or merges automatically.
4. `/review-z <feature>` — `reviewer-z` (read-only) checks the diff against acceptance and scope; verdicts land in `status.json` as `review: pass|fail` + `review_note`. On fail, re-run `/dev-z <feature>` — the feedback is the fix spec.
5. Review the diff yourself, then commit and push manually — the pipeline never commits or pushes for you.

Or run `/pipeline-z <feature>` for the whole loop with checkpoints.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Command missing from the `/` menu | frontmatter YAML error (e.g. `colon-space` in `description`) | keep values YAML-safe (see the command files in this repo) |
| Command missing from the `/` menu | files not in a scanned root | must be `<project>/.zcode/commands/*.md` |
| Command missing from the `/` menu | session started before the files existed | open a new session |
| Subagent not visible | session started before install | open a new session |
| "Model not found" when running | provider not registered / id mismatch | register the provider in Settings; use the exact id from the model selector |

## 8. Switching models later

1. Edit `pipeline.json` → `roles.<role>.model`.
2. Sync the matching subagent `model` field (`coder-z.md` / `reviewer-z.md`).
3. Select the new model in the session.

Nothing else changes — the contract (`tasks.json`) and the commands stay the same.
