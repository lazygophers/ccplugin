# cortex-dataview Dataview 查询 skill

## Goal

为 cortex 加 Obsidian Dataview 插件支持 skill, AI 可:
1. **构建** — 按需求生成 DQL (LIST/TABLE/TASK) 或 DataviewJS 代码块
2. **修改** — 检测 vault 内已有 Dataview 块, 幂等重写 (保留 marker, 不破坏用户自定义)
3. **查询** — 解释 user 给的 DQL 含义, 给出语法纠错 / 等价改写 / 优化建议

multi-file skill, 走渐进披露 (SKILL.md ≤ 80 行入口 + references/* 按需加载)。

## Requirements

### R1 SKILL.md 入口
- frontmatter: name / description (触发词覆盖"dataview" / "DQL" / "数据视图" / "查询块" / "项目仪表盘") / disable-model-invocation: false / allowed-tools: Read Edit Write
- 决策树: 构建 / 修改 / 解释 三分支
- AUTO_MODE 默认: DQL 不 dataviewjs (安全策略, 详 references/integration-patterns.md)
- references 指针表

### R2 references/dql-syntax.md
内容来自 research, 复制 `research/dql-syntax.md` 到 skill, 删除调研 meta 段, 保留全部技术内容。

### R3 references/dataviewjs-api.md
内容来自 `research/dataviewjs-api.md`, 同上处理。

### R4 references/integration-patterns.md
内容来自 `research/integration-patterns.md`, 同上处理。

### R5 references/modify-flow.md (新写)
专项: 修改现有 Dataview 块的 SOP
- 检测: regex 找 ```dataview / ```dataviewjs fence
- 解析 marker: `<!-- cortex-dataview v<N> kind=<kind> hash=<sha1> -->` (PRD R6 marker 契约)
- 幂等替换: 不变 hash 跳过; 变更则保留 marker + 重写 block
- 安全: dataviewjs 必须 AskUserQuestion 拿用户许可

### R6 references/cookbook.md (新写)
8-10 cortex-vault 实用 query (基于 integration-patterns 的 6 example 扩展):
- 项目仪表盘 (按 score 排序)
- 本月日记
- 收件箱孤儿 (无 outlinks)
- 领域关联
- 评分 review (score < 0.6 待重审)
- 记忆 L2 候选
- 最近 7 天活跃 (file.mtime)
- TASK 滚动 (未完成 tasks)

每条含 use case + DQL + 输出预览。

## Acceptance Criteria

- [ ] `plugins/tools/cortex/skills/cortex-dataview/SKILL.md` 存在, ≤ 80 行 (frontmatter 计入)
- [ ] `references/{dql-syntax,dataviewjs-api,integration-patterns,modify-flow,cookbook}.md` 全 5 文件存在
- [ ] SKILL.md description 池能触发 (claude --settings glm-4.7-flash 验证)
- [ ] README + Skills 详解.md + AGENT.md skill 表加 cortex-dataview 行 (skill 18 → 19)
- [ ] memory cortex-plugin + MEMORY.md 计数同步
- [ ] .version bump

## Decision (ADR-lite)

**Context**: 用户要求 Dataview skill, 但 cortex vault 现用 `<!-- DASH:BEGIN/END -->` 自定义 marker, 非 Dataview。

**Decision**:
1. 新 skill 与现有 dashboard 系统**共存**, 不替换
2. AUTO_MODE 默认只生成 DQL, 不生成 dataviewjs (任意 JS 安全风险)
3. 修改流程用 marker `<!-- cortex-dataview v<N> kind=<kind> hash=<sha1> -->` 实现幂等
4. 不写 CLI 脚本 (无 ingest/generate 自动化必要), 纯 skill 形态
5. references 5 文件 (3 来自 research + 2 新写) ≥ 1100 行总深度

**Consequences**:
- + 用户两套 marker 系统并存清晰
- + 安全默认: dataviewjs 必须显式批准
- - 无自动检测 dataview 块的 CLI, 用户依赖 AI 调 skill

## Out of Scope

- 自动批量生成 vault 所有页面的 dataview 块
- Dataview 插件本身的安装 (用户先装)
- Bases (Obsidian 1.7+) 集成 (已在 cortex-cartographer / cortex-dashboard 体系)
- DataviewJS 安全沙箱 (本 skill 仅生成代码, 不执行)

## Technical Notes

- research 三件套已写完, 参考 `research/{dql-syntax,dataviewjs-api,integration-patterns}.md` (~1100 行)
- 复用 cortex skill 多文件模式: SKILL.md 入口 + references/ 按需加载 (参考 cortex-image-understand / cortex-video-understand 结构)
- skill description ≤ 220 字符, 自动触发池总长 ≤ 1500 字符约束
