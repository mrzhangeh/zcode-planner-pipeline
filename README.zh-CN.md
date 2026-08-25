# ZCode Planner Pipeline（中文说明）

为 [ZCode] 设计的双模型开发工作流：**强（贵）模型负责规划**并产出一份机器可读的契约；**便宜模型按契约逐任务实现**，用测试做硬门禁。

[English](README.md)

```
用户需求
    │
    ▼
/plan-z  （强模型）      ──►  .plan/<feature>/  plan.md + tasks.json + status.json
    │                          （停下来等用户确认）
    ▼
/dev-z   （便宜模型）    ──►  逐任务：实现 → 跑测试 → 提交
    │                          （绝不自动提交或推送）
    ▼
/review-z（便宜模型）    ──►  对照验收标准检查 diff，
    │                          把 review: pass|fail 写进 status.json
    │                          （fail → /dev-z 返工，review_note 就是修复说明书）
    ▼
你最终审阅 → merge
```

## 为什么这么设计

- **贵的 token 只花一次**：用在架构推理（planner）上，而不是每次改代码都烧。
- **便宜的模型做大量廉价迭代**：编码、修错、重跑测试。
- 机器可读的契约（`tasks.json`）+ 测试门禁，才是让弱模型可靠的关键。

完整设计见 [docs/FLOW.md](docs/FLOW.md)，模型选择与切换见 [docs/MODELS.md](docs/MODELS.md)，v2 规划见 [docs/ROADMAP.md](docs/ROADMAP.md)，安装与使用教程见 [docs/USAGE.zh-CN.md](docs/USAGE.zh-CN.md)（含排障）。

## 为什么命令带 `-z` 后缀

命令命名为 `/plan-z`、`/dev-z`、`/review-z`、`/pipeline-z`，避免与 CLI 内置命令冲突——`-z` 后缀命名空间专属于本工作流。

## 环境要求

- 支持斜杠命令的 [ZCode]
- 项目必须是 git 仓库（流程依赖 `git diff`；提交一律手动）
- 两个模型端点：强规划模型 + 便宜编码模型（例如走 [OpenRouter]）

## 安装

二选一：

**方式 A — 项目级**（推荐：随仓库版本化，团队可共享）

```bash
# 在本仓库目录下执行，拷进你的项目根目录
cp -r .zcode /path/to/your-project/
```

> 注意：子代理（`coder-z`、`reviewer-z`）是用户级的——要启用自动模型路由（`driver: subagent`），还需按方式 B 最后一步把 `.zcode/agents/*.md` 拷到 `~/.zcode/agents/`。

**方式 B — 用户级**（打开任何项目都能用）

```bash
mkdir -p ~/.zcode/commands ~/.zcode/agents
cp .zcode/commands/*.md ~/.zcode/commands/
cp .zcode/pipeline.json ~/.zcode/pipeline.json
cp .zcode/agents/*.md ~/.zcode/agents/   # v2：钉死模型的 coder/reviewer 子代理
```

## 配置模型

`pipeline.json` 是角色 → 模型的唯一配置点——以后换更强更便宜的模型，只改这一个文件：

```json
"roles": {
  "planner":  { "provider": "openrouter", "model": "openai/gpt-5.6-luna" },
  "coder":    { "provider": "openrouter", "model": "deepseek/deepseek-v4-flash-0731" },
  "reviewer": { "provider": "openrouter", "model": "deepseek/deepseek-v4-flash-0731" }
}
```

命令读取顺序：项目 `.zcode/pipeline.json` → 没有则回退 `~/.zcode/pipeline.json`。

## 使用

你只需选**一次**会话模型——planner 模型（`roles.planner`）；coder 和 reviewer 由钉死模型的子代理自动执行。

1. 把会话模型切到 **planner 模型**（`roles.planner`）。
2. 运行 `/plan-z <feature>`。它探索仓库并写出 `.plan/<feature>/`（`plan.md`、`tasks.json`、`status.json`），然后**停住**——实现前先审阅计划。
3. 运行 `/dev-z <feature>`。它按依赖顺序执行 `tasks.json`：每个任务由 `coder-z` 子代理（钉死便宜模型）实现 → 跑该任务的测试 → 更新 status.json → 输出摘要。绝不自动提交或推送。
4. 运行 `/review-z <feature>`（可选但推荐）。只读的 `reviewer-z` 子代理对照验收标准和改动范围检查 diff，把 `review: pass|fail` + `review_note` 写进 status.json。有 fail 就重跑 `/dev-z <feature>`——评审意见就是修复说明书。
5. 你自己审阅 diff 后，手动 commit 和 push——流程绝不自动提交。

**一条命令跑全程：** 运行 `/pipeline-z <feature>` 串联三个阶段——它会在每个检查点停下，绝不自动 merge。

`tasks.json` 的 schema 见 [docs/CONTRACT.md](docs/CONTRACT.md)，完整示例见 [examples/payment](examples/payment/)。

## License

MIT — 见 [LICENSE](LICENSE)。

[ZCode]: https://github.com/zcode
[OpenRouter]: https://openrouter.ai
