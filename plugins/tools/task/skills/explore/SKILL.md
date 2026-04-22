---
description: 项目上下文探索。当用户需要了解项目结构、分析代码架构或为任务收集上下文时触发，定位相关模块和文件，推断代码风格与工具链，输出 context.json
memory: project
color: orange
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: true
effort: medium
context: fork
agent: task:explore
argument-hint: [任务描述或探索目标]
---

# Explore Skill

目标导向的渐进式探索，聚焦任务相关上下文。**只读分析，不修改项目代码。**

**项目范围**：所有文件搜索和读取必须限定在 `project_root` 目录内（由 flow 传入，独立调用时为 `$(pwd)`）。

## 独立调用模式

当用户直接调用 `/task:explore` 时（无 flow 上下文）：

1. 从用户输入生成中文 task_id（≤10 字符）
2. 执行 `task update {task_id} --status=explore` 创建任务
3. 按下方探索策略执行
4. 将 context.json 写入 `.lazygophers/tasks/{task_id}/context.json`
5. 输出探索结果摘要

当由 flow 调用时：直接使用传入的 task_id 和 environment 参数。

## 探索策略

按优先级依次执行，每个阶段完成后评估是否已有足够信息：

### 阶段1：任务相关性定位

从用户输入（user_prompt 或 align_feedback）中提取关键术语（模块名、函数名、技术概念），使用以下工具定位相关代码：

- **Grep**：搜索关键术语在代码中的出现位置（`output_mode="files_with_matches"`）
- **Glob**：按文件模式定位模块（如 `src/**/*.py`、`lib/**/*.ts`）
- **Read**：读取定位到的关键文件，理解其结构和职责

**产出**：相关模块列表、关键文件路径列表

### 阶段2：依赖关系与架构

对阶段1发现的文件，分析其上下游关系：

- 读取 import/require/include 语句，追踪依赖链
- 识别入口点（main、handler、route）和调用链
- 理解数据流向（输入→处理→输出）

**产出**：依赖关系图（哪些模块依赖哪些模块）、调用链关键节点

### 阶段3：代码风格与约定

从阶段1的文件中采样 3-5 个代表性文件，推断项目约定：

| 维度 | 检测方法 | 示例输出 |
|------|---------|---------|
| 命名约定 | 观察函数/变量/类的命名模式 | `snake_case for functions, PascalCase for classes` |
| 缩进风格 | 观察缩进字符和宽度 | `4 spaces` |
| 导入模式 | 观察 import 语句的组织方式 | `absolute imports, stdlib → third-party → local` |
| 错误处理 | 观察 try/except 和异常类型 | `custom exceptions in errors.py, logging on catch` |
| 测试风格 | 观察测试文件的组织和命名 | `pytest, test_ prefix, fixtures in conftest.py` |
| 文档风格 | 观察注释和 docstring 格式 | `Google style docstrings` |

**产出**：code_style 字典

### 阶段4：项目配置与工具链

快速扫描项目根目录的配置文件：

- 构建工具：`package.json`、`pyproject.toml`、`Makefile`、`Cargo.toml` 等
- Lint/格式化：`.eslintrc`、`ruff.toml`、`.prettierrc` 等
- 测试框架：`pytest.ini`、`jest.config.*`、`vitest.config.*` 等
- CI/CD：`.github/workflows/`、`.gitlab-ci.yml` 等

**产出**：可用的验证命令（lint、test、build）

## 返回标准

探索完成后，必须写入 `context.json`，结构如下：

```json
{
  "task_related": {
    "modules": ["模块A", "模块B"],
    "files": ["src/auth/login.py", "src/auth/middleware.py"],
    "dependencies": {"login.py": ["middleware.py", "models/user.py"]},
    "entry_points": ["src/main.py:app"],
    "patterns": ["认证使用 JWT", "所有路由经过 middleware"]
  },
  "code_style": {
    "naming": "snake_case for functions, PascalCase for classes",
    "indentation": "4 spaces",
    "imports": "absolute imports, isort grouping",
    "error_handling": "custom AppError hierarchy, logging on catch",
    "testing": "pytest, fixtures in conftest.py",
    "documentation": "Google style docstrings"
  },
  "toolchain": {
    "language": "Python 3.11",
    "package_manager": "uv",
    "lint_command": "ruff check .",
    "test_command": "pytest",
    "build_command": "uv build"
  },
  "last_updated": "2026-04-13T10:00:00"
}
```

### 必需字段

| 字段 | 要求 |
|------|------|
| `task_related.modules` | ≥1 个相关模块 |
| `task_related.files` | ≥1 个关键文件路径 |
| `code_style.naming` | 非空，明确的命名约定 |
| `code_style.indentation` | 非空，明确的缩进风格 |
| `last_updated` | ISO 8601 时间戳 |

### 可选字段

`dependencies`、`entry_points`、`patterns`、`toolchain` — 有则填，无则省略。

## 增量更新

如果已有 context.json（从之前的探索中），执行增量更新：
- 列表字段（modules、files）：合并去重
- 标量字段（naming、indentation）：用最新值覆盖
- 保留旧数据中新探索未涉及的字段

## 检查清单

- [ ] 关键文件已定位并读取
- [ ] 代码风格已从实际文件中推断（非猜测）
- [ ] context.json 已写入且符合返回标准
- [ ] 增量更新已处理（如有旧数据）
