---
updated: 2026-06-09
rewrite-version: 1
authored-by: trellisx-spec
mode: optimize
---

# Thinking Guides Index

何时被读: sub-agent dispatch 前加载上下文时; main 在 Phase 2.1 实现前
谁读: trellis-implement sub-agent; main agent
不遵守的代价: 重复代码 / 跨层耦合泄漏, 后续改动连锁失败

---

## 可用指南

| 指南 | 触发条件 | 验证 |
| --- | --- | --- |
| [Code Reuse](./code-reuse-thinking-guide.md) | 写新函数 / 新建文件前 | `grep -r '<语义词>' src/ packages/` 命中 ≥ 1 → 必须复用 |
| [Cross-Layer](./cross-layer-thinking-guide.md) | 改动 ≥ 2 层 (e.g. API + DB) | 契约边界文档必须存在, 缺一不改 |
| [trellisx worktree](./trellisx-worktree.md) | 实施 trellis task (worktree / subtask 隔离) | 源码改动落 worktree 内, 主工作区干净 |
| [trellisx skill 拆分](./trellisx-skill-split.md) | 拆分 / 重构已有 trellisx skill | 共享逻辑单一真值源 (参数化入口开关), 保名保交叉引用 |

---

## 强制加载触发器

以下场景 MUST 读对应指南后再开始编码:

- [ ] 写新函数 / 新建文件 → [Code Reuse](./code-reuse-thinking-guide.md)
- [ ] 改动涉及 ≥ 2 层 → [Cross-Layer](./cross-layer-thinking-guide.md)
- [ ] 发现同语义代码 ≥ 3 处 → [Code Reuse](./code-reuse-thinking-guide.md) 并抽取
- [ ] 批量修改同名 / 同语义字段 → [Code Reuse](./code-reuse-thinking-guide.md) 确认无遗漏

---

## Pre-Modification Rule

改任何值前 MUST 先搜:

```bash
grep -r "value_to_change" .
```

未搜先改 = 违反 spec。
