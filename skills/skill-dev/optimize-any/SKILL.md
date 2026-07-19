---
name: optimize-any
description: 跨任意组件 (plugin/skill/agent/command) 的验证驱动优化循环纪律。评分→单变量改→ratchet (严格更好才留否则回滚)→触顶停。防自评偏差/多维归因失效/膨胀凑分。单 skill 深评交 skill-dev，插件接线交 plugin-dev。仅手动 /optimize-any。
disable-model-invocation: true
argument-hint: "<组件路径>"
arguments: "<组件路径>"
---

# Optimize Any — 跨组件验证驱动优化循环纪律

> 定位：教「优化过程本身」的纪律，不绑定具体组件类型。核心理念 = **验证驱动优化循环**：评分定位短板 → 单变量改 → 改后过质量门 + 改前改后对比 → 严格更好才留（否则 git revert）→ 触顶停。
> 方法论软引用（借鉴非依赖，禁 import 禁调脚本）：darwin-skill（9 维 rubric + validation-gated + ratchet + 触顶停）· huashu-nuwa（独立子 agent 验证防自评偏差）· cangjie-skill（压力测试 / 诱饵边界）· grill-me（逐问确认决策，事实自己查决策等用户）。

## 🔴 硬规（违反即失效）

1. **改过任何组件内容即过质量门**（项目 CLAUDE.md 强制）：
   ```bash
   claude -p "<待测内容>" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
   端点抖动（400）重试循环（见记忆 claude-p-endpoint-flaky）；3 次仍败 → 人工验 + 小步可回滚提交，标「待端点恢复补跑」。
2. **validation-gated 严格更好才留**：改后过质量门 + before/after 对比（触发准确 / 输出质量 / 分数）**任一退步** → `git revert HEAD` 回滚，禁「我觉得更好」直落。分数 fine-grained 不可信，仅 gross 信号（Δ>0）。
3. **单变量轮**：一轮只改一维度（或一紧密相关簇），多维同改归因失效。
4. **独立验证防自评偏差**：评分与对比 spawn 独立子 agent（或独立 session），禁同 context 自评自改（乐观偏差实证 LLM-as-judge ~46% 准确率）。
5. **触顶停**：连续 2 轮 Δ < 2 分 → break，禁硬凑 MAX_ROUNDS（典型症状 = 加废话让 LLM 觉得更详细，膨胀即警示）。
6. **无第三方直接依赖**：评分 rubric / 对比脚本均自包含（见 references/）；软引用 darwin/nuwa/cangjie/grill 是「方法论借鉴源，非依赖」，禁 import 其脚本。

## 路由（先判去重，避免与 skill-dev / plugin-dev 重叠）

| 输入信号 | 走 |
|---|---|
| 优化**单个 skill / agent** 的深度质量（9 维评分 / 修触发 / 补失败模式 / 爬山） | 🛑 `/skill-dev`（流程 B） |
| **插件级** manifest / 组件接线 / hook 健壮性 / marketplace 一致性 | 🛑 `/plugin-dev`（流程 B） |
| 跨任意组件、无明确方向、要套通用「评分→单变量改→验证→ratchet→触顶停」纪律 | ✅ **本 skill** |
| 优化 command / 脚本 / 配置 / 跨组件组合（非单 skill 也非插件接线） | ✅ **本 skill** |

> 边界模糊（如「这个 skill 触发不准顺便帮我优化整个流程」）：先按本 skill 套循环纪律做框架性优化，单 skill 深度评分瓶颈再交 `/skill-dev`。

---

## 通用优化循环（4 阶段）

### Phase 0: 定范围（grill 逐问，决策等用户）

逐问确认**决策项**（事实自己查环境，禁问事实）：
1. 优化目标组件（plugin / skill / agent / command / 组合）+ 路径。
2. 当前痛点（不触发？输出跑偏？太长？误触发？人审觉得退步？）。
3. 验收标准（触发准确 / 输出质量 / 体积上限 / 可观测行为）—— 写成可判定的 before/after 对比项。

> 🔴 **CHECKPOINT**：目标 + 痛点 + 验收标准三项落字给用户点头再动。方向错后续全返工。

### Phase 1: 基线评分（独立评，定位最低维度）

- 按通用维度表打分定位最低维度，**评分 spawn 独立子 agent**（或独立 session）跑，禁同 context 自评。
- 维度表速查 + 打分细则见 [references/scoring-matrix.md](references/scoring-matrix.md)（s2 subtask 创建，含触发准确 / 结构清晰 / 失败模式覆盖 / 具体性 / 冗余度 / 可验证性 等通用维度，按组件类型给适配权重）。
- 输出诊断表：维度 / 分 / 短板证据（行号引用） / 建议编辑类型（add/delete/replace） / 相关簇。

> 🔴 **CHECKPOINT**：诊断表给用户确认方向 + 优先级后再设计编辑。

### Phase 2: 单变量轮（核心 — 改 → 验证 → ratchet → 触顶停）

循环每轮：
1. **改一维度**（或一相关簇）：最小可验证改动，优先小步而非整段重写（除非 ≥3 维同时 ≤4 分触发探索性重写，且必须用户确认）。
2. **过质量门**（硬规 1 命令）+ **before/after 对比**：见 [references/validation-gate.md](references/validation-gate.md)（s3 subtask 创建，含 should-trigger / should-not-trigger / edge case 集 + 独立子 agent 盲评流程 + dry_run 降级）。
3. **严格更好才留**：触发准确不退步 · 输出无负面（冗余 / 跑偏 / 格式怪）· 分数 gross Δ>0 → `git commit`（分支 `optimize/<comp>-YYYYMMDD`）；任一退步 → `git revert HEAD` 回滚（禁 `reset --hard` 丢工作树），记失败尝试原因（归因不明 / Δ<0 / 触发变差）。
4. **触顶停**：连续 2 轮 Δ < 2 → break 进 Phase 3（+0.x 是停手信号非继续）。

### Phase 3: 汇总（分数变化 + 留 / 滚统计 + 触顶信号）

输出：before/after 分数变化表 + 各维度 Δ + 保留 / 回滚编辑清单 + 回滚原因 + judge 共识度 + dry_run 比例 + 触顶轮次。破坏性变更（触发词 / 大范围重写 / merge）显式标注需用户确认。

---

## 失败模式速查（触发 → 一线修复 → 仍失败兜底）

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 质量门 `claude -p` 返 400 / 空 | 重试循环（端点抖动，记忆 claude-p-endpoint-flaky） | 3 次仍败 → 人工审 + 小步可回滚提交，标「待端点恢复补跑」 |
| 自评乐观偏差（改完都说好） | 评分 / 对比 spawn 独立子 agent 或独立 session | judge 分歧大 → 加第 3 judge 或换 full_test 实测，仍分歧标「评估不可信」人审 |
| 多维同改无法归因哪项起效 | 降单变量重试，一轮只改一维度（或一紧密相关簇） | 已混改 → revert 全部，逐维重做建立因果 |
| 触顶后硬凑废话涨分（体积膨胀） | 膨胀护栏：改后 > 原 ×1.5 拒绝提交，先精简再评 | 删冗余 / 合并重复回到 ×1.5 内仍 Δ<2 → 接受触顶停 |
| 独立子 agent 不可用 | 降级 dry_run（模拟执行思路），标注 dry_run | dry_run > 30% → ⚠️ 评估失效警告，仅出建议不改盘，分数不可信须人审 |
| 改后触发词变更致下游 break | 回滚触发词，body 内补关键词 | 新建组件而非原地改（破坏性变更必须用户确认） |

## 反例（命中 = 流程错误）

- 同 context 自评自改（应 spawn 独立子 agent / 独立 session 防乐观偏差）。
- `git reset --hard` 回滚（丢工作树，应 `git revert HEAD` 建反向 commit）。
- 为凑分加冗余 / 扩体积（应膨胀护栏 > 原 ×1.5 拒提交，先精简再评）。
- 跳质量门直接提交改后内容（违反硬规 1）。
- 多维同改一轮（归因失效，应单变量轮）。
- 拿本 skill 去评**单 skill / agent 深度**（交 `/skill-dev`）或查**插件接线**（交 `/plugin-dev`）。
- 凭空猜测不查证 / 决策不让用户拍板（应 grill：事实自己查环境，决策等用户）。

## 资源

- [references/scoring-matrix.md](references/scoring-matrix.md) — 通用维度评分表 + 按组件类型的权重适配（s2 subtask 创建，本 skill Phase 1 指向）。
- [references/validation-gate.md](references/validation-gate.md) — before/after 对比流程 + 独立子 agent 盲评 + dry_run 降级 + held-out 集构造（s3 subtask 创建，本 skill Phase 2 指向）。
- 方法论借鉴源（非依赖，禁 import 禁调脚本）：darwin-skill（rubric + ratchet + 触顶）· huashu-nuwa（独立验证防自评偏差）· cangjie-skill（压力测试 / 诱饵）· grill-me（逐问确认决策）。

## 诚实边界

- 评分 fine-grained 不可信：gross 信号（Δ>0）有效，作粗判可；重要决策（破坏性 / 触发词 / 大范围重写）必须人审，禁「分数涨了就 merge」。
- 无第三方基准：rubric 为 darwin/nuwa/cangjie/grill 共性提炼 + 经验汇总，非同行评审，无独立第三方复现。
- dry_run 多时分数虚高：独立子 agent / 真实 harness 不足时退化 dry_run，> 30% 评估失效，仅出建议不改盘。
