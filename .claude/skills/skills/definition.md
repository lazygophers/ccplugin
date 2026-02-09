# Skills 定义

## 什么是 Skill

Skill 是**扩展 Claude Code 功能的模块化能力**：

### 与 Commands/Agents 的区别

| 类型 | 用途 | 触发方式 |
|------|------|----------|
| **Skill** | 指导行为规范 | 自动或 `/skill-name` |
| **Command** | 执行特定命令 | `/command` |
| **Agent** | 执行复杂任务 | `@agent` |

### 价值主张

**为什么使用 Skills：**

- **专业化**：将通用 Claude 转变为领域专家
- **复用性**：一次创建，多次使用
- **组合性**：Skills 可组合构建复杂工作流
- **上下文感知**：Claude 自动在相关时使用

## 三级内容架构

### 级别 1：元数据（始终加载）

**YAML Frontmatter**：

```yaml
---
name: explain-code
description: Explains code with visual diagrams. Use when user asks "how does this work?"
---
```

Claude 在启动时加载，用于**技能发现**。

### 级别 2：指令（触发时加载）

**SKILL.md 主体**：

```markdown
# Explain Code

When explaining code:
1. Start with an analogy
2. Draw a diagram
3. Walk through step-by-step
```

Claude 在技能被调用时加载，用于**行为指导**。

### 级别 3：资源（按需加载）

**支持文件**：

```
explain-code/
├── SKILL.md
├── analogy-guide.md
└── diagram-templates/
    └── flowcharts.md
```

Claude 仅在被引用时加载，用于**详细参考**。

## 基于文件系统的架构

Skills 利用 Claude 的**虚拟机环境**：

- Skills 以目录形式存在
- Claude 通过 `bash` 命令访问文件
- 指令从文件系统读取到上下文
- 脚本通过 `bash` 执行，输出进入上下文

### 优势

| 优势 | 说明 |
|------|------|
| **按需访问** | Claude 只读取相关文件 |
| **高效执行** | 脚本代码不进入上下文 |
| **无限制捆绑** | 支持大量参考材料 |

## 使用场景

### 场景 1：编码规范

```yaml
---
name: python-coding
description: Python coding standards for this project
---

# Python Coding Standards

Always use type hints with Python 3.11+
Import order: stdlib → third-party → local
```

### 场景 2：工作流

```yaml
---
name: deploy
description: Deploy application to production
disable-model-invocation: true
---

Deploy steps:
1. Run tests
2. Build application
3. Push to target
4. Verify deployment
```

### 场景 3：专业指导

```yaml
---
name: security-review
description: Security review checklist and guidelines
context: fork
agent: Explore
allowed-tools: Read, Grep
---

Review for security vulnerabilities:
1. Check input validation
2. Verify authentication
3. Test for injection attacks
```
