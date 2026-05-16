---
name: python-core
description: Python 核心编码规范与工具链 — PEP 8 风格、命名约定、文件结构、uv 依赖管理、ruff lint/format。Use when 编写 Python 代码、初始化 Python 项目、配置 pyproject.toml、跑 lint/format、审查 Python 风格。Also triggers on "Python 规范"、"PEP 8 风格"、"uv init"、"ruff check"、"pyproject 配置"、"Python project setup"。
---

# Python 核心规范 (2026)

适用于 Python 3.13/3.14 项目。所有新建/修改的 .py 文件都应遵守。

## 工具链 (Astral 全家桶)

- **uv** — 依赖与虚拟环境管理 (取代 pip / poetry / pyenv / virtualenv)
- **ruff** — lint + format (取代 flake8 / black / isort / pylint)
- **ty** (Beta, 2026) 或 **pyright** — 类型检查
- **pytest** — 测试框架
- 不要在新项目里引入 pip / poetry / black / isort / flake8

## 项目初始化

```bash
uv init --package my-project
cd my-project
uv add fastapi pydantic httpx
uv add --dev pytest pytest-cov ruff pyright
```

`pyproject.toml` 最小化配置:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.13"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ANN", "SIM", "RUF"]
ignore = ["ANN101", "ANN102"]

[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.13"
```

## 项目结构

src layout 是默认选择 (隔离源码与测试, 防止 import 冲突):

```text
my-project/
├── src/mypackage/
│   ├── __init__.py
│   ├── core.py
│   └── models.py
├── tests/
│   ├── conftest.py
│   └── test_core.py
├── pyproject.toml
└── uv.lock
```

文件 ≤ 500 行 (推荐 200-400 行)。超出就拆模块。

## 命名约定 (PEP 8)

| 类别 | 风格 | 示例 |
|------|------|------|
| 模块/包 | `lowercase` 或 `lower_snake` | `user_service.py` |
| 类/异常 | `CapWords` | `UserManager`, `HTTPClient` (缩写大写) |
| 函数/变量 | `lower_snake_case` | `calculate_total`, `user_id` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| 私有 | 前缀 `_` | `_internal_helper` |
| 类型别名 (PEP 695) | `CapWords` | `type UserId = int` |

## 代码格式

由 `ruff format` 自动处理:

- 行长 100 (项目可调, 但全局一致)
- 双引号字符串
- import 顺序: 标准库 → 第三方 → 本地 (`ruff` 自动排序)
- 函数顶层间 2 空行, 类方法间 1 空行
- 不要手工对齐, 让 formatter 处理

## 文档字符串 (Google 风格)

公共 API 必须有 docstring。私有/内部函数仅在逻辑非显然时写。

```python
def calculate_average(numbers: list[float]) -> float:
    """计算浮点数列表的算术平均值。

    Args:
        numbers: 非空浮点数列表。

    Returns:
        所有数字的算术平均值。

    Raises:
        ValueError: 当列表为空。
    """
    if not numbers:
        raise ValueError("numbers cannot be empty")
    return sum(numbers) / len(numbers)
```

注释只解释 WHY (设计动机), 不解释 WHAT (代码做了什么)。

## 现代 Python 特性 (3.13+)

优先使用:

- `list[int]` / `dict[str, int]` / `tuple[int, ...]` (PEP 585, 不要 `List`/`Dict`)
- `X | None` (PEP 604, 不要 `Optional[X]`)
- `match` 语句替代多层 `if isinstance`
- `type Alias = ...` (PEP 695) 替代 `TypeAlias`
- f-string (日常) 或 t-string (PEP 750, 需要结构化处理时)
- `@dataclass(slots=True)` 替代手写 `__init__`
- 不要再写 `from __future__ import annotations` (PEP 649 默认延迟求值)

## 质量门禁 (提交前)

```bash
uv run ruff check --fix .
uv run ruff format .
uv run pyright          # 或 ty check
uv run pytest -q
```

CI 应同步跑这四条, 任一失败则阻断合并。

## 反模式

- 写 `from typing import List, Dict, Optional` (改用内置泛型 + `|`)
- 用 `os.path` 操作路径 (改用 `pathlib.Path`)
- 用 `print` 调试 (改用 logging / structlog, 见 `python-error`)
- 用 `requests` 同步请求 (改用 `httpx`, 见 `python-async`)
- 用 `setup.py` / `requirements.txt` (改用 `pyproject.toml` + `uv.lock`)
- 全局 `try: ... except Exception:` (只捕获具体异常)
