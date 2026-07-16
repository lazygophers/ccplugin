# 维度 3：社区高质量生态（plugin / skill 仓库）

> 二手但高信号：展示社区已验证的 skill 组织模式与最佳实践。

## 来源清单

| # | 来源 | URL | 类型 |
|---|------|-----|------|
| A | awesome-claude-skills | https://github.com/travisvn/awesome-claude-skills | 社区策展 |
| B | Anthropic 官方 17 skills | https://github.com/anthropics/skills | 官方一手 |
| C | superpowers plugin | `/plugin install superpowers@claude-plugins-official` | 官方市场 |
| D | skill-creator plugin | 同上 | 官方市场 |
| E | alchaincyf 生态（nuwa/darwin-skill） | https://github.com/alchaincyf | 社区（开源自查） |
| F | superpowers-writing-skills | https://www.atcyrus.com/skills/superpowers-writing-skills | 社区 |

## 高质量 skill 仓库模式总结

### 共性结构

1. **SKILL.md + references/*.md 多文件**（非单文件）。SKILL.md ≤500 行，细节拆引用。
2. **evals/ 目录**：成熟 skill 带 evals.json 做回归。
3. **plugin 打包**：跨仓库共享打成 `.claude-plugin/plugin.json` + skills/ + agents/ + hooks/。
4. **README 独立于 SKILL.md**：README 给人看（安装/用途），SKILL.md 给 Claude 看（指令/触发）。

### Anthropic 官方 17 skills（B）

GitHub anthropics/skills 是官方标杆。讨论区高频问题：
- frontmatter YAML 缩进/引号错误 → skill 不被检测（[讨论 #244](https://github.com/anthropics/skills/discussions/244)）
- 路径错误 / skill 孤立 / 命令冲突 → 静默失败

### alchaincyf 生态（E，本地一手）

nuwa（女娲造人术）+ darwin-skill 是本项目产物的一手参照。模式：
- 重流程（Phase 0~5）而非重知识
- 检查点驱动（Phase 1.5 / 2.5 / 4）
- 反模式显式编码（信息源黑名单、绝对不做的事）
- 自包含（references/ 全部内嵌，复制即用）

### superpowers（C）

社区最广泛使用的功能型 plugin。Reddit 多帖提及「feature development 大部分时间靠 superpowers」。其 writing-skills 子能力（F）专门教写新 skill——证明「meta-skill」是社区已验证品类。

## 社区共识最佳实践（跨源汇总）

| 实践 | 来源 | 一致性 |
|------|------|--------|
| SKILL.md ≤500 行 | 官方 + 全社区 | 全一致 |
| description 前置 key use case | 官方 + Charlie O'Brien 反模式 | 全一致 |
| 多文件 progressive disclosure | 官方 + awesome 列表 | 全一致 |
| eval-driven | 官方 skill-creator + darwin-skill | 全一致 |
| 反例黑名单 | darwin-skill + nuwa | 高度一致 |
| 检查点 / 人审 gate | darwin-skill + nuwa | 高度一致 |
| runtime 中立（Agent Skills 开放标准） | darwin-skill + 官方 | 一致 |

## 产物框架应用点

本维度验证产物定位（meta-skill 是已验证品类）、命名（skill-author 与社区命名风格一致）、多文件结构（与 awesome 列表中高质量 skill 一致）、分发（plugin 打包可选）。
