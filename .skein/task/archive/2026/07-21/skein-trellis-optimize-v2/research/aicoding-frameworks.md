# AI Coding 任务/流程框架调研 — 对 skein 的优化建议

调研时间: 2026-07-18 · 数据源: agent-reach (AVAILABLE, gh CLI / twitter / exa) + WebSearch/WebFetch 降级补缺 (reddit/medium/blog 未全覆盖登录态平台) · 罗盘: skein 现状 (task.json + DAG + 4 阶段 plan/exec/check/finish + 两层 core/recall 记忆 + 双层同构 DAG 并发 2)

> 通用观察: 多数框架 (claude-flow/Ruflo, SPARC) 文案含大量 marketing 肿胀词 ("quantum consciousness / hive-mind / 涌现智能"), 信号噪声比低。真正可借鉴的是**具体机制**, 不是包装话术。Devin/Cognition 反而公开发声**反对多 agent 架构** (称脆弱), 与 skein DAG 多 agent 编排形成张力, 见末节反例。

---

## 1. Claude Flow / Ruflo (ruvnet/claude-flow) — 任务编排

claude-flow 已更名为 Ruflo, 定位 "agent meta-harness for Claude Code and Codex"。本质 = MCP server + hooks + 大量 plugin (swarm/rag-memory/autopilot/federation/...)。

**独特设计 (URL 证据)**:
- **swarm 并行 + BatchTool**: 多 AI worker 并行执行 subtask (plan/coding/test/security 各一), 共享上下文。v1.0.50 称 BatchTool 并行带来 20x 提升。源: Reddit r/ClaudeAI v1.0.50 公告 (reddit.com/r/ClaudeAI/comments/1ld7a0d); Ruflo README (gh api repos/ruvnet/claude-flow/readme)。
- **hooks 自动路由**: `npx ruflo init` 后 "hooks 系统自动 routes tasks, learns from successful patterns, coordinates agents in background" — 用户无需学 314 MCP 工具 / 26 CLI, 正常用 Claude Code 即可。源: Ruflo README。
- **federation**: 跨机器 agent 安全通信。源: README plugins 列表 ruflo-federation。
- **self-learning memory**: agent 从历史成功 pattern 学习 (ruflo-intelligence)。

**对 skein 建议**:
- **借鉴 (弱)**: "hooks 自动路由, 用户零认知" 的理念 skein 已具备 (SessionStart 注入 + flow skill 自动加载), 无需新增。
- **拒绝**: swarm 60+/100+ agent + 314 工具的体量与 skein "5 个受限具名 agent + 递归护栏" 的克制哲学冲突; claude-flow/Ruflo 是膨胀反面教材, 不可学其工具爆炸。
- **演进 (推测)**: "self-learning from successful patterns" 概念可映射 skein sediment, 但 skein 是**显式判定门 + 写盘**, 比 claude-flow 隐式 learning 更可控, 维持现状即可。

---

## 2. Cline (cline/cline) — VSCode AI coding

**独特设计 (URL 证据)**:
- **Plan/Act 双模式强分离**: Plan mode 只探索不改文件 (analysis/architecture/strategy), Act mode 才执行修改/命令。可分别选不同 LLM。源: docs.cline.bot/core-workflows/plan-and-act; KodeKloud notes。
- **Checkpoints = shadow git 快照**: 每次改文件/跑命令自动快照到**隐藏 shadow git 仓库** (VSCode global storage), 用 .gitignore/.gitattributes 控体积。可 Compare/Restore 任意 checkpoint, **保留对话上下文**。源: docs.cline.bot/core-workflows/checkpoints; Medium "The Shadow Git Behind Cline"; Cline v3.1 发布 (reddit r/ChatGPTCoding/comments/1hvaihm)。
- **已知坑**: shadow git restore 有 bug — #1213 (restore 误删 workspace 文件)、#9590 (大 monorepo corrupt)、#6645 (IDE VFS 缓存不同步)。源: github.com/cline/cline issues。
- **任务/plan 可在 planning 阶段产 todo list**, Act 阶段可跟踪。

**对 skein 建议**:
- **借鉴 (强, top 1)**: **shadow git checkpoint 思路** → skein 已有 worktree 隔离 (1 task 1 worktree) + finish commit/merge, 但**缺少 subtask 级可回滚快照**。可演进: subtask done 后自动 commit (worktree 内, 不 push), 失败/自愈重派时可 reset 回上一个 subtask 边界。当前 skein subtask 失败靠 `subtask start` 重派 + 手动修, 无原子回滚点。量化收益: check 失败自愈从 "重派 + 手动清理半改" 变 "reset 回 checkpoint 重派", 减少半改残留。
- **借鉴 (中)**: **Plan/Act 强分离** skein 已天然具备 (plan/exec/check/finish 4 阶段硬门, grill 硬门), 无需新增; 但可确认 plan 阶段产出**显式 todo list** 进 task.json (skein subtask --check 已做)。
- **拒绝**: shadow git 在大 monorepo corrupt 的已知坑 (Cline #9590) 警示 skein worktree 实现需防 (skein 用 worktree 而非 shadow repo, 隔离更干净, 风险更低)。

---

## 3. Roo Code (RooCodeInc/Roo-Code) — Cline fork, mode 系统

**独特设计 (URL 证据)**:
- **内置 mode + 自定义 mode (.roomodes)**: 默认 Code/Ask/Architect/Debug/Orchestrator, 用户可 `.roomodes` 文件自建 mode (带各自 tool 权限/prompt)。源: roocodeinc.github.io/Roo-Code/basic-usage/using-modes; atomicobject.com "How I Effectively Use Roo Code"; HN 43849056。
- **switch_mode 工具**: agent 运行中可自主切 mode。源: roocodeinc.github.io/Roo-Code/advanced-usage/available-tools/switch-mode。
- **Orchestrator mode + new_task + Boomerang Tasks**: Orchestrator 用 `new_task` 把目标拆 subtask 派给合适 mode (Architect/Code/Debug), 完成 subtask **boomerang 回 orchestrator** 跟踪全局进度。源: reddit r/RooCode/comments/1jaro0b; LinkedIn "Boomerang Tasks"; gist nickcent/49281afd; wadan.co.jp boomerang-mode (Roo v3.8.0 引入)。
- 流程: Orchestrator → architect 出 spec → 迭代达成共识 → hand to Code 执行 (HN 44562794)。

**对 skein 建议**:
- **借鉴 (强, top 2)**: **mode 系统的 per-mode tool 权限** 映射 skein 已有 (5 个具名 agent 各绑 skill + 工具受限 + 递归护栏), 但 skein mode 是**预定义具名 agent 5 个**, 无用户自建扩展。可演进: 提供 `.skein/agents/` (或复用 .claude/agents/) 让用户/项目自定义具名 agent 绑 skill, planning 派 subtask 时可 `--agent <custom>`。量化: 项目特定角色 (e.g. 前端/迁移/i18n) 不必塞进通用 executor。
- **借鉴 (中)**: **Boomerang / new_task 双向回路** skein 已等价 (claim→派→done/fail→reclaim), 但 skein 缺**任务回流给 orchestrator 时携带结构化结果摘要** 的显式 schema — Roo new_task 有明确 task+result 双向。skein dispatch prompt 输出格式已有压缩摘要, 可对齐确认。
- **拒绝**: agent 运行中自主 switch_mode (无 main 仲裁) 与 skein "main 作调度器, 顺序归 planning" 冲突, 不学。
- **演进 (推测)**: Roo Orchestrator→Architect→Code 三段与 skein plan(grill)→exec→check 同构, 验证 skein 流程方向正确, 无需改。

---

## 4. Claude Engineer (Doriandarko) — task/memory

**信号弱**: 搜索未直接命中 Doriandarko/Claude Engineer 的现代 task/memory 机制, 结果偏向通用 Claude Code memory system (monsef.chafik 4 层架构 / sammiihk memory/ 目录 + MEMORY.md 索引 + active-work.md)。

**独特设计 (URL 证据, 部分来自相邻 memory system 而非 Claude Engineer 本身)**:
- **memory/ 目录 + MEMORY.md 索引 + 按主题分文件**: 通用模式 (dev.to sammiihk)。每主题一文件, MEMORY.md 作索引, active-work.md 跨会话续。
- **短/长/scoped 三层记忆** (mindstudio blog)。
- **memory tool (Claude platform 官方)**: 目录式 memory 文件 + create/read/update/delete。源: platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool。

**对 skein 建议**:
- **拒绝 (强)**: skein 的 **core/recall 两层 × 类目** 已远超通用 memory/ 目录方案 — 有 sediment 判定门、自动 reindex、软预算降级、bootstrap/reconstruct。通用方案是 skein 的退化版, 无可借鉴。
- **借鉴 (弱, top 5 备选)**: memory tool 的 **CRUD 原语** 概念 skein 已等价 (skein-memory archive/restore/sediment), 维持。
- **结论**: Claude Engineer 信号不足, 标 `需要: 若要深挖 Doriandarko 具体实现需直查其 GitHub 仓库源码`, 当前调研不覆盖。

---

## 5. OpenHands (All-Hands-AI/OpenHands) — agent runtime

**独特设计 (URL 证据, 信号最强)**:
- **stateless Agent + Action/Observation 事件循环**: "a tiny core: a stateless Agent that emits Actions, executes Actions, returns Observations, and an LLM"。Action = 工具调用 (ActionEvent), Observation = 结果 (ObservationBaseEvent), 共同事件类型。源: arXiv 2511.03690v1 (OpenHands SDK 论文); dev.to truongpx396 "OpenHands Deep Dive"; runtime.all-hands.dev。
- **Docker/sandboxed Runtime**: 隔离执行环境。源: docs.openhands.dev/openhands/usage/architecture/runtime。
- **Condenser 系统 (核心亮点)**: 管理 conversation history 压缩, 把长 event history 压成 condensed 形式保持 agent context 在 LLM token 限内, 自动 truncate 并替换丢弃内容 (summary)。源: docs.openhands.dev/sdk/arch/condenser; docs.openhands.dev/sdk/guides/context-condenser; blog openhands-context-condensensation。
- **model-agnostic 多 LLM routing + 内建安全分析** (OpenReview pzVmWs6yGq)。
- V0 有 AgentController + EventStream pub/sub (EventStream.subscribe)。

**对 skein 建议**:
- **借鉴 (强, top 3)**: **Condenser 思路** → skein 当前靠 SessionStart 注入 core (软预算 8000 字符) + recall 按需召回控制上下文, 但**长 task / 多 subtask 累积的对话历史无自动压缩**。可演进: 长会话 >80% (skein CLAUDE.md 已有此阈值提示) 时, main 主动跑一次 "condense" — 把已完成 subtask 的历史压成 findings 摘要落盘 (skein 已有 research/findings.md 机制), 释放上下文。量化: 避免 long task 后期上下文爆。
- **借鉴 (中)**: **Action/Observation 显式事件模型** skein 已部分等价 (subtask done/fail + check 回传 + dispatch prompt 6 字段), 但 OpenHands 的**类型化事件 + EventStream pub/sub** 更利于辅助服务消费 (如 #6706 提议记录 condensation 事件供可观测)。skein 可演进: check/finish 关键事件结构化落 task 日志 (已有 output trace), 提升 task 可观测性。
- **拒绝**: sandboxed Docker runtime 对 skein (Claude Code 插件, 非独立 runtime) 不适用, 不学。

---

## 6. Aider (Aider-AI/aider) — git-integrated coding

**独特设计 (URL 证据, 信号强)**:
- **repo map = tree-sitter + personalized PageRank**: tree-sitter 解析成 AST, 节点=定义 (function/class), 边=引用, **personalized PageRank (以用户 /add 的文件为 personalization)** 排序选最重要定义塞进 token 预算。保持 LLM 在 codebase 中定向。源: aider.chat/docs/repomap.html; aider.chat/2023/10/22/repomap.html (tree-sitter 博客); 源码 aider/repomap.py `get_ranked_tags`; github issue 1385。
- **auto-commit 每次 edit**: 默认每改一处自动 git commit (atomic), 自动生成 commit message, `--no-auto-commits` 关。源: aider.chat/docs/git.html; DeployHQ "atomic auto-commits"。
- **architect/editor 双模型**: architect (reasoning 模型) 规划, editor 模型应用 SEARCH/REPLACE diff 块, 各 edit 后仍 auto-commit。源: DeployHQ; SurePrompts prompting guide。
- **SEARCH/REPLACE diff 块格式** 提案编辑。

**对 skein 建议**:
- **借鉴 (强, top 4)**: **personalized PageRank repo map** → skein 记忆系统是**项目约定层** (core/recall spec), 但**缺代码结构层的自动上下文**。planning 拆 subtask / dispatch 给 subagent 时, 若能生成 "以本 subtask 涉及文件为 personalization 的 ranked symbols map" 注入 dispatch prompt「已知」段, 可替代部分 grep 探索。量化: subagent 少跑 N 次 grep/Glob 定位符号。但实现重 (需 tree-sitter + graph), 属**演进方向非近期**, 标为可选。skein 已有 SessionStart core 注入 + recall 召回做"约定层"上下文, 代码结构层是补全。
- **借鉴 (中)**: **auto-commit per edit / atomic** → skein 已有 auto_commit (config.yaml) + finish commit/merge, 但粒度是 **task/subtask 级** (finish 一次性 commit), 非 Aider 的**逐 edit**。结合 top 1 (Cline checkpoint) 思路: subtask done 即 commit (worktree 内), 既作 checkpoint 又保留细粒度历史, finish 时 squash/merge。量化: 自愈回滚有原子点 + git 历史更细。
- **拒绝**: SEARCH/REPLACE diff 格式是 Aider 的无 tool-use 模型适配, skein 用 Claude Code Edit/Write 工具, 不适用。
- **演进**: architect/editor 双模型分离与 skein plan(grill 用更强推理?)→exec 分离同构, 可确认 plan/grill 是否该强制用更强模型 (当前 model: inherit)。

---

## 7. Devin (Cognition) + 其他 (AutoGPT 等) — 参照对比

**Devin 独特设计 (URL 证据)**:
- **Interactive Planning**: plan 阶段与用户交互确认才执行。源: digitalapplied.com Devin 完整指南。
- **parallel cloud agents + ACP (Agent Communication Protocol)**: Devin Desktop 多 agent 经 ACP。源: reddit r/CognitionLabs/comments/1u1ga5s。
- **Cognition 公开反对多 agent 架构**: 称其 "fragile", 主张集成式单 agent。源: reddit r/ChatGPTCoding/comments/1latkqz; LinkedIn ricky-ho 分析。

**对 skein 建议 (张力点, 需用户裁)**:
- **需要 (分歧, 交 main 转用户)**: skein 核心是 **DAG 多 subtask + 并行派 agent (并发 2)**, 而 Cognition 公开主张多 agent **脆弱**、单 agent 更稳。这是根本性张力。两方各有理: 多 agent 并行快但协调/一致性成本高 (skein 用 check 一致性核查 + 自愈闭环应对); 单 agent 简单但慢/上下文易爆。**skein 的并发上限 2 (克制) + check 一致性门 + 根因复盘** 已是"受控多 agent"的折中, 比 claude-flow swarm 60+ 克制得多。是否进一步收敛并发到 1 (Devin 路线) 或放开 (>2) 需用户结合实际痛点定。当前调研不替用户拍板。
- **借鉴 (中)**: **Interactive Planning (用户确认才执行)** skein 已部分有 (grill 硬门 + brainstorm + planning 登记), 维持。
- **AutoGPT 等**: 早期 autonomous loop (goal→plan→execute 无门) 已被业界证伪 (无监督长跑漂移), skein 4 阶段硬门 + 人审是对其失败的修正, 确认 skein 方向对, 无新增。

---

## Top 5 可借鉴点 (按价值排序, 以 skein 为罗盘)

| # | 借鉴点 | 源框架 | 对 skein 的演进 | 量化收益 | 状态 |
|---|--------|--------|----------------|----------|------|
| 1 | **subtask 级 checkpoint (shadow/git 快照)** | Cline | subtask done 即 commit (worktree 内, 不 push); 失败自愈/重派时可 reset 回边界, 而非手动清半改 | 自愈从"重派+手清"变"reset 重派"; 减半改残留; git 历史更细 (配合 top 4 atomic) | 建议近期 |
| 2 | **可自定义具名 agent (per-role tool 权限)** | Roo Code (.roomodes) | 放开 5 个预定义具名 agent → 允许项目/用户自建 agent 绑 skill, planning 派 `--agent <custom>` | 项目特定角色 (前端/迁移/i18n) 不必塞通用 executor; 复用度提升 | 建议中期 |
| 3 | **长会话 condenser (对话历史自动压缩落盘)** | OpenHands | main 在 >80% 阈值触发时主动 condense: 完成子任务历史压成 findings 摘要落盘, 释放上下文 | 避免 long task 后期上下文爆 (skein CLAUDE.md 已有阈值提示但无自动动作) | 建议中期 |
| 4 | **代码结构层 repo map (tree-sitter + PageRank)** | Aider | dispatch prompt「已知」段注入"以本 subtask 涉及文件 personalization 的 ranked symbols" | subagent 少跑 N 次 grep/Glob 定位符号 | 演进方向, 实现重, 可选 |
| 5 | **auto-commit per subtask (atomic)** | Aider | subtask done 即 atomic commit (与 #1 合一), finish 时 squash/merge | 配合 #1 提供回滚点 + 细粒度历史 | 与 #1 合并实现 |

**次级/拒绝项**: claude-flow/Ruflo (膨胀, 反面教材, 拒); Claude Engineer (信号不足, 标需要); Devin 单 agent 路线 (与 skein 多 agent 根本张力, 需用户裁, 不拍板); Cline shadow-git 大 monorepo corrupt 坑 (skein worktree 隔离已规避, 警示)。

---

## 源清单 (证据 URL)

- claude-flow/Ruflo: github.com/ruvnet/claude-flow (gh api readme); reddit.com/r/ClaudeAI/comments/1ld7a0d; dev.to stevengonsalvez 4kd4
- SPARC: github.com/ruvnet/sparc (gh api readme); gist ruvnet/27ee9b1d
- Cline: docs.cline.bot/core-workflows/plan-and-act; docs.cline.bot/core-workflows/checkpoints; medium "The Shadow Git Behind Cline" 8523c7c6437f; reddit r/ChatGPTCoding/comments/1hvaihm; issues #1213/#9590/#6645/#9631
- Roo Code: roocodeinc.github.io/Roo-Code/basic-usage/using-modes; .../available-tools/switch-mode; github.com/RooCodeInc/Roo-Code; reddit r/RooCode/comments/1jaro0b; wadan.co.jp/en/tech/boomerang-mode-ai-orchestration; gist nickcent/49281afd; HN 44562794
- Claude Engineer/memory: dev.to sammiihk 3208; platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool; medium monsef.chafik 84b443066066
- OpenHands: arxiv.org/html/2511.03690v1; docs.openhands.dev/openhands/usage/architecture/runtime; docs.openhands.dev/sdk/arch/condenser; docs.openhands.dev/sdk/guides/context-condenser; dev.to truongpx396 1al0; openreview.net pzVmWs6yGq
- Aider: aider.chat/docs/repomap.html; aider.chat/2023/10/22/repomap.html; aider.chat/docs/git.html; 源码 aider/repomap.py; DeployHQ aider guide; SurePrompts aider prompting
- Devin: devin.ai; cognition.com; digitalapplied.com/blog/devin-ai-autonomous-coding-complete-guide; reddit r/CognitionLabs/comments/1u1ga5s; reddit r/ChatGPTCoding/comments/1latkqz; LinkedIn ricky-ho 7353652784283463680

## 需要 (缺信息/需用户裁)
- Claude Engineer (Doriandarko) 具体 task/memory 实现未直查源码, 当前结论部分借相邻 memory-system 方案, 若要精确需读其 GitHub 仓库源码。
- Devin 单 agent vs skein 多 agent 的根本张力, 不替用户拍板 (交 main 转用户: 是否收敛并发/放开并发)。
