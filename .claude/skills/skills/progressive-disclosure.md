# 渐进披露模式

## 核心理念

渐进披露（Progressive Disclosure）是 Skills 的**核心架构模式**：

> Claude 根据需要分阶段加载信息，而不是预先消耗上下文。

## 三个级别

### 级别 1：元数据（始终加载）

**目的**：技能发现

**内容**：YAML frontmatter

```yaml
---
name: explain-code
description: Explains code with visual diagrams...
---
```

**Token 消耗**：~100 tokens per skill

**加载时机**：启动时加载到系统提示

### 级别 2：指令（触发时加载）

**目的**：行为指导

**内容**：SKILL.md 主体

```markdown
# Explain Code

When explaining code:
1. Start with an analogy
2. Draw a diagram
3. Walk through step-by-step
```

**Token 消耗**：~5k tokens（SKILL.md 主体）

**加载时机**：技能被调用时通过 `bash` 读取

### 级别 3：资源（按需加载）

**目的**：详细参考

**内容**：支持文件（脚本、参考文档等）

```
skill/
├── SKILL.md
├── FORMS.md              # 额外参考
├── templates/
│   └── report.md        # 模板
└── scripts/
    └── validate.py        # 脚本
```

**Token 消耗**：实际上无限制

**加载时机**：仅在被引用时加载

## 路径变量

所有路径使用 `${CLAUDE_PLUGIN_ROOT}` 变量：

```markdown
# ✅ 正确
详细指南见 [reference.md](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/reference.md)
模板见 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/skill-name/templates/template.md)

# ❌ 避免
详细指南见 [reference.md](../../reference.md)
模板见 [../templates/template.md](./templates/template.md)
```

## 引用模式

### 从 SKILL.md 引用

```markdown
# Skill Name

## Quick Reference

- Topic 1: [topic.md](topic.md)
- Topic 2: [detailed-guide.md](detailed-guide.md)

## Full Documentation

See the complete guide in [reference.md](reference.md)
```

### 引用支持文件

```markdown
## Forms

For form filling best practices, see [FORMS.md](FORMS.md).

## Scripts

Claude can execute the validation script:
```bash
bash scripts/validate.py
```
```

## 加载流程

```
1. 启动
   ↓
2. 加载元数据（name + description）
   ↓
3. 用户请求匹配 description
   ↓
4. 通过 bash 读取 SKILL.md
   ↓
5. Claude 执行技能指令
   ↓
6. 如引用支持文件，通过 bash 读取
   ↓
7. 返回结果
```

## 优势

| 优势 | 说明 |
|------|------|
| **按需访问** | Claude 只读取相关文件 |
| **高效执行** | 脚本代码不进入上下文 |
| **无限制捆绑** | 支持大量参考材料 |
| **结构清晰** | 主文件简洁，详细信息分离 |

## 规范要点

1. **保持 SKILL.md 简洁**
   - 提供概览和导航
   - 不要超过 500 行

2. **详细参考移至支持文件**
   - API 文档 → reference.md
   - 示例 → examples.md
   - 模板 → templates/

3. **清晰的文件命名**
   - 使用描述性名称
   - 保持一致性

4. **使用路径变量**
   - 所有路径使用 `${CLAUDE_PLUGIN_ROOT}`
   - 避免相对路径

## 示例：完整 Skill

```
explain-code/
├── SKILL.md              # 300行，包含快速参考和导航
├── analogies.md           # 比喻示例
├── diagram-templates/
│   ├── flowcharts.md
│   └── sequence-diagrams.md
└── scripts/
    └── generate-diagram.py

# SKILL.md 引用：
# - 详细比喻见 [analogies.md](analogies.md)
# - 模板见 [flowcharts.md](diagram-templates/flowcharts.md)
```
