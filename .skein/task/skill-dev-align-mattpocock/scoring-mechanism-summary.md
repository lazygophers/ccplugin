# 评分机制汇总 — skill-dev 9 维 + plugin-dev 8 维

> 本文件汇总 s1/s2/s3 改造后两 skill 的评分体系，供用户定夺后续优化方向。质量门均通过（claude -p 一次通过，非空 + 识别正确）。

## 1. skill-dev · 9 维 Rubric 全表（总分 100）

来源：`skills/skill-dev/skill-dev/references/dimensions.md`（适配自 darwin-skill v2.0，依据 SkillLens arXiv 2605.23899）。

每维 5 列：**方向**（↑=越高越好 / ↓=越少越好）· **理想值**（量化锚点）· **完成准则底线**（checkable + exhaustive，未达即该维未过）。

| # | 维度 | 权重 | 方向 | 理想值 | 完成准则底线（checkable + exhaustive） |
|---|------|------|------|--------|---------------------------------------|
| 1 | Frontmatter 质量 | 7 | ↑ | name 规范 + description 做什么+何时用+触发词 + **项目底线 < 512 字符** + when_to_use < 128 | name 合规 / description 含做什么+何时用+触发词 / < 512 字符 / when_to_use < 128 |
| 2 | 工作流清晰度 | 12 | ↑ | 每步有序号 + 输入/输出契约 + Done when 完成准则 | 每步有序号、每步输入/输出明确、每步有 checkable 完成准则 |
| 3 | 失败模式编码 | 12 | ↑ | 每个关键失败点显式 if-then 三段式（触发/一线修复/兜底） | 每个失败分支都是三段式、无裸两列（症状/解法） |
| 4 | 检查点设计 | 6 | ↑ | 关键决策点 🔴/🛑/STOP 显性视觉标记 + 用户确认动作 | 每个关键决策点有视觉标记、每个标记配用户确认（非「建议」措辞） |
| 5 | 可执行具体性 | 17 | ↑ | 具体参数/格式/示例可直接复制执行 | 全文无「建议/可以考虑/根据情况/灵活把握」软措辞 |
| 6 | 资源整合度 | 4 | ↑ | references/scripts 路径可达 + SKILL.md 引用 + 引用只深一层 | 每个引用文件路径可达、每个孤立文件都在 SKILL.md 引用、引用只深一层 |
| 7 | 整体架构 | 12 | ↑ | 层次清晰、无冗余、runtime 中立 | 全文无 AI 腔、无孤立冗余段落 |
| 8 | 实测表现 | 23 | ↑ | ≥2 test prompt 实测，输出质量符合宣称 | 跑过 ≥2 test prompt、每个 prompt 有 before/after 结论 |
| 9 | 反例与黑名单 | 6 | **↓** | 主体正向表述；仅不可正化的硬护栏留反例且配正例 | 每条保留的反例都配正例、有 Rejected framings 段、无裸「不要做 Y」黑名单 |

**评分公式**：dim 1-7、9 每维打 1-10 × 权重；dim8 按 2-3 test prompt 输出质量打 1-10；总分 = Σ(维度分 × 权重) / 10，满分 100。

**HL 杠杆**（high-leverage，4 行撬动 +3 分）：HL-1 dim4 显性视觉标记 / HL-2 dim3 if-then 三段式 fallback / HL-3 Phase1 维度相关簇（dim2/3/4 工作流簇 / dim5/7 表达簇 / dim1/9 触发簇）/ HL-4 Phase4 触顶自动 break。

**实证基础**（darwin-skill 自引 SkillLens）：LLM-as-judge 准确率仅 46.4% → 加 dim3/5/9 升到 73.8%。结论：gross degradation 识别可靠，fine-grained 不可信，重要决策必须人审。

## 2. plugin-dev · 8 维 Rubric 全表（总分 100）

来源：`skills/skill-dev/plugin-dev/references/optimize-rubric.md`（基于官方 plugins 三篇规范 + 本仓库 docs/ + plugins/tools/* 真实插件）。

| # | 维度 | 权重 | 方向 | 理想值 | 完成准则底线（未达 = 该维未完成） |
|---|------|------|------|--------|---|
| 1 | Manifest 合规 | 16 | ↑ | 10 | `jq .` 通过；name kebab-case = 目录名；description 含「做什么 + 差异化」；author/license/homepage 齐 |
| 2 | 组件接线完整 | 20 | ↑ | 10 | 体检 #3 #4 双向零悬挂零漏挂；路径大小写与磁盘一致 |
| 3 | 结构规范 | 12 | ↑ | 10 | 组件在插件根非 `.claude-plugin/`；SKILL.md 大写；`.claude-plugin/` 仅 plugin.json |
| 4 | Hook 健壮性 | 14 | ↑ | 10 | 每 hook `${CLAUDE_PLUGIN_ROOT}` + `timeout` + 失败 exit 0；guard 用 exit 2；matcher 非 `*`；async 仅副作用型 |
| 5 | 组件质量 | 14 | ↑ | 8 | 逐 skill/agent/command 过：触发词准、无占位符残留（**深评交 /skill-dev，本维只做门槛**）|
| 6 | Marketplace 一致性 | 12 | ↑ | 10 | marketplace.json name/source/description/author/license/keywords 与 plugin.json 逐字段对齐；source 路径存在；无 `../` |
| 7 | 文档完整 | 6 | ↑ | 8 | README 有装/用/例三段；description 无「灵活应用」空话尾巴 |
| 8 | 命名与元数据一致 | 6 | ↑ | 10 | 目录名 = manifest name = marketplace name；keywords 命中真实能力非堆砌 |

**评分公式**：每维 1-10 × 权重，Σ/10 满分 100。

**体检前置**：评分前先跑 9 项机械体检（manifest JSON 合法 / name kebab / 双向接线 / SKILL.md 大写 / 组件不误放 / hook 变量 + timeout / marketplace 一致），维度 1/2/3 命中 = P0 先修，再谈质量。

## 3. 共享收敛机制（两 skill 一致）

| 机制 | 落地 | 防 |
|---|---|---|
| **ratchet 严格更好才留** | 改进后总分**严格高于**改进前才保留；退步 `git revert HEAD`（禁 `reset --hard` 丢工作树，保留历史可审计） | 退步硬凑、归因失效 |
| **触顶停** | 连续 2 轮 Δ < 2 → break；+0.15 是停手信号非继续信号 | 硬凑 MAX_ROUNDS（over-engineering） |
| **膨胀护栏** | 改后 SKILL.md / 插件体积 > 原 ×1.5 → 拒绝提交，先精简再评 | 「加废话让 LLM 觉得更详细」凑分膨胀 |
| **方向轴校验** | 收敛不只看总分；退步维度（方向轴反向走）即使总分涨也标警示，留滚交人审 | 拆东墙补西墙式虚假改进 |
| **独立验证防自评偏差** | 每轮评分 spawn 独立子 agent，禁同 context 自评（自评 +1 偏乐观；LLM-as-judge 46.4% 准确率） | 乐观偏差 |
| **单变量轮** | 一轮只改 1 维度或 1 相关簇（plugin: 2/3/4 接线相关簇；skill: dim2/3/4 工作流簇） | 多维同改归因失效 |
| **二层 gate** | gross gate（总分 Δ>0 + 体检硬伤数↓ + 接线零悬挂 + 质量门非空）+ 人审 gate（破坏性/接线/触发词变更 → AskUserQuestion，禁「我觉得更好」直落） | 凭感觉直落破坏性变更 |
| **诚实边界** | fine-grained 不可信，重要决策必须人审；dry_run > 30% → 评估失效警告 | 编造看似完美的 90 分 |

## 4. 各 skill 评分适用场景

| 场景 | 走 | 理由 |
|---|---|---|
| 单个 skill / agent / command / 单组件 `.md` 的深度质量评估 | **skill-dev 9 维** | dim1-9 覆盖 frontmatter / 工作流 / 失败模式 / 检查点 / 具体性 / 资源 / 架构 / 实测 / 反例，针对单文档方法论质量 |
| 整个 Claude Code 插件（manifest + 接线 + hook + marketplace）的健康度评估 | **plugin-dev 8 维** | 维度聚焦插件级硬伤（接线零悬挂 / hook 健壮 / marketplace 一致），单组件深评只是其维度 5 门槛 |
| 不确定是单 skill 还是插件级问题 | 先 plugin-dev 体检 9 项定位硬伤，硬伤修完仍单 skill 退化 → 转 skill-dev 9 维 | 体检命令机械可跑，零成本先排插件结构 |
| 人物角色扮演 DNA / 表达语气 / 人格模拟 | 🛑 两 skill 都不覆盖 | skill-dev 明确「蒸方法论不蒸人物」 |

**边界原则**：plugin-dev 维度 5（组件质量）只做门槛检查（触发词准不准 / 有无占位符残留），单组件的 9 维深度评分路由 skill-dev 流程 B。两者职责互不重叠，靠路由表互导。

## 5. 后续优化建议（基于本次改造观察，供用户定夺）

1. **plugin-dev 8 维权重经验汇总无第三方基准**。9 维有 SkillLens 实证（46.4% → 73.8%）+ darwin 本机 controlled study 支撑，8 维的 16/20/12/14/14/12/6/6 是经验拍定。可选：把 8 维权重对齐到 skill-dev 的实证分布（如把「组件接线完整」权重从 20 提到与 dim8 实测同档），或跑一次真实插件（plugins/tools/skein 等）回归校准。**优先级低**——当前 8 维已覆盖所有插件级硬伤类型。

2. **skill-dev 9 维 dim9 方向轴 ↓ 是唯一反向维度**，报告模板里 after 分可能比 before 低（反例减少）但视为改进。当前模板的「方向轴」段已处理，但 rubric 评分公式「严格高于」对 dim9 这类反向维度的语义未显式说明（总分会因 dim9 after < before 而「下降」实为改进）。可选：在 dimensions.md 评分规则加一句「dim9 反向：after 分降低 = 该维改进，纳入 Δ 时取负号」。**优先级中**——影响报告一致性。

3. **两 skill 共享收敛机制（ratchet / 触顶停 / 膨胀护栏 / 独立验证）当前各写一份**，存在漂移风险（如 skill-dev 写「触顶 Δ<2 连续 2 轮」，plugin-dev 同样写，未来改一处易忘改另一处）。可选：抽一个 `skills/skill-dev/_shared/convergence-protocol.md` 共享文件，两 SKILL.md 引用。**优先级低**——当前两份文本一致，未漂移；抽共享会增加一层引用（违反「引用只深一层」），需权衡。
