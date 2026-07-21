# PRD: skein-skill-agent-slim (A: skill/agent 写法瘦身)

## 来源
skein-trellis-optimize-v2 调研: superpowers-deep-dive.md (P0 维度 2/4)
+ skein-current-state-audit.md (维度 2/3/6: SKILL/agent 体积, 公共铁律重复 14 处, 术语漂移)

## 罗盘 (瘦身必须保的不变量)
- 4 阶段闭环 (plan→exec→check→finish)
- grill 硬门
- 6 字段 dispatch
- Recursion Guard
- 两层 core/recall 记忆
- DAG 双层调度
- worktree 隔离

## 4 子项

### A1. description 只写 when-to-use, 砍 workflow 摘要
**问题**: superpowers 实测 (writing-skills:150-172) — description 含 workflow 摘要让 agent follow description 跳过读 body (实例: "只做 1 轮 review 而非 2 轮")。skein 多数 description 正中此陷阱:
- skein-check: 把"回 planning 重确认→同 task 排队修复→重新 claim→通过才放行"整流程写进 description
- skein-exec: 把"双层 subtask+多 task 级同构调度算法"写进 description
- skein-plan: 把"判新旧+create+brainstorm+grill 硬门"流程枚举写进 description
- skein-memory: 把"core 常驻+recall 召回+sediment 判定门+bootstrap+reconstruct"全写进 description

**改法**: description 只留 = 触发条件 (何时用) + 症状 (什么场景) + 产出物 (产出什么)。workflow/调度算法/判定门细节归 body 或 references。
**目标**: 每个 description ≤ 描述触发+产出, workflow 摘要移走。

### A2. 抽 agent 公共铁律单点
**问题**: 7 agent 各写一遍三条铁律 (Recursion Guard / 无 AskUserQuestion / `需要:` 回传), ~30 行纯重复 (审计维度 3)。
**改法**: 抽到单点 (shared snippet / 一次定义), 各 agent frontmatter 或 body 引用, 只写独有职责。
**待定**: 载体 — shared markdown snippet 被 include? 还是写进某 SKILL 一次定义 agent 引用? (frontmatter 无 include 机制, 需确认 Claude Code 是否支持 skill 间 include)

### A3. 统一 emoji 标签词表
**问题**: skein 现用 🛑+(硬门·STOP) 文字标记, 各 skill 标记不统一。
**改法**: 统一词表 — 🛑 硬门 (STOP, 用户必确认) / ⚠️ 硬规 (违反即失效) / ❌ 反例 (命中=流程错误)。全 skill 一致, 利 agent 扫描识别。
**待确认**: 词表用 emoji 还是纯文字 (CLAUDE.md 已有 🛑 先例, 倾向 emoji)。

### A4. 反例按失败类型编码 (Match the Form)
**问题**: superpowers writing-skills:459-475 "Match the Form to the Failure" — prohibition (禁做 X) 在 shaping failure (输出格式/回传压缩/进度清单) 上**适得其反** (实测 prohibition arm 比 no-guidance control 还差)。skein 反例段多为 prohibition 式。
**改法**:
- **discipline failure** (跳 grill / inline 改源码 / 宣称派 agent 无 tool_use) → 保持 prohibition (❌ 反例)
- **shaping failure** (dispatch 太长 / 回传不压缩 / 进度清单不齐) → 改 **positive recipe** (✅ 输出格式 IS 4列 id/状态/摘要/进度%)
- 补 rationalization table (Excuse|Reality) + Iron Law 单行置顶

## 验收标准
- [ ] A1: 4 个重 description (check/exec/plan/memory) 砍 workflow 摘要, 只留触发+产出; 过质量门 (claude -p 测 agent 仍能正确识别何时触发)
- [ ] A2: 7 agent 公共铁律去重, 单点定义; 各 agent 只写独有职责
- [ ] A3: 全 skill 标签词表统一 (🛑/⚠️/❌)
- [ ] A4: 反例段按失败类型编码, shaping failure 改 positive recipe
- [ ] 全程过质量门 (改 SKILL/agent 必跑 claude -p)
- [ ] 罗盘不变量零破坏

## 风险
- A2 载体待确认 (skill 间 include 机制)
- A1 砍太多可能丢关键触发词 → 需质量门验证
- A4 区分 discipline vs shaping failure 需逐反例判定

## 流程铁律
所有修复方案逐个与用户确认后才动手 (用户硬规)。
