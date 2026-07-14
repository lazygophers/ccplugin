---
name: skein-research
description: SKEIN 调研数据源路由 (绑定 skein-researcher agent)。planning 阶段做外部资料检索 / 库选型 / 竞品对比 / 现状勘察时使用 — 分层组合数据源: 项目内代码勘察 (Read/Grep/Glob) + 外部联网检索。外部检索优先探测 agent-reach (互联网能力路由器, 15 平台多后端): 存在则纳入数据源 (小红书/Twitter/B站/Reddit/GitHub/YouTube/Exa 等多平台并行), 缺失则降级 WebSearch/WebFetch。参考 agent-reach 实现, 不重造。
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

### AVAILABLE — 纳入 agent-reach 作数据源

agent-reach 是互联网能力路由器 (15 平台、多后端), **存在时必须用它, 不自己发明方案**。它自带 `SKILL.md` + `references/{search,social,career,dev,web,video}.md` 完整命令, 按其文档路由:

1. **多后端/登录态平台先体检**: `agent-reach doctor --json`, 按各平台 `active_backend` 选命令组。
2. **声明在用什么**: 回传里注明「经 agent-reach 的 X 平台 / Y 后端取得」(承接 researcher「带来源」铁律, 来源写平台+命令)。
3. **失败按 agent-reach references 重试链**, 不瞎猜命令。
4. **全网调研组合多平台并行**: Exa 网页搜索 + GitHub 看实现 + Twitter/Reddit 看讨论 + 小红书/B站看中文场景, 并行收集再汇总。

路由对照 (详见 agent-reach 各 references):

| 调研意图 | agent-reach 分类 |
| --- | --- |
| 网页/代码搜索 (选型、报错、文档) | search |
| GitHub 仓库/实现/issue/PR | dev |
| 社区讨论 (小红书/Twitter/B站/Reddit/V2EX) | social |
| 网页/文章/RSS 精读 | web |
| YouTube/B站/播客字幕转录 | video |

### FALLBACK — 无 agent-reach

降级用 agent 自带 `WebSearch` / `WebFetch`。能力受限 (无登录态平台、无字幕转录), 回传时**注明「agent-reach 不可用, 已降级 WebSearch/WebFetch, X 类数据未覆盖」**, 别假装全网都查过。

## 反例 (不要做)

- ❌ 探测到 agent-reach 存在却仍手搓 curl / 自造抓取方案 — 存在必用它。
- ❌ 跳过本地代码勘察直接联网 — 违反「提问前先搜项目」, 且外部结论可能与本仓现状矛盾。
- ❌ 降级后不声明覆盖缺口 — 让 main 误判「已全网覆盖」。
- ❌ 在本 skill 里重抄 agent-reach 的平台命令 — 命令以 agent-reach references 为准, 版本漂移只维护一处。

## 落盘

调研结论落盘仍走 skein-researcher 的「结论落盘」: `.skein/task/<task-id>/research/<topic-slug>.md`。本 skill 只定数据源, 不改落盘路径。
