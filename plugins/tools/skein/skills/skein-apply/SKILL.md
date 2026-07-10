---
name: skein-apply
description: 内化注入 (internalize)。首次在某项目启用 SKEIN、或想把 SKEIN 约定落地到本仓时使用 — 初始化 .skein/ 工作区 + .claude/rules 两层记忆库, 让本仓具备 task 闭环与规则记忆能力。一次性 bootstrap。
---

# skein-apply — 内化注入

把 SKEIN 能力**落地到当前仓库**: 建工作区 + 记忆库, 之后本仓即可走 task 闭环 (skein-flow) 与规则记忆 (skein-memory)。一次性动作 (已装则幂等)。

## 流程 (main 同步跑)

1. **建工作区**:
   ```
   python3 <plugin>/scripts/skein.py init      # → .skein/{tasks,archive}, config.json
   python3 <plugin>/scripts/memory.py init      # → .claude/rules/{core,recall}/index.md
   ```
   两条均幂等 (已存在不覆盖)。

2. **确认 .gitignore** (可选): worktree 根 `.worktrees/` 若不想入库则加进 `.gitignore` (task 产物走 merge 回主分支, worktree 本体是临时的)。`.skein/` 与 `.claude/rules/` **应入库** (任务记录 + 规则是团队资产)。

3. **回报已内化**: 列出建好的目录 + 下一步提示 (「本仓已启用 SKEIN, 用 `/skein-go <任务>` 走闭环」)。

## 无 active task 软提示

内化后, 当会话无 active task 却出现「复杂/多步/跨文件」请求时, 应主动提示走 `skein-flow` 建 task (而非 inline 硬做)。此提示是**软建议**, 不强制; 用户坚持 inline 极简请求则尊重 (作用域边界见 skein-flow)。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| 手动 mkdir 建工作区 | 走 skein.py/memory.py init (含 index.md 模板) |
| 把 `.worktrees/` 当资产入库 | 临时目录, 建议 .gitignore; `.skein/`+`.claude/rules/` 才入库 |
| 内化后仍 inline 硬做复杂任务 | 软提示走 skein-flow 建 task |
