# ADR 0001 · 调度器 = main (递归保护)

- 状态: Accepted (2026-06-29)
- 分支: C (subtask 动态 DAG 调度)
- 相关 commit: 050c00fb

## 背景 (Context)

subtask 动态 DAG 调度 (自动冲突检测 + 并发上限 2 + 完成即派) 需要一个调度器: 读各 subtask 资源声明 → 算冲突 → 建 DAG → 动态派发 → 收态 → 转 check。

候选调度器:
1. **main session** (协调者)
2. **trellis-implement agent** (执行器)

早期文档 (spec-injection / orchestrate SKILL) 写 "trellis-implement 派 subagent 执行各 subtask", 隐含 trellis-implement 作调度器。

## 决策 (Decision)

**main 是唯一 subtask 调度器**。trellis-implement **纯执行**, 不调度不递归。

调度链: main 算冲突 (写盘 glob 相交 + 执行作用域相交 + 显式依赖) → 建 DAG → 动态派 trellis-implement (并发≤2, 完成即派下一个, 不空等) → 收 notification 更新态 → 全 done 转 trellis-check。

## 证据

本会话实验验证 trellis-implement **无法作调度器**:
- 工具集仅 `Read / Write / Edit / Bash` (+ exa MCP), **无 Agent / Task 工具**
- Recursion Guard: 物理上不能派 subagent, 也不能递归派 trellis-implement / trellis-check
- 平台约束: 只有 main session 能派 Trellis implement/check agents

旧文档 "trellis-implement 派 subagent" 是事实错误, 已全量修正。

## 后果 (Consequences)

- ✅ 调度逻辑集中 main (算冲突 / DAG / 派发 / 收态 / 转 check)
- ✅ trellis-implement 单一职责 (执行 1 subtask + 自验)
- ✅ 每 subtask 文件声明 `write-files` + `exec-scope` 供 main 冲突判定
- ⚠️ main 须持调度状态 (5 态: ready/blocked/running/done/failed), 不可下沉到脚本
- ⚠️ 调度权依赖 main session 存在 (非脚本可自动化)

## 备选 (Alternatives)

| 方案 | 否决理由 |
| --- | --- |
| trellis-implement 作调度器 | 工具集无 Agent/Task, 物理不可行 (Recursion Guard) |
| 独立调度脚本 | 脚本无法派 Claude agent, 也无法收 notification |
