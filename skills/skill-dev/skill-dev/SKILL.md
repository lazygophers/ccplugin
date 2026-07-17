---
name: skill-dev
description: 创建、维护与持续优化 Claude skills 和 subagents 的方法论框架。写 SKILL.md / 新建 skill / 设计 subagent(agent.md) / 配 frontmatter / 拆 progressive disclosure(流程 A 创建), 或诊断 9 维短板 / 修触发准确性 / 补失败模式 / 收窄误触发 / validation-gated 优化现有 skill(流程 B 优化)时使用。领域/主题视角蒸馏(分维度调研+三重验证)内置流程 A; 9 维评分+validation-gated 爬山+可视化成果卡片内置流程 B。仅手动 /skill-dev 触发。
disable-model-invocation: true
argument-hint: "[create|optimize] <skill/agent 路径>"
arguments: "[create|optimize] <skill/agent 路径>"
---

# Skill Dev — Skill / Agent 创建 · 优化方法论

> meta-skill：教如何**编写与打磨其他 skill 与 subagent**。方法论源自 Anthropic 官方规范 + SkillLens 9 维实证（arXiv 2605.23899）+ SkillOpt validation-gated 优化（arXiv 2605.23904）+ 社区反模式，已完整内化——评分 rubric、爬山门、盲评、成果卡片均自包含，**创建线（流程 A）内置分维度并行调研 + 调研审查门 + 三重验证漏斗 + 量化质量门 + 降级表**，无需外链其他 skill。完整调研素材见 `references/research/01-06.md` 与 `references/`。本 skill 管**功能 / 领域 / 主题视角 skill 与 subagent 的创建（流程 A）到深度优化（流程 B：9 维评分 + validation-gated 爬山 + 可视化成果卡片）全生命周期**（人物角色扮演 DNA / 表达语气不在范围——蒸方法论不蒸人物）。

## 🔴 硬规（违反即失效）

1. **显式触发**：本 skill `disable-model-invocation: true`，仅 `/skill-dev` 手动调用。它是创作/优化工具，不是背景知识，不要改为自动触发。
2. **产物定位**：造功能 / 领域 / 主题视角 skill 或 subagent（创建方法论已内置流程 A）；不蒸人物角色扮演 DNA（表达语气 / 角色人格不在本 skill 范围）。
3. **诚实标注**：禁编造引用。无法核实的来源直接弃用；dry_run 比例 > 30% → 评估失效警告，分数不可信，必须显式告知用户。
4. **独立评分**（优化时）：评分 spawn 子 agent，禁同 context 自评自改（乐观偏差，SkillLens 实证 LLM-as-judge 46.4%）。至少 2 judge 共识或 1 full_test 实测才信。
5. **改任何 SKILL.md / agent.md 后过质量门**（项目 CLAUDE.md 强制）：
   ```bash
   claude -p "<待测内容>" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
   端点抖动（400）时重试循环（见记忆 claude-p-endpoint-flaky）；3 次仍败 → 人工验 + 小步可回滚提交，标「待端点恢复补跑」。

## 路由（先判 create 还是 optimize）

| 输入信号 | 走 |
|---|---|
| 「帮我做个 X skill / 从零写 skill / 加个 subagent / 配 db agent」 | **流程 A · 创建** |
| 「这个 skill 不触发 / 太长 / 改了没生效 / 误触发 / 质量退化 / 做下回归」 | **流程 B · 优化** |
| 「该进 SKILL.md 还是拆 reference / 该用 context:fork 吗 / description 怎么写」 | **流程 A** 相关 Phase（结构/frontmatter 决策） |
| 深度自主评分 + 可视化成果卡片 + 多轮 hill-climbing | **流程 B · 优化**（9 维评分 / validation-gated 爬山 / 成果卡片均内置） |
| 领域/主题视角蒸馏（需分维度调研 + 三重验证提炼） | **流程 A · 创建**（Phase 4 内置调研 swarm + 验证漏斗） |
| 人物角色扮演 DNA（表达语气 / 人格模拟） | 🛑 不在本 skill 范围（蒸方法论不蒸人物） |

> create 与 optimize 边界模糊时（如「这个 skill 不触发，顺便帮我加个功能」）：**先 optimize 诊断，再按诊断结论决定是否走 create 补结构**。

---

## 流程 A · 创建 skill / agent（6 Phase）

### Phase 1: 定位（先答 4 问，再动笔）

1. **skill 还是 subagent？**
   - 可复用 prompt/工作流、主对话跑 → **skill**
   - 产出冗余输出需隔离、需强制工具限制、自包含回摘要 → **subagent**
   - 背景知识（不应命令触发）→ skill + `user-invocable: false`
   - **混合**（主对话交互 + 子任务隔离，如部署需确认+验证+执行）→ skill + `context: fork` + `agent: <type>`
2. **触发方式？** 副作用操作（deploy/commit/send）→ `disable-model-invocation: true`（仅手动）；背景知识 → `user-invocable: false`；一般工作流 → 默认。
3. **内容类型？** Reference（约定/模式）→ 内联常驻；Task（部署/生成步骤）→ 常配 `disable-model-invocation`。
4. **自由度？** 多解皆可 → high（文本指令）；有首选 → medium（参数模板）；操作脆弱 → low（具体脚本禁参数）。

### Phase 2: 骨架

```
my-skill/
├── SKILL.md              # 主指令（≤500 行 / token 意识）
├── references/           # 按需加载细节（只深一层）
└── scripts/              # 可执行脚本（执行而非加载）
```

- 多域按 `references/<domain>.md` 拆；>100 行 reference 顶部放目录。
- **引用只深一层**：禁 a→b→c 嵌套（Claude 对嵌套 `head -100` 预读致信息不全）。

> 🔴 **CHECKPOINT**：骨架定型后展示目录结构给用户确认，再进 frontmatter。骨架方向错，后续全返工。

### Phase 3: frontmatter

**完整 16 字段表 + 调用控制矩阵 + 字符串替换变量见 [references/frontmatter-spec.md](references/frontmatter-spec.md)。** 最常用 5 个：

```yaml
---
name: <lowercase-kebab>           # 默认目录名；≤64 字符，禁 anthropic/claude 保留词，禁 XML 标签
description: <做什么 + 何时用>      # 🔴 项目底线 < 512 字符；第三人称；key use case 前置
disable-model-invocation: true    # 副作用操作必加（仅手动 /name）
allowed-tools: Bash(git *)         # 预授权工具（可选，仅免批准不限制工具池）
paths: packages/api/**             # monorepo 按包触发（可选）
---
```

**description 铁律**（P0 反模式）：第三人称（禁「I can」「You can」）· 含 key terms（用户会说的词）· 同时写「做什么」+「何时用」· **key use case 前置**（🔴 底线 < 512 字符，比官方 1024/1536 截断更严；长列表按「最少 invoke 先丢」裁剪）· 超长触发短语/示例分流 `when_to_use`（底线 < 128）· **收窄「何时用」边界**（太泛会误触发；可发现性 ≠ 触发准确性）。

### Phase 4: 调研 + 内容（落盘即真值 → 审查门 → 三重验证 → 装配）

**先调研再动笔**——功能 / 领域 / 主题视角 skill 的质量上限由调研质量决定（垃圾进垃圾出，这里拦截比 Phase 5 返工便宜）。目标域全是 Claude 已知常识时可跳 4.1-4.2 直接写。

**4.1 分维度并行调研**（域知识不足时）：把目标域拆成互不重叠的维度（官方规范 / 现有实现模式 / 边界与失败模式 / 反模式 / 工具链），每维度一个独立 subagent 并行调研。**接口约定**（swarm 靠 agent 现场编排，无实体脚本）：每个 agent 必须把结果写入 `references/research/0X.md`——**不落盘等于没做**（落盘即真值）；每条标来源 + 可信度（一手 > 二手 > 推测）；区分「文档写的」vs「社区说的」vs「我推断的」；发现矛盾**保留不和稀泥**。**skill 须自包含**：调研文件落 skill 目录内，复制整个目录即可独立用。环境不支持并行 → 见流程 A 降级表。

**4.2 🔴 调研审查门（CHECKPOINT）**：所有维度落盘后暂停，展示调研质量摘要（每维度来源数 / 关键发现 / 矛盾点 / 信息不足维度）给用户。质量 OK 才进合成；某维度不足 → 补调研再继续。此门拦截垃圾输入，成本远低于 Phase 5 返工。

**4.3 三重验证漏斗**（决定什么进 skill body）：对每条候选规则/主张过三关——① **跨域复现**（≥2 个不同场景/任务成立）② **生成预测力**（能据此推断新问题的正确做法）③ **独特性排除常识**（不是所有称职的 Claude 默认就会的）。三重通过 → 核心内容；仅 1-2 重 → 降为次要提示/边注；0 重 → 丢弃（Claude 已知，写了只烧 token）。这是「只加 Claude 不知道的」的可执行版。

**4.4 模板 + 映射表装配**：骨架（Phase 2）为模板，用 section→来源映射表把调研 + 验证结果逐段填入（frontmatter / 工作流 checklist / 失败模式 / 反例黑名单 / 调研来源）。**渐进披露**：SKILL.md 像目录指向按需细节；复杂工作流给可复制 checklist（Claude 逐项打勾）；质量关键操作加 **feedback loop**（validate → fix → repeat），批量/破坏性操作用 **plan-validate-execute**（产 plan → 脚本验证 → 执行 → verify）。每段问「这段值得它的 token 成本吗？」

> 🔴 **CHECKPOINT**：SKILL.md 初稿完成后展示给用户审阅，确认内容方向再进 Phase 5。

### Phase 5: 验证

1. **eval 先行**（写内容前）：跑 3 个代表性任务**不带** skill 记录失败 baseline → 写 ≥3 eval 场景（query + expected_behavior）→ 写完对比。
2. **结构自检**：逐项查「反模式黑名单」。
3. **AI 可发现性质检**：`claude -p "列出所有可用 skill 并说明何时触发" ...`（同硬规 5 命令）。
4. **🛑 触发准确性测试**（关键，区别于可发现性）：用 should-trigger + should-not-trigger prompt 对，测 false positive / false negative。可发现性只测「能列出」，测不到误触发/漏触发——零可见度故障。
5. **反拷问**（可选）：`/grilling` red-team。
6. **量化质量门（收敛判据）**：逐项过量化标准（≥3 eval 场景全过 · 触发无 false positive+false negative · 反例黑名单齐 · 无未核实引用）。不过 → 回对应 Phase 修，**Phase 4→5 迭代上限 2 轮**：2 轮后仍有不过项，在诚实边界标注薄弱维度、交付当前最优版，不无限打磨（宁交诚实标注局限的 60 分，不造看似完美实则编造的 90 分）。
7. **9 维评分/A-B eval**（可选）：需深度评分 + validation-gated 爬山 → 转本 skill **流程 B**（9 维评分 / 爬山门 / 盲评均内置，见下）。

### Phase 6: 维护（改已有 skill）

- **invoke 后 session 不更新**：SKILL.md 渲染为单条消息整 session 常驻，改文件后已 invoke 的 session 仍跑旧版 → 通知用户开新 session 或重新 invoke。
- **改动范围判断**：行为/触发变更（影响 muscle memory + 下游发现逻辑）→ 评估是否新建 skill 而非原地改；仅 body 优化 → 原地改。
- **回归**：改后跑原 eval 场景确认未 break。
- **版本语义**：description 触发词变更 = 破坏性；仅 body 优化 = 兼容。

> 需要 9 维诊断 + validation-gated 深度优化 → 转**流程 B**。

### 流程 A 降级表（环境不足时的退化路径，if-then）

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 环境不支持并行 subagent（Phase 4.1 挂起死等） | 调研降级**串行**：做完一维落盘一维，禁挂起等后台通知 | 单 agent 分轮跑，每轮一维立即落盘 |
| 上下文窗口不足（累积超窗跑不完） | 分 Phase 续跑：每 Phase 落盘 `references/research/`，新会话读文件恢复（调研文件即断点） | 分段会话跑 Phase 1-3 / 4 / 5-6，每段开头先读已落盘文件 |
| 搜索/WebSearch 工具不可用 | 换环境可用等价工具（fetch / 已装信息获取 skill） | 引导用户提供一手素材，转本地素材模式 |
| 信息源匮乏（<10 条可用来源） | Phase 4.2 就降期望，核心规则减量 | 加大诚实边界篇幅，标注推测成分 |
| 单维 agent 超时无有价值结果 | 不等待继续推进，Phase 4.4 标「该维信息不足」 | 诚实边界说明该维薄弱，不强行生成 |

---

## 流程 B · 优化现有 skill / agent（5 Phase · validation-gated）

> 基于 SkillLens utility-grounded 评估 + SkillOpt validation-gated text-space 优化。完整维度表 / loop 细节见 `references/dimensions.md` · `references/workflow.md`。

**🔴 优化硬规**（叠加顶部硬规）：**validation-gated 二层 gate**（第一层 gross：9 维 Δ>0；第二层人审：分数 fine-grained 不可信，破坏性/触发词变更必须用户确认，禁「我觉得更好」直落）· **单变量轮**（每轮只改 1 维度或 1 相关簇）· **ratchet**（只留有改进的提交，退步 `git revert HEAD` 自动回滚，git 分支隔离）· **体积护栏**（改后 SKILL.md > 原 ×1.5 → 拒绝提交，先精简再评，防「加废话凑分」膨胀）· **触顶即收**（连续 2 轮 Δ<2 → break）。🛑 **已知限制**（方法固有，非缺工具）：text-space 优化的 validation gate 依赖真实 skill harness 触发 + 独立 judge swarm，环境不足时退化 dry_run；dry_run > 30% 即评估失效警告，分数不可信须人审——这是**文本空间优化的天花板本身**，无外部 skill 能绕过，只能靠 full_test 比例 + 人审兜底。

### Phase 1: 诊断（Diagnose）

1. **定位**：用户指定路径，或扫 `.claude/skills/*/SKILL.md` + `.claude/agents/*.md`。
2. **9 维评分**（速查见 [references/dimensions.md](references/dimensions.md)）：结构 dim1-6（frontmatter/工作流/**失败模式**/**检查点**/具体性/资源）· 效果 dim7-8（架构/实测）· meta dim9（反例黑名单）。
3. **runtime 红灯扫描**（gate 项，先于评分）：
   ```bash
   grep -nE "(在 Claude Code|Claude Code skill|Cursor only|Codex 中|~/\.claude/skills/[a-z]|/plugin install\b)" <target>
   ```
   命中 → P0 先修 runtime drift：钉死单一平台的措辞（「在 Claude Code 里」「Claude Code skill」）替换为中立表述，badge/安装路径改「Agent Skills Standard + 多 runtime」三层中立结构。例外：frontmatter 触发词、生态内部 skill 名引用、明确标注 runtime-specific 的章节、commit message 不算红灯。
4. **找短板 + 相关簇**（HL-3）：dim2/3/4 是相关簇，修其一时看另两个是否同步短板。输出诊断表：维度/分/短板证据（行号引用）/建议编辑类型。

> 🔴 **CHECKPOINT**：诊断表展示给用户，确认方向 + 优先级后再设计编辑。方向错后续全返工。

### Phase 2: 设计编辑（Design · SkillOpt 编辑词表）

| 操作 | 适用 | 例子 |
|------|------|------|
| **add** | dim3 失败分支缺 / dim4 检查点缺 / dim9 反例缺 | 补 if-then 三段式 fallback 表 |
| **delete** | dim7 冗余 / AI 腔废话 / 时间敏感信息 | 删「说白了/换句话说/综上」 |
| **replace** | dim1 description 太泛 / dim5 软化措辞 / dim2 步骤模糊 | 「建议/可以考虑」→ 具体参数 |

**单变量约束**：一轮只动一维度（或一相关簇），多维同改归因失效。**编辑粒度**：优先最小可验证改动（HL-1：4 行 🔴 CHECKPOINT 撬动 dim4 +3），避免整段重写——除非 Phase 2.5 触发。

### Phase 2.5: 探索性重写（按需）

仅当 dim8 实测 ≤ 4/10，或 ≥3 维同时 ≤ 4，单点修补不够时整段重写。**必须用户确认**，且重写版仍走 Phase 3 gate。

### Phase 3: 验证（Validation Gate · SkillOpt 核心）

1. **held-out 测试**（禁用训练过的 prompt）：2-3 个 should-trigger + 1-2 个 should-not-trigger（测 false positive）+ 1 个边缘 case。
2. **before/after 对比**：spawn 独立子 agent 各跑一遍（带 skill vs baseline），盲评。
3. **接受准则**（严格提升才留）：触发准确性（should-trigger 命中 + should-not-trigger 不命中）· 输出质量相比 baseline 可见提升无负面（冗余/跑偏/格式怪）· 9 维总分严格高于前 · 🛑 **分数仅作 gross 信号**，Δ>0 不替代人审，破坏性/触发词变更必须用户确认。
4. **dry_run 降级**：子 agent 不可用时干跑（模拟执行思路），标注 `dry_run`；> 30% → ⚠️ 评估失效警告。

### Phase 4: 应用 / 回滚（Ratchet）

- 通过 gate → 应用编辑，git 提交（分支 `optimize/<skill>-YYYYMMDD`）。
- 🔴 **CHECKPOINT**：merge 主分支 / 改触发词 / 大范围重写前用户确认（破坏性，下游发现逻辑会变）。
- 未通过 → 回滚（`git revert HEAD` 建反向 commit，禁 `reset --hard` 丢工作树），记失败尝试到 `references/optimization-log.md`（note 写原因：归因不明 / Δ<0 / 触发变差）。
- **体积护栏**：改后 SKILL.md > 原 ×1.5 → 拒绝提交，回改进步骤精简（删冗余/合并重复）再评。触顶后继续硬改常是「加废话让 LLM 觉得更详细」，膨胀 ×1.5 即警示。
- **触顶即收**（HL-4）：连续 2 轮 Δ < 2 分 → break 进 Phase 5。+0.15 是停手信号非继续信号。

### Phase 5: 回归 + 汇总

1. **回归**：改完跑原 eval 场景。**绝大多数 skill 无 evals.json**（常态）→ 现场编 2-3 test prompt 跑 before/after（复用 Phase 3 held-out 集）。
2. **变更语义标注**：description 触发词变更 = **破坏性**（下游发现逻辑变）必须显式告知；仅 body 优化 = 兼容。
3. **汇总**：before/after 9 维分 + Δ + 接受/回滚编辑清单 + judge 共识度 + dry_run 比例。
4. **可视化成果卡片**（可选，展示战绩）：复制 `templates/result-card.html`，填 skill 名 / before-after-Δ 分 / 9 维雷达 / 爬山轮次 / 改进摘要 / 日期，浏览器打开或截图。模板自带 3 风格（swiss/terminal/newspaper，URL hash 切换），无需外部脚本。

---

## subagent 编写要点 + agent.md 优化差异

subagent frontmatter / body 设计点（错误处理约定 / 工具继承例外 / hook 条件验证 / fork vs named）+ 常驻vs按需 / 显式vs隐式触发 / runtime 中立取舍，详见 [references/subagent-authoring.md](references/subagent-authoring.md)。优化 agent.md 时诊断维度适配：

| 维度 | skill 适配 | subagent 适配 |
|------|-----------|--------------|
| dim1 frontmatter | name/description/when_to_use/disable-model-invocation | name/description/**tools**/model（body=system prompt，禁依赖继承的 CC prompt） |
| dim3 失败模式 | 正文 if-then | **body 须要求工具失败显式标注 `[工具失败:原因]`**，否则主对话把错误摘要当有效数据消费 |
| dim4 检查点 | 🔴 视觉标记 | subagent 无用户交互，检查点上移到委派 prompt |
| dim7 架构 | progressive disclosure | tools 字段最小化 + 嵌套 ≤ 5 层 |
| 实测 | test prompt 对比 | 委派真实任务，验返回摘要是否含错误混入 |

subagent 工具继承例外（即使列了也不给）：AskUserQuestion / EnterPlanMode / ExitPlanMode / ScheduleWakeup / WaitForMcpServers。Explore/Plan 跳过 CLAUDE.md——规则必须到达则委派 prompt 重述。

## 共识铁律（全源一致）

| # | 铁律 | 理由 |
|---|------|------|
| 1 | SKILL.md ≤500 行（**token proxy 非精确值**） | CJK/表格/代码块 token 密度高，500 行中文可能 8000+ token；整 session 常驻 |
| 2 | description 第三人称 + key use case 前置 + 做什么+何时用 + **收窄边界防误触发** | 发现入口，🔴 底线 < 512 字符（官方 1024/1536 截断）；超长分流 `when_to_use`（< 128） |
| 3 | 引用只深一层 | 嵌套致 head 预读信息不全 |
| 4 | eval 先于文档 | 解决真实问题而非臆想 |
| 5 | 反例黑名单 > 正例清单 | 反例抓住指令遗漏的失败模式 |
| 6 | 一致术语 + 正斜杠路径 + 无 voodoo 常量 | 跨平台 + 可维护 |
| 7 | token 生命周期意识 | auto-compaction 保留最近 invoke 前 5000 token、合计 25000 token 跨 skill 共享，多 skill session 旧 skill 会被丢——**无错误信息**，最难 debug 的零可见度故障 |

## 失败处理（触发 → 一线修复 → 仍失败兜底）

高频故障内联；创建侧完整 22 条见 [references/anti-patterns.md](references/anti-patterns.md)。

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| skill 写完不触发 | description 太泛/缺 key terms → 加用户会说的词 + 收窄边界 | 跑可发现性质检看是否被列出；未列出查 name/description 含保留词或超 512 截断 |
| 改了 SKILL.md 没生效 | 已 invoke session 常驻旧版 → 开新 session 或重新 invoke | 确认改的是被加载路径（非 references 副本）；`disable-model-invocation` 需 `/name` 重新触发 |
| 多 skill session 本 skill 行为丢失 | 25000 token 跨 skill 共享、旧 invoke 被 compaction 丢 → 精简 SKILL.md、细节拆 references | 缩到 ≤500 行仍丢 → 关键指令上移顶部 5000 token 保留窗 |
| reference 读不全 | 嵌套引用致 `head -100` 截断 → 拍平只深一层 | >100 行 reference 顶部加目录 |
| validation gate Δ<0 | 回滚，查是否多变量同改 | 降单变量重试；仍负 → 标 known limitation |
| judge 分歧大 | 加第 3 judge 或换 full_test 实测 | 标「评估不可信」，人审 |
| dry_run > 30% | 补 full_test（spawn 真实子 agent 跑 test prompt） | 评估失效，仅出建议不改盘 |
| 触发词变更致下游 break | 回滚触发词，body 内补关键词 | 新建 skill 而非原地改（破坏性变更） |
| 结构/触发正确但输出跑偏 | 缺反例黑名单 → 补「不要做 Y」清单 | 跑 `/grilling` red-team 找遗漏失败模式 |
| runtime 红灯命中 | P0 先修 runtime drift（钉死措辞→中立表述） | badge/安装路径改「Agent Skills Standard + 多 runtime」三层中立 |

## 反模式黑名单

创建侧 P0-P3 共 22 条见 [references/anti-patterns.md](references/anti-patterns.md)。优化侧高频反模式：

| # | 反模式 | 后果 | 正例 |
|---|--------|------|------|
| 1 | 同 context 自评自改 | 乐观偏差（46.4% 准确率） | spawn 独立子 agent 评分 |
| 2 | 跳过 test prompt 直接评分 | dim8 凭空打分（权重 23%） | Phase 1 强制备 2-3 prompts |
| 3 | 轮内改多个维度 | 归因失效 | 每轮 1 维度（或 1 相关簇） |
| 4 | dry_run 高当满分 | 分数虚高，0 revert | 强制 ≥ 1 full_test |
| 5 | 凭「必须」代替视觉标记 | LLM 扫标记优先于语义 | 🔴 / 🛑 标记 |
| 6 | 两列 fallback（症状/解法） | 缺兜底路径 | 三段式（触发/一线/兜底） |
| 7 | 硬凑 MAX_ROUNDS | over-engineering | Δ<2 连续 2 轮即停 |
| 8 | 改 subagent body 不加错误标注 | 主对话消费错误摘要 | `[工具失败:原因]` 显式标注 |
| 9 | 整段重写不走 gate | 无法归因 + 可能 break | 重写仍走 Phase 3 |
| 10 | runtime 钉死单一平台 | 其他 agent 拒装 | 中立 badge + 措辞 |

## 验证 checklist

产物发布前逐项查；创建侧完整 5 组见 [references/validation-checklist.md](references/validation-checklist.md)。优化侧：9 维评分完成（行号引用）· runtime 红灯扫描跑过 · 相关簇短板识别 · 🔴 诊断表用户确认 · held-out test（should/should-not/edge）· 独立子 agent 盲评（≥2 judge 或 1 full_test）· dry_run < 30% · Δ>0 严格提升 · 通过 gate 才应用 + git 分支隔离 · 触发词变更标注破坏性 · 汇总报告。

## 诚实边界（去自夸，真限制）

- 针对 Claude 生态（Agent Skills 标准），跨平台迁移需调整触发机制。
- **9 维 rubric / HL-1~4 只在 darwin-skill 自身测试集验证**（用自己出的题考自己），非同行评审、无第三方基准。fine-grained quality difference 不可信——重要决策必须人审。
- **调研来源含 3 个自媒体平台**（Medium/LinkedIn/Substack），无独立第三方复现；反模式频次为主观汇总。
- **validation gate 自指悖论**：核心主张 validation-gated，但真实 skill harness + judge swarm 不足时几乎必然退化 dry_run，核心机制难被自身 full_test 验证。诚实定位：**强的诊断 checklist + validation-gated 纪律，弱的验证引擎**——这是文本空间优化的天花板，靠 full_test 比例 + 人审兜底，无外部工具能绕过。
- **覆盖 agent.md 但经验少于 skill**：subagent 维度表是设计推导，实战样本少于 skill。
- 领域/主题视角蒸馏方法论已内置流程 A（分维度调研 + 三重验证）；深度自主评分 + 可视化成果卡片已内置流程 B，不再外链其他 skill。仅人物角色扮演 DNA（表达语气 / 人格模拟）不在范围。

## 调研来源

| 文件 | 维度 | 主源 |
|------|------|------|
| frontmatter-spec.md | frontmatter 16 字段全表 + 项目底线 | code.claude.com/docs/zh-CN/skills（官方一手） |
| dimensions.md | 9 维 rubric 全表 + HL-1~4 + 相关簇 | darwin-skill 本地 + SkillLens |
| workflow.md | SkillOpt validation-gated loop + git ratchet + judge 独立性 | SkillOpt (arXiv 2605.23904) + darwin |
| subagent-authoring.md / anti-patterns.md / validation-checklist.md | subagent 设计 / 22 反模式 / 发布前 checklist | 官方 + 社区 + darwin dim9 |
| research/01-06.md | 官方规范 / 学术 / 社区 / 跨平台 / 反模式 / 工具链 | platform.claude.com / anthropics/skills / 等 |
| optimizer-sources.md | 3 论文 + darwin 引用 + 实证数据 | arXiv / GitHub（2026-06-26 curl 核实） |

信息源黑名单（永远排除）：知乎、微信公众号、百度百科。
