---
description: SKEIN 体检 — 纯脚本检测 task/subtask 不符合规范的地方 (非法 status/deps 悬空成环/禁父子/active 缺 subtask·worktree/索引不一致/sid 重复/验收越界), 有错 exit 1
---

# skein-doctor

跑纯脚本体检, 定位 task/subtask 违反 SKEIN 规范之处。**判断全在脚本, AI 只解读输出并给修复建议**。

## 步骤

1. 跑体检:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py doctor
   ```
2. 读脚本输出 (`✗`=错误 exit 1 / `⚠`=警告不阻断 / `✅ 无违规`)。
3. **有 `✗`** → 逐条向用户说明违规项 + 建议修法 (改哪个 task.json / 补哪个字段 / 用哪个 `skein.py subtask` 命令), **禁自动改** `.skein/` (违规多为流程错误, 需用户确认). 涉及顶层索引与 per-task 不一致 → 建议重跑对应生命周期命令重建。
4. **仅 `⚠`** → 列出提醒, 不阻断。
5. **`✅ 无违规`** → 一句话报告通过。

## 脚本查什么 (规范不变量)

- **task**: id 非 kebab-case / 非法 status / deps 自引用·悬空·成环 / **出现父子字段** (task 级仅 deps DAG, 禁父子) / active 无 subtask·缺 started·worktree 失效 / done 缺 finished / 顶层 task.json 索引 status ≠ per-task 真值 / active 数超 max_active。
- **subtask**: sid 重复 / 非法 status / depends_on 自引用·悬空 (须同 task 内 sid)·成环 / 验收done 序号越界 / done 但验收未全过 (⚠)。

$ARGUMENTS
