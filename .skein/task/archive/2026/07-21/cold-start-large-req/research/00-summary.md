# 00 跨维度收敛 — 给 SKEIN cold-start 档的机制推荐

> 调研对象: SKEIN plan skill 现有 3 档 (direct-fix/standard/heavy) 均假设用户给任务描述; 缺一档处理「模糊愿景/痛点」(如「重构整个权限系统」「我们要加 AI 能力」)。本 summary 收敛 5 维调研 → 推荐借鉴的核心机制。
>
> 数据源: 本仓 skein-plan/SKILL.md (代码勘察) + agent-reach **dev (gh api/search, GitHub 一手仓)** + agent-reach **social (twitter search, 社区视角)** + WebSearch (exa off 降级, 覆盖需求工程/拆解/scope/失败模式方法论文献)。
>
> 声明: exa_search off → 网页搜索降级 WebSearch; reddit warn (OpenCLI 扩展未装) → Reddit 社区视角未覆盖, 本维社区数据由 Twitter 补。

## 一句话结论

cold-start 不是新造引擎, 是在现有 brainstorm→grill→拆 subtask 链路**前面加一个「愿景收敛」入口**, 用 **Job Story 句式 + said/implied/missing 三分 + walking skeleton 第一刀** 把模糊愿景逼成第一个可执行 task, 借鉴 liza 仓的**技术** (SMARC/双受众/anti-patterns/size 门) 而非**结构** (不搬其四文档体系, 遵守 SKEIN「探索封顶尽早转异步」铁律)。

## 推荐借鉴的 5 个核心机制 + SKEIN 适配建议

### 机制 1: 「Job Story 句式」作冷启动入口填空骨架 (强推)

- **是什么**: "When [situation], I want to [motivation], so I can [expected outcome]" 三段填空。来源: JTBD / Christensen Institute / Intercom (01 维)。
- **解决什么痛点**: 用户说「加 AI 能力」时, main 现有 brainstorm 逐问 (目标/边界/验收) 太陡, 用户答不出。Job Story 把开放式追问降级成填空, 降低冷启动门槛。
- **SKEIN 适配**: 不新造机器。在 brainstorm 第一步前加「愿景翻译」环节 — main 把用户原话套进 Job Story 三段草拟, 用 `AskUserQuestion` 让用户确认/修正三段 (situation/motivation/outcome 各给 2-3 推荐选项)。产物写进 prd.md 新增的「愿景 (Job Story)」段。
- **弃用风险**: 无。轻量、可复用、与现有 brainstorm 无冲突。

### 机制 2: 「said / implied / missing」三分 + SMARC 可测门 (强推)

- **是什么**: 写需求前先区分明说/暗示/缺失 (liza Parse 三分); 每条 AC 须 Specific/Measurable/Achievable/Relevant/Context-bound, 做不到 = Open Question 而非模糊需求 (liza SMARC)。来源: liza-mas/liza skills/detailed-spec-writing (03 维, 一手)。
- **解决什么痛点**: 防止 AI 在冷启动里脑补用户没说的需求 (Assumption Burial / Wishful Specification / Scope Absorption — 三大 anti-pattern)。
- **SKEIN 适配**:
  - missing 项 → 显式列 prd.md「Open Questions」段, 用 `AskUserQuestion` 逐条问 (轮数上限 ≤3, 超限标「需求未定」停 planning, 复用现有兜底 SKILL.md:89)。
  - SMARC → 作为 grill 硬门的新增审查轴 (现有 grill 重点「用户想法=PRD」, 加一条「每条 AC 可测、无 user-friendly 类词」)。
  - 所有 AI 假设 → 强制写 prd.md「Assumptions」段, 禁埋正文。
- **弃用风险**: 无。纯校验增强, 不改机器。

### 机制 3: 「walking skeleton 第一刀」+ size 门强制拆分 (强推, 与现有天花板合并)

- **是什么**: 冷启动拆完能力域后, **第一个 task 强制是端到端最薄能跑通的 walking skeleton** (验证假设), 而非铺平所有能力域。+ size 门: 复合嗅味 ("X and Y and Z") / 多独立能力 / 会产 >8 story → 必拆, 禁 mega。来源: liza epic-writing §0.Size + vertical slice/walking skeleton 共识 (02/04 维)。
- **解决什么痛点**: 「重构整个权限系统」类最容易拆成又大又平的技术模块清单, 第一个 task 过重, 验证不了任何假设。
- **SKEIN 适配**:
  - walking skeleton: cold-start 拆 subtask DAG 后, 标注其中「贯穿所有层最薄路径」的那条作必须先 done 的 walking skeleton (用现有 `--deps` 让其他 subtask 依赖它)。
  - size 门: 把 liza 的「复合嗅味文本判据」「capability≠技术模块提醒」「>8 拆多 task」**并入现有「复杂度天花板」表**(SKILL.md:34-46), 作 cold-start 专属行。阈值 8 与 liza 的 3-8 同号, 无冲突。
- **弃用风险**: walking skeleton 对纯重构 (strangler) 场景需变体 (见机制 5), 不能硬套。

### 机制 4: 「Out-of-Scope 显式段」+ MoSCoW 只取 Won't (适配, 轻量)

- **是什么**: prd.md 强制有「非目标」段, 显式列「源说 X, 不做 Y/Z」。+ MoSCoW 只借 Won't-have 桶 (Could/Won't 落非目标, Should 落后续 task 占位不 create)。来源: liza Out-of-Scope + MoSCoW (04 维)。
- **解决什么痛点**: Scope Absorption + scope 无限膨胀 (05 维失败模式)。
- **SKEIN 适配**: 现有 prd 模板已有「边界/非目标」段 (SKILL.md:73), 强化其**强制力** (未填非目标 = planning 未收敛, 与现有 TODO 勾选机制一致)。MoSCoW 的 Must/Should/Could 分类**不引入** (SKEIN 用复杂度天花板 + capability 切分已覆盖排序需求, 不重复造桶)。
- **弃用项**: Kano / RICE 打分 (需客户/数据, AI 单对话难凑, 标「不适合 AI 即时」)。

### 机制 5: 场景分流的拆解入口 — greenfield 用 vertical slice, 重构用 strangler fig (需改造, 仅 heavy 补强)

- **是什么**: cold-start 拆解入口按场景分 — 「加新能力」(greenfield 段) 第一个 task 走 vertical slice (端到端纵切); 「重构存量」(重构整个 X 类) 走 strangler fig (建 facade 定边界契约→分批替换→退役旧)。来源: strangler fig (Fowler) + vertical slice 社区共识 (02 维)。
- **解决什么痛点**: 单一拆解模式套不住两类需求 — greenfield 要先验证闭环, 重构要先定新旧边界防大爆炸重写。
- **SKEIN 适配**:
  - greenfield 段: 与机制 3 walking skeleton 合并, 不单列。
  - 重构段: 在现有 heavy 档 breaking-refactor (references/breaking-refactor.md) 基础上补「strangler 结构建议」— 第一个 task = 建 facade + 定边界契约, 中间 task = 逐块替换 (各 `--deps` 串), 末 task = 退役旧路径。**作为 heavy 档的拆解模板补充, 不新造档** (cold-start 识别出是重构类 → 路由进 heavy + strangler 模板)。
- **弃用风险**: strangler 需系统有可加 facade 的接缝; 对无接缝硬壳系统不适用, 此时退回 breaking-refactor 大爆炸 (需用户裁定)。

## 弃用项 (明确不引入)

| 弃用项 | 理由 |
|---|---|
| liza 四文档体系 (vision→epic→story→spec 四个 git-tracked md) | 违反 SKEIN「探索封顶尽早转异步」铁令; SKEIN 是 task→subtask 两层, 折叠 epic 进 prd.md 章节即可 |
| OST 完整四层 (含 experiments 层) | experiments 层在 SKEIN 无对应概念, 折叠进 subtask 验收 checklist; 只借 outcome/opportunity/solution 三层思想 |
| Story Mapping (Jeff Patton 立体 backlog) | SKEIN 是 DAG 非 backlog; 取其「backbone 先行」= walking skeleton 已够 |
| IDD intent-as-executable-spec | 太重 (意图直接变可执行断言); SKEIN task.json 已是单一真值源, 取「意图先沉淀契约」思想即可 |
| Kano / RICE 打分排序 | 需客户调研/数据, AI 单对话难凑; cold-start 标不适用 |
| MoSCoW Must/Should/Could 分类桶 | SKEIN 用复杂度天花板 + capability 切分已覆盖; 只借 Won't-have |
| Anthropic 官方 cold-start skill (对标) | anthropics/skills 官方 17 skill 无此档 (03 维), 无可对标对象; SKEIN 自建是差异化机会 (非弃用, 是无现成可抄) |

## 落地形态建议 (供 main + 用户裁定, 不替拍板)

> 以下是对 SKEIN 机器层面的**建议方向**, 非结论。是否新增 cold-start 档 / 改 brainstorm / 改 prd 模板 / 改 grill 轴, 由 main 汇总后交用户。

1. **档位路由**: 在现有 direct-fix/standard/heavy 旁加 `cold-start` 档, 判据 = 「用户输入是愿景/痛点 (非任务描述) + 答不出 Job Story 的 outcome 段」。命中 → 走愿景收敛入口再路由进 standard/heavy。
2. **brainstorm 前置「愿景翻译」**: Job Story 三段填空 + said/implied/missing 三分, 产物落 prd.md 新段。
3. **prd 模板增强**: 强制「愿景(Job Story) / Open Questions / Assumptions / 非目标」四段 (前两段新增, 后两段强化)。
4. **grill 加轴**: AC 可测性 (SMARC, 无 wishful 词) + 产出 vs 原始愿景一致性 (防 drift) + 是否超出源诉求 (防 scope absorption)。
5. **复杂度天花板表加 cold-start 行**: 复合嗅味文本判据 + capability≠模块提醒 + >8 拆多 task (与 liza 3-8 同号)。
6. **heavy 档补 strangler 拆解模板**: 重构类第一个 task = facade+契约, 末 task = 退役。
7. **失败兜底复用**: 现有「答不出停 planning」(SKILL.md:89) 加 cold-start 追问轮数上限 (≤3) + 政治冲突检测标 `需要: 人工仲裁`。

## SPEC 沉淀候选 (供 finish sediment, 不在本调研范围落盘)

- `cold-start` 档判据 + Job Story 入口若被采纳, 是「后续同类大需求会再走」的可复用流程 → 建议作 `[skill]` 类目 recall 层规则沉淀。
- SMARC 作 grill 轴 / Out-of-Scope 强制段 → 建议作 `[skill]` recall 规则。
- liza size 门 (3-8 / 复合嗅味 / capability≠模块) 与现有天花板合并 → 更新现有天花板规则。

---

## 附: 各维证据密度

| 维 | 一手条目 | 二手条目 | 社区条目 | agent-reach 用了? |
|---|---|---|---|---|
| 01 需求工程 | 3 (liza×2 + JTBD) | 4 | 0 | 否 (WebSearch, exa off) |
| 02 大需求拆解 | 3 (liza×2 + IDD) | 4 | 1 (Reddit vertical slice) | 否 (WebSearch) |
| 03 AI 辅助梳理 | 6 (liza×3 + tanure + ntnt + 多仓) | 0 | 1 (Twitter GPT-5.6) | **是: dev(gh) + social(twitter)** |
| 04 scope 收敛 | 2 (liza×2) | 4 | 0 | 否 (WebSearch) |
| 05 失败模式 | 5 (liza×4 + 本仓 SKILL + IDD) | 3 | 0 | 否 (WebSearch) |

满足验收: 5 维 + summary 全落盘; 每维 ≥3 可溯源 (最少维 04 有 6 条); 2 维 (03 + 跨维 Twitter) 用了 agent-reach 外部检索; summary 给 5 核心机制 + 适配 + 弃用项。
