---
description: "Python核心编码规范与工具链配置。涵盖PEP 8风格、命名约定、代码格式化、uv包管理、ruff检查。适用于编写Python代码、代码风格检查、格式化配置、项目初始化等场景。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Python 核心规范

## 适用 Agents

- **python:dev** - 开发阶段使用
- **python:debug** - 调试时遵守
- **python:test** - 测试代码规范
- **python:perf** - 性能优化时保持规范

## 相关 Skills

- **Skills(python:types)** - 类型系统最佳实践
- **Skills(python:async)** - 异步编程模式
- **Skills(python:error)** - 错误处理和日志
- **Skills(python:testing)** - 测试框架和策略
- **Skills(python:web)** - Web 框架集成

## 核心原则（2024-2025 版本）

### 1. Python 版本要求

- **最低版本**：Python 3.13+（推荐）
- **类型检查**：启用 Python 3.12+ PEP 695 泛型语法
- **性能优化**：利用 Python 3.13 JIT 编译器

### 2. 工具链标准（2024-2025）

**包管理器**：
```bash
# ✅ 优先使用 uv（速度提升 10-100 倍）
uv init my-project
uv add fastapi pydantic

# ⚠️ 不推荐：pip（速度慢）
# ⚠️ 可选：poetry（成熟但慢）
```

**代码格式化和 Lint**：
```bash
# ✅ 推荐：ruff（替代 black + isort + flake8）
ruff format .           # 格式化
ruff check --fix .      # Lint 并自动修复

# ❌ 已过时：black + isort + flake8 组合
```

**类型检查**：
```bash
# ✅ 推荐：mypy strict mode
mypy --strict src/

# ⚠️ 可选：pyright（VS Code 集成）
```

### 3. PEP 8 规范

**必须遵守**：
- ✅ 行长不超过 100 字符（ruff 默认）
- ✅ 缩进使用 4 个空格
- ✅ 使用 UTF-8 编码
- ✅ import 语句分组：标准库 → 第三方 → 本地

**禁止行为**：
- ❌ 单字母变量名（除循环变量 `i`, `j`, `k`）
- ❌ 过长的函数（>50 行）
- ❌ 缺少类型提示
- ❌ 缺少文档字符串

### 4. 命名规范

```python
# 模块名：lowercase_with_underscores
my_module.py

# 包名：lowercase（避免下划线）
mypackage/

# 常量：UPPERCASE_WITH_UNDERSCORES
MAX_RETRIES = 3
DATABASE_URL = "postgresql://..."

# 类名：PascalCase
class UserManager:
    pass

class HTTPClient:  # 缩写保持大写
    pass

# 函数/方法：lowercase_with_underscores
def calculate_total(items: list[int]) -> int:
    pass

# 私有成员：_leading_underscore
def _internal_helper():
    pass

# 类型别名（Python 3.12+）
type UserId = int
type UserName = str
```

### 5. 文档字符串标准

```python
def calculate_average(numbers: list[float]) -> float:
    """计算数字列表的平均值.

    使用标准算术平均值公式：sum(numbers) / len(numbers)

    Args:
        numbers: 浮点数列表，不能为空.

    Returns:
        列表中所有数字的平均值.

    Raises:
        ValueError: 如果列表为空.

    Example:
        >>> calculate_average([1.0, 2.0, 3.0])
        2.0
    """
    if not numbers:
        raise ValueError("列表不能为空")
    return sum(numbers) / len(numbers)
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "这是临时代码，不需要遵循规范" | ✅ 是否所有代码都符合 PEP 8？ |
| "变量名很明显，不需要类型注解" | ✅ 是否所有函数都有类型注解？ |
| "这个函数很简单，不需要 docstring" | ✅ 是否所有公共函数都有 docstring？ |
| "black 已经格式化过了" | ✅ 是否迁移到 ruff format？ |
| "pip 安装很快" | ✅ 是否使用 uv 管理依赖？ |
| "手动管理 import 顺序" | ✅ 是否使用 ruff 自动排序 import？ |

## 工具链配置

### pyproject.toml 最佳实践

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic>=2.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.11.0",
    "ruff>=0.6.0",
]

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ANN",    # flake8-annotations（强制类型注解）
]

ignore = [
    "E501",   # line-too-long（交给 formatter 处理）
    "ANN101", # missing-type-self
]

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
disallow_untyped_defs = true
```

## 质量检查工作流

```bash
# 1. 格式化代码
ruff format .

# 2. Lint 检查并自动修复
ruff check --fix .

# 3. 类型检查
mypy src/

# 4. 运行测试
pytest --cov=src tests/

# 5. 安全检查
bandit -r src/
safety check
```

## 项目结构标准

```
my-project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       ├── models.py
│       └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_core.py
│   └── test_models.py
├── docs/
│   └── api.md
├── pyproject.toml
├── uv.lock           # uv 锁文件
├── README.md
└── .gitignore
```

## 检查清单

### 代码规范
- [ ] 遵循 PEP 8 规范
- [ ] 行长不超过 100 字符
- [ ] 使用 4 个空格缩进
- [ ] import 语句正确分组和排序

### 类型和文档
- [ ] 所有公共函数有类型注解
- [ ] 所有公共函数有 docstring
- [ ] docstring 包含 Args/Returns/Raises
- [ ] 使用 Python 3.12+ 类型语法

### 工具链
- [ ] 使用 uv 管理依赖
- [ ] 使用 ruff format 格式化
- [ ] 使用 ruff check 进行 lint
- [ ] 使用 mypy --strict 类型检查

### 安全性
- [ ] 运行 bandit 安全检查
- [ ] 运行 safety check 依赖漏洞检查
- [ ] 没有硬编码的密钥或密码
