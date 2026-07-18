---
name: skein-research
description: SKEIN 调研数据源路由 (绑定 skein-researcher agent)。planning 阶段做外部资料检索 / 库选型 / 竞品对比 / 现状勘察时使用。分层组合: 项目内代码勘察 + 外部联网检索 (优先 agent-reach, 缺失降级 WebSearch/WebFetch)。
user-invocable: true
model: inherit
effort: medium
---

# skein-research — 调研数据源路由

**绑定 agent `skein-researcher`** (它 frontmatter `skills: skein:skein-research`)。planning 阶段 main 派 skein-researcher 调研时, 数据源按本 skill 分层组合。

> 定位: 只管**从哪取数据、怎么取**; 结论汇总 / 设计裁定仍归 researcher 回传 main (见 skein-researcher 铁律)。

## 数据源分层 (每次调研按需组合, 非全跑)

| 层 | 工具 | 适合 |
| --- | --- | --- |
| **代码勘察** | Read / Grep / Glob / Bash | 现状勘察 / 既有实现 / 依赖版本 / 项目约定 (本地真值, 恒先查) |
| **外部检索** | agent-reach (存在) → 否则 WebSearch/WebFetch | 库选型 / 竞品对比 / 官方文档 / 社区讨论 / 最新版本 |

**顺序**: 先本地代码勘察 (成本低、最相关), 再外部检索补空缺。CLAUDE.md 硬规: 提问前先搜项目。

## 外部检索: agent-reach 优先

**探测门** (外部检索开跑前必做一次):

```bash
command -v agent-reach >/dev/null 2>&1 && echo AVAILABLE || echo FALLBACK
```

- **AVAILABLE** — 纳入 agent-reach 作数据源 (15 平台、多后端, 存在时必用, 不自己发明方案): doctor 体检 / 声明来源 / 重试链 / 多平台并行策略 + 路由对照表 (调研意图 → agent-reach 分类), 详见 [references/agent-reach-routing.md](references/agent-reach-routing.md)。
- **FALLBACK** — 无 agent-reach: 降级 WebSearch/WebFetch, 回传声明覆盖缺口。细节同上 reference。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                              | 一线修复                                         | 仍失败兜底                                                  |
| --------------------------------- | ------------------------------------------------ | ----------------------------------------------------------- |
| agent-reach doctor 报目标平台后端全挂 | 换 agent-reach 内同类其他后端/平台重试            | 仍不可用 → 降级 WebSearch 并声明「该平台数据未覆盖」          |
| 外部检索零结果 (查空)             | 换关键词 / 换平台分类 (search↔dev↔social) 重试   | 仍空 → 回传「已查 X 源均空, 现状可能无先例」, 禁编造填充      |
| 本地勘察与外部结论矛盾            | 以本仓现状为准复核 (版本/约定/接口)              | 无法调和 → 并列两方证据回传 main 裁, 禁单方拍板              |

## ❌ 反例 (命中=调研流程错误)

> 🔒 Iron Law: 提问前先搜项目 — 先本地代码勘察 (Read/Grep), 后外部检索。

- ❌ 探测到 agent-reach 存在却仍手搓 curl / 自造抓取方案 → ✅ 存在必用它。
- ❌ 跳过本地代码勘察直接联网 → ✅ 先 Read/Grep/Glob 本仓现状 (违反「提问前先搜项目」, 外部结论可能与本仓现状矛盾)。
- ❌ 降级后不声明覆盖缺口 → ✅ 回传声明「该平台数据未覆盖」(让 main 不误判「已全网覆盖」)。
- ❌ 在本 skill 里重抄 agent-reach 的平台命令 → ✅ 命令以 agent-reach references 为准 (版本漂移只维护一处)。

## 落盘

调研结论落盘仍走 skein-researcher 的「结论落盘」: `.skein/task/<task-id>/research/<topic-slug>.md`。本 skill 只定数据源, 不改落盘路径。
