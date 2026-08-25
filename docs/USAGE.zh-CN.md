# 使用指南

ZCode Planner Pipeline 的安装、模型配置、AI 读取机制与排障。

## 1. 你得到什么

- **命令**（在 ZCode 输入框运行）：
  - `/plan-z <feature>` — 规划：探索仓库并写出计划契约
  - `/dev-z <feature>` — 执行：实现任务、跑测试；绝不自动提交
  - `/review-z <feature>` — 评审：对照验收标准检查 diff
  - `/pipeline-z <feature>` — 一条命令串联三个阶段，在每个检查点停下
- **子代理**（v2）：`coder-z` 和 `reviewer-z`——通过 `model` 字段钉死便宜模型，由主 AI 经 Agent 工具自动启动。
- **配置**：`pipeline.json`——唯一的模型路由契约。

`-z` 后缀是有意为之：避免与 ZCode 内置斜杠命令重名冲突。

## 2. 环境要求

- 支持斜杠命令和子代理的 ZCode
- 项目必须是 git 仓库（流程依赖 `git diff`；提交一律手动）
- 在 ZCode 中注册一个模型提供商，至少有两个可用模型——例如自定义 OpenAI 兼容端点：
  - ZCode 中的提供商名：`基元` | Base URL：`https://tokenrhythm.studio/v1`
  - 模型：`deepseek-v4-flash-0731`（planner）和 `deepseek-v4-flash`（coder/reviewer）

## 3. 安装

### 方式 A — 项目级（随仓库版本化）

```bash
cp -r .zcode /path/to/your-project/
```

子代理是用户级的；要启用自动模型路由（`driver: subagent`）还需执行：

```bash
mkdir -p ~/.zcode/agents
cp .zcode/agents/*.md ~/.zcode/agents/
```

### 方式 B — 用户级（任何项目可用）

```bash
mkdir -p ~/.zcode/commands ~/.zcode/agents
cp .zcode/commands/*.md ~/.zcode/commands/
cp .zcode/pipeline.json ~/.zcode/pipeline.json
cp .zcode/agents/*.md ~/.zcode/agents/
```

### 验证安装

1. **新建会话**——命令和子代理在会话启动时加载，不热更新。
2. `/` 菜单里能看到 `plan-z`、`dev-z`、`review-z`、`pipeline-z`。
3. 设置 → 子智能体里能看到 `coder-z` 和 `reviewer-z`。

## 4. 配置模型

### 4.1 在 ZCode 里注册提供商

设置 → 模型/提供商 → 添加：

- 提供商名：如 `基元`
- Base URL：如 `https://tokenrhythm.studio/v1`
- API Key：你的密钥

之后该提供商的模型（`deepseek-v4-flash-0731`、`deepseek-v4-flash` 等）会出现在模型选择器里。

### 4.2 `pipeline.json` — 唯一的路由配置

```json
"roles": {
  "planner":  { "provider": "基元", "model": "deepseek-v4-flash-0731" },
  "coder":    { "provider": "基元", "model": "deepseek-v4-flash" },
  "reviewer": { "provider": "基元", "model": "deepseek-v4-flash" }
}
```

- `provider` 必须和 ZCode 里配置的提供商名一致；`model` 必须和模型选择器里显示的 id 一致。
- `execution.driver`：固定为 `subagent`——coder/reviewer 由钉死模型的子代理执行，没有其他模式。
- `execution.max_task_retries`：任务测试失败时 coder 最多重试几次，超过则标记 `failed`。

### 4.3 子代理的 `model` 字段（保持同步）

`~/.zcode/agents/coder-z.md` 和 `~/.zcode/agents/reviewer-z.md` 各有 `model:` 字段，必须与 `roles.coder` / `roles.reviewer` 一致——配置是契约，子代理文件是机制。

## 5. AI 如何读取你的配置

- **命令**：ZCode 依次扫描 `~/.zcode/commands/` 和项目 `.zcode/commands/`（同名先到先得）。命令是带 YAML frontmatter（`description`、`argument-hint`）的 markdown 文件。**frontmatter 值必须 YAML 安全**——值里出现"冒号+空格"会导致解析失败、命令被静默丢弃。
- **配置**：命令正文指示 AI 读取 `pipeline.json`——先项目 `.zcode/pipeline.json`，没有则回退 `~/.zcode/pipeline.json`。
- **子代理**：从 `~/.zcode/agents/<name>.md` 加载；主 AI 经 Agent 工具启动它们，上下文独立——只传入 task 切片和相关文件路径，这正是让便宜模型上下文（和成本）保持小的关键。

## 6. 跑一个功能

1. 把会话模型切到 **planner 模型**（`roles.planner`）——每个功能周期只需一次。
2. `/plan-z <feature>` — 读仓库、写 `.plan/<feature>/`（`plan.md`、`tasks.json`、`status.json`），然后**停住**等你确认。
3. `/dev-z <feature>` — 按依赖顺序执行 `tasks.json`：每个任务由 `coder-z` 实现、跑 `verify`（必须通过）、留在工作区不提交。绝不自动 commit / push / merge。
4. `/review-z <feature>` — 只读的 `reviewer-z` 对照验收标准和改动范围检查 diff，结论写进 `status.json`（`review: pass|fail` + `review_note`）。有 fail 就重跑 `/dev-z <feature>`——评审意见就是修复说明书。
5. 你自己审阅 diff 后，手动 commit 和 push——流程绝不自动提交。

或者直接 `/pipeline-z <feature>` 跑完整循环（带检查点）。

## 7. 排障

| 症状 | 可能原因 | 解决 |
|---|---|---|
| `/` 菜单里没有命令 | frontmatter YAML 错误（如 `description` 值里有"冒号+空格"） | 值保持 YAML 安全（参考本仓库命令文件） |
| `/` 菜单里没有命令 | 文件不在扫描根目录 | 必须放在 `<项目>/.zcode/commands/*.md` |
| `/` 菜单里没有命令 | 会话在文件创建前就启动了 | 新建会话 |
| 子代理不显示 | 会话在安装前就启动了 | 新建会话 |
| 运行时报"模型不存在" | 提供商未注册 / id 不匹配 | 在设置里注册提供商；用模型选择器里的确切 id |

## 8. 以后换模型

1. 改 `pipeline.json` → `roles.<角色>.model`。
2. 同步对应的子代理 `model` 字段（`coder-z.md` / `reviewer-z.md`）。
3. 在会话里选新模型。

其余都不用动——契约（`tasks.json`）和命令保持不变。
