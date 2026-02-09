---
name: skill-name
description: 技能用途简述 - 说明这个技能做什么和什么时候使用。当用户需要[XX功能]或遇到[XX问题]时自动激活。支持[XX操作]。
---

# Skill Name

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、优先级速览 | 快速入门 |
| [reference.md](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md) | 完整配置参考 | 详细实现 |
| [examples.md](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/examples.md) | 使用示例 | 代码示例 |

## 核心原则

**必须遵守**：

1. 使用 `${CLAUDE_PLUGIN_ROOT}` 引用路径
2. Skill 采用渐进披露模式
3. 所有配置使用 YAML frontmatter

**禁止行为**：

- 使用相对路径（如 `../../xxx.md`）
- 硬编码绝对路径

## 路径引用规范

```markdown
# ✅ 正确
[参考文档](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md)
[示例代码](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/examples.md)

# ❌ 禁止
[参考文档](../../skill-name/reference.md)
[示例代码](./examples.md)
```

## 目录结构

```
skill-name/
├── SKILL.md                   # 主入口（必需）
├── reference.md              # 详细参考（可选）
└── examples.md               # 使用示例（可选）
```

## Frontmatter 格式

```yaml
---
name: skill-name              # 技能标识（小写+连字符）
description: 简短描述          # 1-2 句话说明用途

# 可选字段
context: fork                # fork 或 inherit
agent: agent-name            # 关联的 Agent
---
```

## 相关资源

- [详细参考](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md)
- [使用示例](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/examples.md)
