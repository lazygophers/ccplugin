---
description: "技能模板 - 创建新技能的标准模板和脚手架。当用户需要新建 Skill、创建技能文件、编写 SKILL.md 或参考技能开发规范时激活。提供目录结构、frontmatter 配置和内容编写示例。"
user-invocable: true
model: sonnet
memory: project
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
description: 简短描述          # 1-2 句话说明用途
user-invocable: true

# 可选字段
context: fork                # fork 或 inherit
---
```

## 相关资源

- [详细参考](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md)
- [使用示例](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/examples.md)
