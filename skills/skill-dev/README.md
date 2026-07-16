# skill-dev 技能分类

Claude 插件与 skill / subagent 开发方法论合集。

| skill | 用途 |
|---|---|
| [skill-dev](skill-dev/) | 创建、维护与 9 维 validation-gated 优化单个 skill / subagent（流程 A 创建 / 流程 B 优化） |
| [plugin-dev](plugin-dev/) | 创建与优化整个 Claude Code 插件（manifest / 组件接线 / hook / marketplace） |

## 路由

- 新建 / 优化单个 skill / agent（结构 / frontmatter / 触发不准 / 质量退化 / 误触发 / 回归）→ skill-dev
- 插件级（搭 plugin.json / 接线组件 / 审查整插件）→ plugin-dev
- 深度自主评分 + 可视化卡片 + 多轮 hill-climbing → darwin-skill
- 人物 / 主题视角蒸馏 → huashu-nuwa
