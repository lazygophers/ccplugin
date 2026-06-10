# Design — cortex 后台 worker agents

## worker agent 文件 (agents/, 自动发现)

```
agents/
├── cortex.md                    (现有, 前台主协调)
├── cortex-lint-worker.md        background, 只读扫 vault → 违规报告 plan
├── cortex-history-worker.md     background, 扫 ~/.claude/projects → 学习增量 plan
├── cortex-evolve-worker.md      background, 扫 vault 算三轴 → 升降级 plan
├── cortex-extract-worker.md     background, 扫 L4-inbox 算三轴 → 路由 plan
└── cortex-ingest-worker.md      background, gh/WebFetch 抓取 → 入库 plan
```

## worker frontmatter 模板

```yaml
---
name: cortex-lint-worker
description: "[何时委托] cortex vault 合规扫描后台 worker — 被 cortex-lint skill (context:fork) 启动. 跑 7 规则 check, 产出违规报告 plan. 不 ask/不 apply."
tools: Read, Glob, Grep, Bash
model: <见下表>
background: true
---
```

model 选型:
| worker | model | 理由 |
| --- | --- | --- |
| cortex-lint-worker | haiku | 规则匹配, 机械, 省成本 |
| cortex-history-worker | inherit | 提取学习增量需语义判断 |
| cortex-evolve-worker | inherit | 三轴评分需判断 |
| cortex-extract-worker | inherit | 三轴路由需判断 |
| cortex-ingest-worker | inherit | 摘要生成需语义 |

tools: 全部只读+脚本 `Read, Glob, Grep, Bash`。**不含** Agent / AskUserQuestion / Write/Edit (worker 不落盘, 只回 plan)。ingest-worker 需 WebFetch → 加 `WebFetch`。

## worker 正文结构 (≤ 80 行)

```markdown
# cortex-<x>-worker

你是 cortex-<x> 的后台扫描 worker。被 cortex-<x> skill (context:fork) 启动。

## 职责
<扫什么 → 算什么 → 出什么 plan>

## 输入契约
- skill argument: <...>
- 读 vault: <路径> (自包含, 不依赖主会话历史)
- 路径/级别权威: 读 cortex-schema references

## 输出 (返回主会话)
JSON plan: {...}

## 边界 (硬规)
- 只读 + 脚本; 禁 Write/Edit 落盘
- 禁 AskUserQuestion (subagent 不支持) — L0/L1 等需确认项标 `needs_ask: true` 留主会话
- 禁 --apply/--fix — 主会话审 plan 后执行
- 失败: 工具错重试 1 次; 阻塞标 "需要: <问题>" 回主
```

## skill 绑定 (5 SKILL.md frontmatter)

每个加两字段 (不破坏既有):
```yaml
context: fork
agent: cortex-<x>-worker
```

## skill 正文分段

每 skill 正文重构为两段:
```markdown
## 后台扫描段 (worker 执行)
<scan → plan; 由 context:fork 派 cortex-<x>-worker 后台跑>

## 主会话段 (worker 返回 plan 后)
<审 plan → ask (L0/L1 确认) → --apply/--fix 落盘 (调脚本)>
```

注: `context: fork` 把整个 skill body fork 进 worker。若 body 含 ask 会崩。**解法**: skill body 主体是"派 worker 拿 plan",ask/apply 写成"worker 返回后主会话继续"的指令段 — worker 读到 ask 段会识别为"非自己职责"跳过 (靠 worker 边界声明)。更稳妥: skill body 描述以 worker 视角写 scan→plan, 末尾一句 "plan 返回主会话, 由主会话审批+落盘"。

## plugin.json

agents 数组 (现仅 ./agents/cortex.md) → 加 5 worker:
```json
"agents": [
  "./agents/cortex.md",
  "./agents/cortex-lint-worker.md",
  "./agents/cortex-history-worker.md",
  "./agents/cortex-evolve-worker.md",
  "./agents/cortex-extract-worker.md",
  "./agents/cortex-ingest-worker.md"
]
```
(文档说 auto-discover, 但本插件显式列 — 保持一致显式列出)

## 资源边界

| Subtask | 写 | 并行 |
| --- | --- | --- |
| S1 | agents/cortex-*-worker.md (新建 5) | // S2 |
| S2 | 5 skill SKILL.md (frontmatter + 正文段) | // S1 |
| S3 | plugin.json + README + llms.txt | 依赖 S1 |
| S4 | 只读验证 | 收口 |

## 验证

- 5 worker frontmatter: name/description/tools/background:true 齐, tools 无 Agent/Write
- 5 skill: context:fork + agent: cortex-<x>-worker
- plugin.json agents len==6, JSON 合法
- 既有脚本 smoke 全过 (worker 不改脚本逻辑)
- README/llms 提 worker

## Rollback

```bash
git checkout plugins/tools/cortex/{.claude-plugin,README.md,llms.txt} plugins/tools/cortex/skills/cortex-{lint,history-digest,evolve,extract,ingest}/SKILL.md
rm -f plugins/tools/cortex/agents/cortex-*-worker.md
```
