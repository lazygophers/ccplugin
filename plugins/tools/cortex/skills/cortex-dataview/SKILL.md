---
name: cortex-dataview
description: Obsidian Dataview 查询 skill — 构建 / 修改 / 解释 DQL (LIST/TABLE/TASK/CALENDAR) 与 DataviewJS 块。覆盖 dql 语法 / dataviewjs api / cortex vault 集成模式 / 幂等改写 marker / 8 个 cortex 实用 cookbook。Triggers on "dataview", "DQL", "数据视图", "查询块", "项目仪表盘", "dataviewjs", "dv.pages", "/cortex:dataview".
disable-model-invocation: false
allowed-tools: Read Edit Write
---

# cortex-dataview

帮助 AI 在 cortex vault 内构建 / 修改 / 解释 Obsidian Dataview 块。不替代 cortex-dashboard (DASH marker 三件套), 专注**单个原子 Dataview 块**。

## 三大功能

| 功能 | 触发短语 | 流程 |
|---|---|---|
| **构建** | "做个项目仪表盘 dataview / 写个 query 列出 X" | 先 ask 用 DQL 还是 DataviewJS → 走 references/dql-syntax 或 dataviewjs-api → 生成块 + marker |
| **修改** | "改一下这个 dataview / 加个 score 排序" | references/modify-flow §2 检测 marker → §3 幂等替换 → §5 lint |
| **解释** | "这段 DQL 干啥的 / 报错了帮看看" | references/dql-syntax + integration-patterns 比对语法 / 常见坑 |

## 决策树

```
用户给/要 Dataview 块?
  ├─ 给现有块, 要解释/改       → 检测 marker (modify-flow §2)
  │                              ├─ 有 cortex marker → 安全改写
  │                              └─ 无 marker (用户手写) → AskUserQuestion 是否托管
  ├─ 要新建块
  │   ├─ 纯数据列表/排序/聚合 → DQL (dql-syntax.md + cookbook.md)
  │   └─ 需要 JS 逻辑/异步/  → DataviewJS (dataviewjs-api.md)
  │                              **AUTO_MODE 默认拒绝**, Interactive 必须 AskUserQuestion
  └─ 仅询问语法/概念          → 引 references 段落答
```

## AUTO_MODE 默认

- 只生成 DQL, 不生成 dataviewjs (安全策略, modify-flow §4)
- marker 自动 v1 + sha1[:8] hash
- 写入前跑 `lint_dql` (modify-flow §5)
- 失败不回滚部分写入 (绝不留半成品)

## 与其他 cortex skill 边界

| 重叠场景 | 走哪个 |
|---|---|
| 全局 KPI / 仪表盘三件套 (index/hot/dashboard) | cortex-dashboard |
| canvas + dashboard 视图重渲编排 | cortex-cartographer |
| 单页面里某个 ```dataview 块 | **本 skill** |
| 落档新笔记 | cortex-save |

## References

| 文件 | 内容 | 何时读 |
|---|---|---|
| [references/dql-syntax.md](references/dql-syntax.md) | ~490 行 DQL 完整参考: 4 query type / 6 clause / FROM 4 source / file.* 字段 / 60+ 函数 / 17 gotcha | 写 DQL / 解释 DQL / 调试报错 |
| [references/dataviewjs-api.md](references/dataviewjs-api.md) | ~460 行 dv API: pages/page/query / DataArray ops / render / io / 14 gotcha + 9 cookbook | 用户显式批准写 dataviewjs 时 |
| [references/integration-patterns.md](references/integration-patterns.md) | ~340 行 cortex 集成: inline metadata / 与 Bases 对比 / 与现有 DASH marker 共存 | 决定写哪种块 / 与 vault 现状磨合 |
| [references/modify-flow.md](references/modify-flow.md) | marker 契约 + regex 检测 + 幂等替换 + lint + 安全策略 | **改任何已存在块前必读** |
| [references/cookbook.md](references/cookbook.md) | 8 cortex-vault 实用 query (项目/日记/孤儿/评分 review/L2 promote/活跃/任务) | 用户问"有没有现成的" |

## 不做

- 不真跑 query (Dataview 在 Obsidian 内执行)
- 不替代 cortex-dashboard / cortex-cartographer
- 不默认生成 dataviewjs (安全)
- 不修改用户手写无 marker 块 (除非明确许可)
- 不 git commit
