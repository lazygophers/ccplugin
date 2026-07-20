# skein 流程闭环重设计 — PRD (主入口)

## 目标
- [ ] **漏建 task 根因修复 (最高优先)**: user_prompt 判定从纯 AI 语义改为 hook 脚本预筹 + AI 兜底 (明显豁免/疑似任务脚本启发式预判, 模糊带 AI 判), 判定可靠性提升
- [ ] UserPromptSubmit hook 全量自动判定任务: 每条用户输入注入判定提示 (含脚本预筹结果), 是→走 skein-flow 闭环; 否→放行
- [ ] check 失败语义改"回 planning" (重跑规划确认, 补修复 subtask 后重新 exec), 替换当前"保持进行中补 subtask 回 exec"
- [ ] 记忆异步: sediment 改 fire-and-forget, 不阻塞 finish
- [ ] 查重 haiku agent: 所有 task 规划完成后异步启动, 扫重复 task/subtask 返回清单
- [ ] 核对 5 要求落地: 及时建 task/subtask / 无重复 / task 绑 worktree(config关除外) / 尽量并行 / 记忆异步

## 边界
范围内:
- 新建 UserPromptSubmit hook (`.claude-plugin/hooks.json` + 注入提示脚本/内联)
- `skills/skein-flow/SKILL.md` — 加 hook 判定入口说明 + check 失败回 planning 语义
- `skills/skein-check/SKILL.md` — check 失败→回 planning (非保持进行中)
- `skills/skein-finish/SKILL.md` — sediment 改异步派发 (fire-and-forget)
- 新增 `agents/skein-dedup.md` (haiku 模型) — 查重 agent
- `skills/skein-plan/SKILL.md` — 规划完成后派 skein-dedup 异步查重
- `skills/skein-memory/SKILL.md` — sediment 异步说明

范围外 (非目标):
- 重写 skein 核心 DAG/调度算法 (双层并发已满足"尽量并行")
- 改 task 状态机枚举 (planning 语义用现有 status 表达, 不加新枚举)
- 多子 git worktree 逻辑 (已满足"task 绑 worktree")

## 验收标准
- [ ] UserPromptSubmit hook 注册且生效: 任意输入注入判定提示; claude -p 质量门验证提示可被 AI 正确识别为"判任务→走 skein-flow"
- [ ] check 失败: task 回到 planning 状态语义 (重新 grill/确认), 补修复 subtask 后重 exec — SKILL 文档描述正确
- [ ] sediment 异步: finish 派 skein-memorier 后不等回传直接 finish; SKILL 文档标注 fire-and-forget
- [ ] skein-dedup agent 存在 (haiku), plan 完成异步派发, 回传重复清单
- [ ] 5 要求逐条在 SKILL 文档有对应机制描述
- [ ] claude -p 质量门: 改动的 SKILL 文件提示可被 AI 正确理解

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json (`skein.py subtask list skein-flow-redesign`)
