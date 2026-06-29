---
name: skill-optimizer
description: 持续优化 skills 与 subagents 的方法论编排器。诊断 9 维短板→设计 bounded 编辑→validation-gated 验证→保留或回滚。用于优化现有 SKILL.md / agent.md、修触发准确性、补失败模式、收窄误触发、回归检查。系统可自动调用，亦可 /skill-optimizer 手动触发。
when_to_use: 用户说「优化/改改这个 skill」「skill 不触发/误触发」「agent.md 优化」「提升 skill 质量」「skill review」「回归」时；skill 触发不准/失败模式缺失/质量退化时自动调用。
---

# Skill Optimizer — Skill / Agent 持续优化编排器

> 双重触发（系统自动 + `/skill-optimizer` 手动）。基于 darwin-skill 9 维 rubric + Microsoft SkillLens（arXiv 2605.23899）utility-grounded 评估 + SkillOpt（arXiv 2605.23904）validation-gated text-space 优化。完整维度表 / loop 细节 / 论文证据见 `references/`。

## 🔴 硬规（违反即失效）

1. **validation-gated（二层 gate）**：编辑须经 held-out 测试前后对比。**第一层 gross**：9 维 Δ>0（gross 改进信号）；**第二层人审**：分数 fine-grained 不可信（SkillLens 实证 LLM-as-judge 46.4%），Δ>0 不自动 accept，破坏性/触发词变更必须用户确认。禁凭「我觉得改完更好」直接落地。🛑 **已知限制**：非 darwin 环境（无 git ratchet + judge swarm + skill harness 真触发）下，validation gate 几乎必然退化为 dry_run——深度验证 route `/darwin-skill`。
2. **独立评分**：评分 spawn 子 agent，禁同 context 自评自改（乐观偏差）。至少 2 judge 共识或 1 full_test 实测才信。
3. **单变量轮**：每轮只改 1 个维度（或 1 个相关簇），多变量同改无法归因。
4. **ratchet**：只保留有改进的提交；退步自动回滚，git 分支隔离。
5. **人在回路**：破坏性 / 大范围重写 / 触发词变更（影响下游发现逻辑）前 🔴 CHECKPOINT 用户确认。
6. **诚实标注**：dry_run 比例 > 30% → 评估失效警告，分数不可信，必须显式告知用户。

## 何时用 / 边界

| 场景 | 用本 skill | 不用本 skill |
|------|-----------|-------------|
| 优化现有 SKILL.md / agent.md | ✅ | — |
| skill 不触发（false negative） | ✅ 补 description 关键词 | — |
| skill 误触发（false positive） | ✅ 收窄 when_to_use | — |
| 失败模式 / 检查点缺失 | ✅ 补 dim3/dim4 | — |
| 质量回归（改坏了） | ✅ 跑原 eval 场景对比 | — |
| 从零创建新 skill | ❌ | → `/skill-author` |
| 深度自主评分 + 可视化卡片 + 多轮 hill-climbing | ❌ | → `/darwin-skill`（本 skill 可路由） |
| 人物 / 主题视角蒸馏 | ❌ | → `/huashu-nuwa` |

**与 darwin 的分工**：darwin 是重型自动引擎（git ratchet + judge swarm + results.tsv + visual card + MAX_ROUNDS hill-climbing）；本 skill 是**轻量方法论编排器**——诊断 + 单轮 bounded 编辑 + validation gate，需要 darwin 深度评分时 `Skill` 工具路由。

**双重触发语义**：未设 `disable-model-invocation`，故 Claude 在用户提及 skill 质量问题时自动加载；用户亦可 `/skill-optimizer <skill-name>` 显式触发。description + when_to_use 遵守项目底线（< 512 / < 128）。

## 优化流程（5 Phase）

### Phase 1: 诊断（Diagnose）

1. **定位目标**：用户指定 skill / agent 路径，或扫描 `.claude/skills/*/SKILL.md` + `.claude/agents/*.md`。
2. **9 维评分**（速查见 [references/dimensions.md](references/dimensions.md)）：
   - 结构维度（dim1-6）：frontmatter / 工作流 / **失败模式** / **检查点** / 具体性 / 资源
   - 效果维度（dim7-8）：架构 / 实测表现
   - meta 维度（dim9）：反例黑名单
3. **runtime 红灯扫描**（gate 项，先于评分）：
   ```bash
   grep -nE "(在 Claude Code|Claude Code skill|Cursor only|Codex 中|~/\.claude/skills/[a-z]|/plugin install\b)" <target>
   ```
   命中 → P0 先修 runtime drift（详见 darwin `references/runtime-neutrality.md`）。
4. **找短板 + 相关簇**（HL-3）：不只看最低维度，dim2/dim3/dim4 是相关簇——修其一时看另两个是否同步短板。输出诊断表：维度 / 分 / 短板证据（行号引用）/ 建议编辑类型。

> 🔴 **CHECKPOINT**：诊断表展示给用户，确认优化方向 + 优先级后再设计编辑。方向错后续全返工。

### Phase 2: 设计编辑（Design）

**SkillOpt 编辑词表**（bounded add/delete/replace，非自由重写）：

| 操作 | 适用 | 例子 |
|------|------|------|
| **add** | dim3 失败分支缺失 / dim4 检查点缺失 / dim9 反例缺失 | 补 if-then 三段式 fallback 表 |
| **delete** | dim7 冗余 / AI 腔废话 / 时间敏感信息 | 删「说白了/换句话说/综上」 |
| **replace** | dim1 description 太泛 / dim5 软化措辞 / dim2 步骤模糊 | 「建议/可以考虑」→ 具体参数 |

**单变量约束**：一轮只动一个维度（或一个相关簇）。多维度同改 → 归因失效。

**编辑粒度**：优先最小可验证改动（HL-1：4 行 🔴 CHECKPOINT 撬动 dim4 +3）。避免整段重写——除非 Phase 2.5 触发（见下）。

### Phase 2.5: 探索性重写（按需触发）

仅当 dim8 实测表现 ≤ 4 / 10，或 ≥ 3 个维度同时 ≤ 4，单点修补已不够时，整段重写。**必须用户确认**，且重写版仍走 Phase 3 validation gate。

### Phase 3: 验证（Validation Gate）— SkillOpt 核心

1. **设计 held-out 测试**（Phase 1 已备，禁用训练过的 prompt）：
   - 2-3 个 should-trigger（该触发的真实用户表达）
   - 1-2 个 should-not-trigger（不该触发的近似表达，测 false positive）
   - 1 个边缘 case（skill 未覆盖但相关）

   **test prompt 样例集**（本 skill 自测用，他 skill 仿此结构）：
   - should-trigger：「我有个 skill 总不触发，帮我看下哪里问题」「这个 agent.md 改完后行为变了，做下回归」「skill 误触发，每次写代码都弹出来」
   - should-not-trigger：「帮我从零写个新 skill」（→ skill-author）、「蒸馏某人的思维方式」（→ huashu-nuwa）、「跑 10 轮自动优化出可视化卡片」（→ darwin-skill）
   - edge：「帮我看下这个 CLAUDE.md 写得好不好」（CLAUDE.md 非 skill，本 skill 不直接处理，但可给结构建议）

2. **before/after 对比**：spawn 独立子 agent 各跑一遍（带 skill vs 不带 baseline），盲评。
3. **接受准则**（严格提升才保留）：
   - 触发准确性：should-trigger 命中 + should-not-trigger 不命中
   - 输出质量：相比 baseline 有可见提升，无 skill 引入的负面影响（冗余 / 跑偏 / 格式怪）
   - 9 维总分严格高于改进前
   - 🛑 **分数仅作 gross 信号**：9 维分 fine-grained 不可信（见诚实边界），Δ>0 只证明「gross 改进」，**不替代人审**；破坏性/触发词变更必须用户确认，禁凭分数自动 accept
4. **dry_run 降级**：子 agent 不可用时退化为干跑（模拟执行思路），results 标注 `dry_run`；dry_run > 30% → ⚠️ 评估失效警告。

### Phase 4: 应用 / 回滚（Ratchet）

- 通过 gate → 应用编辑，git 提交（分支 `optimize/<skill>-YYYYMMDD`）。
- 🔴 **CHECKPOINT**：merge 到主分支 / 改触发词 / 大范围重写前用户确认（破坏性，下游发现逻辑会变）。
- 未通过 → 回滚，记录失败尝试到 `references/optimization-log.md`（note 列写失败原因：归因不明 / Δ<0 / 触发变差）。
- **触顶即收**（HL-4）：连续 2 轮 Δ < 2 分 → break，进 Phase 5。+0.15 是停手信号非继续信号；硬凑轮数引入 over-engineering。

### Phase 5: 回归 + 汇总

1. **回归测试**：改完跑原 skill 的 eval 场景。evals.json 存在则复用；**绝大多数 skill 无 evals.json**（已知常态），此时现场编 2-3 test prompt 跑 before/after（复用 Phase 3 held-out 集），确认未 break 已有能力。
2. **变更语义标注**：
   - description 触发词变更 = **破坏性**（下游依赖发现逻辑会变），必须显式告知。
   - 仅 body 优化 = 兼容。
3. **汇总报告**：before/after 9 维分 + Δ + 接受/回滚的编辑清单 + judge 共识度 + dry_run 比例。

## agent.md 优化差异

subagent frontmatter ≠ skill frontmatter，诊断时适配：

| 维度 | skill 适配 | subagent 适配 |
|------|-----------|--------------|
| dim1 frontmatter | name/description/when_to_use/disable-model-invocation | name/description/**tools**/model（body=system prompt，禁依赖继承的 CC prompt） |
| dim3 失败模式 | skill 正文 if-then | **body 须要求工具失败显式标注 `[工具失败:原因]`**，否则主对话把错误摘要当有效数据消费 |
| dim4 检查点 | 🔴 视觉标记 | subagent 无用户交互，检查点上移到委派 prompt |
| dim7 架构 | progressive disclosure | tools 字段最小化（不列继承全部）+ 嵌套 ≤ 5 层 |
| 实测 | test prompt 对比 | 委派真实任务，验返回摘要是否含错误混入 |

subagent 工具继承例外（即使列了也不给）：AskUserQuestion / EnterPlanMode / ExitPlanMode / ScheduleWakeup / WaitForMcpServers。Explore/Plan 跳过 CLAUDE.md——若规则必须到达，委派 prompt 重述。

## 失败处理（dim3 三段式）

| 触发条件 | 一线修复 | 仍失败兜底 |
|----------|---------|-----------|
| 改完 skill 行为没变 | 新 session 或重新 `/skill-name` invoke（invoke 后 session 不重读文件） | 见 skill-author Phase 6 |
| validation gate Δ<0 | 回滚，查是否多变量同改 | 降为单变量重试；仍负 → 标记 known limitation |
| judge 分歧大（共识度低） | 加第 3 个 judge 或换 full_test 实测 | 标注「评估不可信」，人审 |
| dry_run > 30% | 补 full_test（spawn 真实子 agent 跑 test prompt） | 评估失效，仅出建议不改盘 |
| 触发词变更致下游 break | 回滚触发词，body 内补关键词 | 新建 skill 而非原地改（破坏性变更） |
| 9 维评分无法归因 | 拆为更小编辑单元 | 路由 `/darwin-skill` 做 MAX_ROUNDS hill-climbing |
| runtime 红灯命中 | P0 先修 runtime drift | 见 darwin runtime-neutrality.md |

## 反模式黑名单

| # | 反模式 | 后果 | 正例 |
|---|--------|------|------|
| 1 | 同 context 自评自改 | 乐观偏差（46.4% 准确率） | spawn 独立子 agent 评分 |
| 2 | 跳过 test prompt 直接评分 | dim8 凭空打分（权重 23%） | Phase 1 强制备 2-3 prompts |
| 3 | 轮内改多个维度 | 归因失效 | 每轮 1 维度（或 1 相关簇） |
| 4 | dry_run 比例高当满分 | 分数虚高，0 revert | 强制 ≥ 1 full_test |
| 5 | 凭「必须」措辞代替视觉标记 | LLM 扫标记优先于语义 | 🔴 / 🛑 标记 |
| 6 | 两列 fallback（症状/解法） | 缺兜底路径 | 三段式（触发/一线/兜底） |
| 7 | 硬凑 MAX_ROUNDS | over-engineering | Δ<2 连续 2 轮即停 |
| 8 | 静默跳过 git/tsv 异常 | ratchet 完整性破坏 | 异常先告知用户 |
| 9 | 单独优化 dim2 不看相关簇 | 已被前轮 dim3 修复推到顶 | HL-3 看相关簇短板 |
| 10 | 改 subagent body 不加错误标注 | 主对话消费错误摘要 | `[工具失败:原因]` 显式标注 |
| 11 | 整段重写不走 gate | 无法归因 + 可能 break | 重写仍走 Phase 3 |
| 12 | runtime 钉死单一平台 | 其他 agent 拒装 | 中立 badge + 措辞 |

## 验证 checklist

### 诊断
- [ ] 9 维评分完成（行号引用证据）
- [ ] runtime 红灯扫描跑过
- [ ] 相关簇短板已识别（HL-3）
- [ ] 🔴 诊断表用户确认

### 编辑
- [ ] SkillOp 词表归类（add/delete/replace）
- [ ] 单变量（1 维度 / 1 相关簇）
- [ ] 最小可验证粒度

### 验证
- [ ] held-out test（should-trigger + should-not-trigger + edge）
- [ ] 独立子 agent 盲评（≥ 2 judge 或 1 full_test）
- [ ] dry_run 比例 < 30%（否则 ⚠️ 失效警告）
- [ ] Δ > 0（严格提升）

### 应用
- [ ] 通过 gate 才应用 + git 提交（分支隔离）
- [ ] 未通过回滚 + 失败日志
- [ ] 连续 2 轮 Δ<2 → break（HL-4）

### 回归
- [ ] 原 eval 场景未 break
- [ ] 触发词变更标注破坏性
- [ ] 汇总报告（before/after/Δ/judge 共识/dry_run 比例）

## 诚实边界（去自夸，真限制）

- **9 维 rubric 源自 darwin-skill 自身测试集**（用自己出的题考自己），非同行评审、无第三方基准。darwin 本机 controlled study（huashu-research 4 类 degradation × 5 judge）证明能识别 gross degradation，但 **fine-grained quality difference 不可信**——重要决策必须人审。
- **SkillLens/SkillOpt 论文经 2026-06-26 curl 核实真实**，但本 skill 的 9 维适配是**转述 darwin 的转述**，非论文原班复现；具体数字（46.4%→73.8%）为 darwin 自引，独立复现缺。
- **dry_run 降级是常见路径**：子 agent 不可用时干跑验证，分数置信度低，本 skill 不声称「无 full_test 也能可靠评分」。
- **覆盖 agent.md 但经验少于 skill**：subagent 优化维度表是设计推导，非 darwin 实战验证（darwin 仅测 skill）。
- 本 skill **不替代 darwin**：需要多轮 hill-climbing + visual card + results.tsv 历史时路由 darwin。
- **validation gate 自指悖论（full_test 实证）**：本 skill 核心主张 validation-gated，但 2026-06-26 首次 dogfooding（2 judge 盲评 + 1 full_test）即在非 darwin 环境 100% dry_run——**核心机制未被自身 full_test 验证过**。subagent fork 不保证重读目标 SKILL.md 做真触发对比，full_test 在普通会话极难达成。诚实定位：**本 skill 是好的诊断 checklist，弱的验证引擎**；深度验证 route darwin。
- **dim8 可重复性为零**：9 维 rubric 不强制 skill 内置 test prompt 集，judge 当场编 prompt 致同一 skill 两次评分 dim8 可差 4 分（dogfooding A=7/B=3 分歧根源）。建议被优化的 skill 内置 test prompt 样例（本 skill L81-83 示范）。
- 不教从零创建（→ skill-author）、不教人物视角蒸馏（→ huashu-nuwa）。

## 调研来源

完整素材见 `references/`：

| 文件 | 维度 | 主源 |
|------|------|------|
| dimensions.md | 9 维 rubric 全表 + HL-1~4 + 相关簇 | darwin-skill 本地 + SkillLens |
| workflow.md | SkillOpt validation-gated loop + git ratchet + judge 独立性 | SkillOpt (arXiv 2605.23904) + darwin |
| sources.md | 3 论文 + darwin 引用 + 实证数据 | arXiv / GitHub（2026-06-26 curl 核实） |
