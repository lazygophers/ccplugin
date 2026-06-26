# 维度 6：工具链与验证机制

> 本项目可用的 skill 编写/优化/验证工具链。

## 来源清单

| # | 工具 | 路径/命令 | 用途 |
|---|------|---------|------|
| A | darwin-skill | ~/.claude/skills/darwin-skill/ | 9 维自主优化器 |
| B | grill-me / grilling | ~/.claude/skills/grill-me/ | red-team 反拷问 |
| C | skill-creator | `/plugin install skill-creator@claude-plugins-official` | 官方 eval 自动化 |
| D | nuwa（huashu-nuwa） | ~/.claude/skills/huashu-nuwa/ | 主题/人物蒸馏（本产物母流程） |
| E | 项目质量检查规范 | CLAUDE.md | `claude -p` stream-json 质检 |

## A. darwin-skill（自主优化器）

### 能力

9 维 rubric + validation-gated 棘轮 + 独立 judge agent + 人审 checkpoint。

### 对产物的可用方式

产物编写完成后，可用 darwin-skill 跑一轮自主优化：
- 9 维打分找最弱项
- HL-1~4 high-leverage 操作建议
- validation-gated keep/revert
- 触顶即停

### 关键产出格式

results.tsv（timestamp/commit/skill/old_score/new_score/status/dimension/note/eval_mode），`.darwin-results.tsv`（本项目内存于 plugins/tools/trellisx/，见 memory [[darwin-trellisx-optimization]]）。

## B. grill-me（反拷问）

147B wrapper，调 `/grilling` 做 red-team。产物设计完成后，用 grill-me 反拷问：
- 框架是否有漏洞？
- 检查点是否足够？
- 反模式覆盖是否充分？
- 诚实边界是否真实？

用户原始请求明确提到 `/grile-me`（grill-me），意图是在产物验证阶段做反拷问。

## C. skill-creator（官方 eval）

自动化 A/B 对比循环：
- test case → evals/evals.json
- 隔离子代理跑
- grading.json + benchmark.json
- 版本盲测 A/B
- description 调优（should-trigger / should-not-trigger）

产物应指向此工具作为 eval 验证手段。

## D. nuwa（母流程）

本产物由 nuwa Phase 0~5 生成（主题 skill 变体）。产物定位 = nuwa 的子能力（专门做 skill/agent 创建方法论），但 nuwa 是人物/主题蒸馏器，功能工作流 skill 须手写（见 memory [[huashu-nuwa-persona-only]]）。所以产物走 nuwa 的调研/提炼/检查点流程，但最终 SKILL.md 是功能型（框架概览+流派对比），非角色扮演型。

## E. 项目质检命令

CLAUDE.md 规定：commands/skills/agents/agent.md 优化须通过：

```bash
claude -p "<待测试内容>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

产物完成后须跑此命令验证 AI 能正确理解识别。

## 验证流水线设计

产物完成后建议验证顺序：

1. **结构自检**（本产物内置 checklist）：frontmatter 合规、description 前置 key use case、≤500 行、引用一层深、反例黑名单成章。
2. **AI 理解质检**：项目 `claude -p` 命令验证可发现性。
3. **grill-me 反拷问**：red-team 框架漏洞。
4. **darwin-skill 9 维评分**（可选）：找最弱维度迭代。
5. **skill-creator eval**（可选）：A/B 对比 with vs without skill。

## 产物框架应用点

本维度定义产物的：
- **验证 section**（指向 darwin-skill / skill-creator / grill-me）
- **自检 checklist**（内置，不依赖外部工具即可跑）
- **诚实标注**（哪些验证已做、哪些推荐用户自跑）
