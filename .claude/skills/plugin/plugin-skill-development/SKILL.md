---
name: plugin-skill-development
description: 插件技能开发指南 - 当用户需要为插件添加 Skills 时使用。覆盖插件技能目录结构、SKILL.md 编写、渐进披露模式和技能注册。
context: fork
agent: skill
---

# 插件技能开发指南

## 技能目录结构

```
skills/
└── skill-name/              # 技能目录（建议小写+连字符）
    ├── SKILL.md             # 技能入口文件（必需）
    ├── topic.md             # 附加文档（可选）
    └── patterns/            # 子目录（可选）
        └── design-patterns.md
```

## SKILL.md 格式

```markdown
---
name: skill-name
description: 技能简短描述
---

# 技能标题

## 快速导航

| 主题 | 内容 | 参考 |
|------|------|------|
| 主题1 | 内容描述 | [file.md](file.md) |

## 详细内容

...
```

### frontmatter 字段

| 字段 | 说明 | 必需 |
|------|------|------|
| `name` | 技能标识（小写+连字符） | 是 |
| `description` | 简短描述（1-2句话） | 是 |

## 渐进披露模式

推荐的多文件结构：

```
python/
├── SKILL.md                 # 入口 + 导航
├── basics.md                # 基础概念
├── advanced.md              # 高级主题
├── patterns/                # 子目录
│   ├── design-patterns.md
│   └── idioms.md
└── examples.md              # 示例集合
```

## 插件中注册技能

在 `plugin.json` 中引用：

```json
{
  "skills": "./skills/"
}
```

技能目录内的 `SKILL.md` 文件会被自动发现。

## 相关技能

- [plugin-development](plugin-development/SKILL.md) - 插件开发
- [plugin-command-development](plugin-command-development/SKILL.md) - 插件命令开发
