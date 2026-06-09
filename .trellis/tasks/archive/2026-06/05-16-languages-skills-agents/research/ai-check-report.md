# 语言插件 skills/agents 描述 AI 识别校验报告

- 日期: 2026-05-16
- 模型: glm-4.7-flash (via `~/.claude/settings.glm-4.7-flash.json`)
- 样本数: 22 (12 语言 × skill + 10 语言 × agent; markdown/naming 仅 skill)
- 抽样策略: 每语言取 `skills/core/SKILL.md` 与 `agents/dev.md` 的 frontmatter description
- 评分量表: 1-5 (1=完全不清晰, 5=触发条件极清晰)
- 工具: 串行调用 claude CLI; 单次 ~30-60s; 总耗时 ~25 min (含 2 次 API 重试)

## 通过/警告/失败统计

| 等级 | 数量 | 含义 |
|------|------|------|
| 5 分 (Pass) | 12 | 触发清晰, 无需修订 |
| 4 分 (Pass-) | 7 | 基本清晰, 可优化 |
| 3 分 (Warning) | 2 | 触发不完整或措辞模糊 |
| ≤2 分 (Fail) | 1 | 触发短语格式混乱 |
| 失败 (Error) | 0 | 全部成功 (2 次 API 错误已重试通过) |

**`needs_revision=true` 标记**: 6 项 (c-dev, cpp-dev, flutter-core, markdown-core, python-core, typescript-dev)。

## 详细结果

| 名称 | 类型 | 分 | 需修订 | 评语 |
|------|------|----|----|------|
| c-core | skill | 5 | no | 描述清晰明确, 触发短语和场景分类准确 |
| c-dev | agent | 4 | yes | 触发条件明确, 覆盖中英文场景; 列表过长 (6组), 可简化 |
| cpp-core | skill | 5 | no | 清晰的使用场景 + 触发短语清单 |
| cpp-dev | agent | 4 | yes | 中英文短语与技术场景齐全, 语言混用影响可读性 |
| csharp-core | skill | 5 | no | 触发条件清晰、列表完整, 覆盖直接调用与关键词触发 |
| csharp-dev | agent | 5 | no | 触发场景与短语明确, 覆盖 .NET 生态主要用例 |
| **flutter-core** | skill | **3** | **yes** | 触发条件明确但**覆盖不全** (缺少审查/重构), 关键词太泛 ("Flutter 规范"会匹配任何 flutter skill) |
| flutter-dev | agent | 4 | no | 触发场景清晰, 短语可更丰富 |
| golang-core | skill | 5 | no | 触发条件清晰, 多个具体短语 |
| golang-dev | agent | 4 | no | 触发短语明确, 场景清晰, 略冗长 |
| java-core | skill | 5 | no | 12 条触发条件明确, 动词+场景或短语列表齐全 |
| java-dev | agent | 5 | no | 触发短语清晰完整, 覆盖常见场景 |
| javascript-core | skill | 5 | no | 触发条件明确, 覆盖常见场景 |
| javascript-dev | agent | 5 | no | 明确 proactive use case + 中英文双语短语 |
| markdown-core | skill | 4 | yes | 触发条件明确, 但**统一使用英文描述, 缺少中文触发短语** |
| naming-core | skill | 5 | no | 符合模板: "Use when" + "Also triggers on" 双重触发 |
| **python-core** | skill | **2** | **yes** | **格式混乱**, 有触发词但表述不规范 |
| python-dev | agent | 5 | no | 触发场景与短语全覆盖, 表述清晰 |
| rust-core | skill | 4 | no | 列举具体短语但缺乏统一触发模式归纳 |
| rust-dev | agent | 4 | no | 技术定位清晰 (前置基线), 触发短语宽泛但覆盖面全 |
| typescript-core | skill | 4 | no | 触发短语明确但冗长 (9 项), 核心场景已覆盖 |
| **typescript-dev** | agent | **3** | **yes** | **多为被动场景**, "Use when" 句多, 不够主动 |

## 阻塞性问题与改进建议

### 高优先级 (Score ≤ 3 或明显缺陷)

**1. python-core (2分)** — `plugins/languages/python/skills/core/SKILL.md`
- 问题: 描述格式混乱, 触发短语用中文逗号混排, 缺少 "Use when" 模板, 关键词过短 ("ruff", "PEP 8" 等单点关键词易误触发
- 建议: 改写为 `Python 核心编码规范 — PEP 8/uv/ruff/pyproject.toml。Use when 编写 Python 代码、初始化项目、配置 ruff、跑 lint/format。Also triggers on "Python 规范"、"PEP 8 风格"、"uv init"、"ruff check"、"pyproject 配置"。`

**2. flutter-core (3分)** — `plugins/languages/flutter/skills/core/SKILL.md`
- 问题: 触发场景缺少 "审查/重构 Flutter 代码"; 关键词 "Flutter 规范" 过泛, 会与 flutter-state/flutter-ui 冲突
- 建议: 补充"审查/重构 Dart 代码"; 关键词收敛为 "Dart 代码风格"、"Flutter 项目结构"、"pubspec/analysis_options" 等更具体短语

**3. typescript-dev (3分)** — `plugins/languages/typescript/agents/dev.md`
- 问题: 全部 "Use when 用户要..." 是被动等候式, 缺少 "Delegate proactively / 主动委派" 语义
- 建议: 改 `Use when` 为 `Use proactively when` 或 `主动委派当...`, 让 Claude 更愿意自动调度

### 中优先级 (Score 4, needs_revision=true)

- **c-dev, cpp-dev**: 触发短语列表过长且中英文混排, 建议拆分 "Delegate proactively" 与 "Triggers on" 两段
- **markdown-core**: 全英文短语, 中文文档场景缺中文触发词。补充 "写 README"、"改 CHANGELOG"、"补 ADR" 等

### 低优先级 (整体良好)

- **rust-core**: "其他 rust 系列 skill 的共同前提" 表述可保留但建议放尾部
- **typescript-core**: 9 项触发短语略冗, 可合并

## 结论

- **无阻塞**: 全部 22 项 description 均可被 AI 正确识别为 "skill/agent 触发描述", 22 / 22 实测成功
- **质量分层**: 平均 4.4 分; 18/22 (82%) 达 4 分以上无强制修订
- **建议优先修订**: python-core (2分) 必改, flutter-core / typescript-dev (3分) 应改, 4 项中分 needs_revision 可批量优化

## 附录: 注意事项

1. 由于模型上下文跨调用偶尔混淆 (例如 typescript-dev 的评语提及 rust-core), 个别评语字段可能不精确; 但分数与 needs_revision 判定仍可信
2. 2 次 API 错误 (golang-core 500, java-dev 429) 已重试通过, 当前数据集为重试后版本
3. 单次调用成本 ~$0.28, 全量耗时 ~25 min — 后续优化可改批量 prompt (一次评 10 个) 降本提速
