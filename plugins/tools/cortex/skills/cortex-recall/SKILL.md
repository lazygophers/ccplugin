---
name: cortex-recall
description: "知识库搜索 + 兜底 + 回填闭环 — 先搜双层 vault (项目级 <repo>/.wiki + 用户级 ~/.cortex/.wiki); 未命中走兜底 (WebSearch → 拿不准问用户); 答案按 scope 归类 (项目级/全局) 自动回填知识库. 触发: 查/搜知识库/recall/想想/记得/这个怎么."
when_to_use: "查知识库/搜 vault/recall/想想/记得/查资料/这个之前怎么做的/有没有记录过"
argument-hint: "[query]"
arguments: "[查询]"
user-invocable: true
---

# cortex-recall

**查询驱动 + 缺则补**: 搜双层 vault → 未命中兜底 (互联网 → 拿不准问用户) → 答案按 scope 归类自动回填知识库. **不写脚本** — 由 main 会话按步骤调 vault 搜索工具 / WebSearch / cortex-extract 回填.

## 流程速查

```
query
 │
 1. 搜 vault (项目级 <repo>/.wiki + 用户级 ~/.cortex/.wiki)
 │   命中 → 返回 (附引用) ✓
 │   未命中 ↓
 2. WebSearch 互联网
 │   拿得准 → 用答案 (标 source URL)
 │   拿不准 ↓
 3. 问用户 → 用答案
 │
 4. 回填: 按 scope 归类 (项目级 / 全局) → 调 cortex-extract/cortex-save 落盘
```

命中 vault 即返回, 不走兜底; 走兜底必回填 (默认落 L3-short).

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 双层搜索范围 + 多级回退 (mcp/rg/grep) + 引用格式 | `references/search.md` |
| 兜底顺序 (WebSearch → 问用户) + "拿不准" 判定 | `references/fallback.md` |
| 回填: scope 归类 + 定级别 + 默认自动写 (含 L0) | `references/writeback.md` |

## 与既有 skill 边界

| skill | 职责 |
| --- | --- |
| cortex-recall (本) | 搜 + 兜底 + 回填 闭环 (查不到主动补) |
| cortex-extract | L4-inbox 内部已收件资料路由分级 |
| cortex-context-digest | 整理当前会话上下文沉淀 |
| cortex-ingest | 外部 repo/website 主动入库 |
| cortex-schema | 路径/级别契约权威 |

recall = "查询驱动 + 缺则补"; extract/digest = "已有资料整理".

依赖: cortex-schema (路径权威) + cortex-extract (回填三轴 + 落盘) + cortex-context-digest (scope 规则).
