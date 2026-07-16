# 维度 2：学术与评估方法论

> 诚实标注：darwin-skill 9 维 rubric 为本地一手实证（开源自查）；SkillLens/SkillOpt 论文经 2026-06-26 curl 核实真实（详见 skill-optimizer/references/sources.md）。

## 来源清单

| # | 来源 | URL/路径 | 可信度 |
|---|------|---------|--------|
| A | darwin-skill SKILL.md（9 维 rubric 本地实证） | ~/.claude/skills/darwin-skill/SKILL.md | 一手（开源自查） |
| B | Anthropic best-practices eval 章节 | 见 01 号文件 | 一手官方 |
| C | skill-creator plugin（agentskills.io eval 格式） | https://agentskills.io | 官方生态 |

## A. darwin-skill 9 维 rubric（本地一手实证）

darwin-skill v2.0 是自主 skill 优化器，其 9 维 rubric 经多轮实战（huashu-gpt-image +10.85 / huashu-weread-advisor +14.9 / claude-design +16.5）。结构：

### 结构维度（59 分）

| 维度 | 分 | 核心问题 |
|------|----|---------|
| dim1 frontmatter | ~7 | name/description/触发词是否合规且高发现率 |
| dim2 工作流清晰度 | ~10 | 步骤是否可顺序执行，有无路由判断 |
| dim3 失败模式编码 | ~10 | 异常路径是否编码（if-then fallback） |
| dim4 检查点设计 | ~8 | 有无人审/自动 gate（视觉标记 🔴/🛑） |
| dim5 可执行具体性 | ~12 | 指令是否具体到可操作，禁含糊 |
| dim6 资源整合度 | ~8 | reference 文件引用是否一层深、按需加载 |
| dim7（扩展） | ~4 | runtime 中立性 / badge |

### 效果维度（35 分）

| 维度 | 分 | 核心 |
|------|----|------|
| dim8 整体架构 | ~15 | 全局一致性、抽象层次 |
| dim9 实测表现 | ~20 | 干跑测试 prompt 的实际效果 |

### dim9 反例黑名单

darwin-skill 设有「反例黑名单成章」——把常见误用模式显式列为反例（边界节正向化）。这是比单纯正例更强的约束。

## 实战 high-leverage 操作（HL-1~4，有数据）

来自 darwin-skill references/skilllens-evidence.md「HL 实战案例」节，经多 skill 验证：

- **HL-1（dim4）显性视觉标记是杠杆**：加 🔴 CHECKPOINT / 🛑 STOP，靠「必须」措辞不够——LLM 解析时扫描视觉标记。4 行改动撬动 dim4 +3 分。
- **HL-2（dim3）if-then 三段式 fallback 表**：「症状/解法」两列升级为「触发条件 / 一线修复 / 仍失败兜底」三段式。失败模式编码维度的落地。
- **HL-3（Phase 2 诊断）维度相关簇**：dim2/3/4 相关簇——修 dim3 时 dim2 常跟涨。「找最低维度」时同时看相关簇短板。
- **HL-4（Phase 2 退出）触顶 break**：连续 2 轮 Δ<2 分 → break。+0.15 是停手信号不是继续信号；硬凑 MAX_ROUNDS 引入 over-engineering。

## 核心可迁移方法论（去伪存真后）

darwin-skill 引用的具体论文数字（46.4%→73.8%）经 2026-06-26 curl 核实（SkillLens arXiv 2605.23899），但为 darwin 自引非独立复现。方法论内核：

1. **多维度结构化 rubric 优于整体打分**：把「skill 质量」拆成可独立诊断的维度，每维度单独评分找最弱项。这比 LLM 整体打 0-100 分更可重复。
2. **反例黑名单 > 正例清单**：显式列出禁做的模式，比罗列「应该怎样」更能约束 LLM。
3. **validation-gated 迭代**：每轮改动必须通过 baseline 对比才保留（keep），否则 revert。git 棘轮机制。
4. **独立 judge agent**：优化 agent 与评分 agent 分离，避免自评偏差。
5. **触顶即停**：明确停止条件（Δ<阈值连续 N 轮），防过度优化。

这些方法论与 Anthropic 官方 eval-driven 开发（维度 1）完全一致，可交叉验证。

## B. Anthropic eval 方法论（官方一手）

来自 best-practices（见 01 号）：

- **先 eval 后文档**：确保解决真实问题。
- **Claude A/B 协作循环**：A 设计/精炼，B 实测，观察回传。
- **观察导航路径**：意外读取顺序 / 漏跟引用 / 重复读 / 从不访问 → 结构迭代信号。
- **跨模型测试**：Haiku/Sonnet/Opus 取指令交集。

## C. skill-creator 自动化评估

来自维度 1 的 skill-creator plugin：
- test case 存 `evals/evals.json`
- 子代理隔离跑（clean context）
- grading.json + benchmark.json（with vs without skill）
- 版本盲测 A/B
- description 调优（should-trigger / should-not-trigger 命中率）

## 产物框架应用点

本维度定义产物的：
- **质量自检 rubric**（多维度而非整体，含反例黑名单）
- **迭代流程**（validation-gated，触顶即停）
- **eval 集成**（指向 skill-creator plugin）
- **诚实标注原则**（无法核实的引用不纳入，宁可降分也不编造——与 nuwa「诚实边界」精神一致）
