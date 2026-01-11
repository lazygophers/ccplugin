# Python 插件

Python 开发插件提供高质量的 Python 代码开发指导和专业支持。包括遵循 PEP 8 规范的编程指导和行业最佳实践。

## 功能特性

### 🎯 核心功能

- **Python 开发专家代理** - 提供专业的 Python 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 异步编程支持

- **开发规范指导** - 完整的 Python 开发规范
  - **PEP 8 规范** - 遵循 Python 官方编码规范
  - **类型提示指导** - 使用 PEP 484 类型提示
  - **现代 Python** - 充分利用 Python 3.8+ 特性

- **测试与性能** - 全面的测试和优化支持
  - pytest 单元测试框架
  - 性能分析和优化
  - 内存和 CPU 优化
  - 并发编程支持

- **调试工具** - 专业的调试和问题诊断
  - 异常追踪和分析
  - 性能瓶颈识别
  - 内存泄漏检测
  - 并发问题诊断

## 安装

### 前置条件

1. **Python 版本**
   - 需要 Python 3.8+（推荐 3.9+）

2. **依赖管理工具**
   - 使用 uv 进行依赖管理和项目初始化
   - 简单安装：`pip install uv`

3. **Claude Code 版本**
   - 支持插件功能的 Claude Code 版本

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude plugin install /path/to/plugins/python

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/python ~/.claude/plugins/
```

## 使用方式

### 1. 开发专家代理（dev）

用于 Python 代码开发和架构设计。

**用途**：
- 开发新功能
- 设计代码架构
- 优化代码实现
- 解决技术问题

**调用**：使用 Claude Code 的 `@python-dev` 或在聊天中请求 Python 开发帮助

**示例**：
```
我需要实现一个用户管理系统。能帮我设计架构和编写代码吗？
```

### 2. 测试专家代理（test）

用于编写和优化 Python 测试用例。

**用途**：
- 设计测试策略
- 编写单元测试
- 编写集成测试
- 提高测试覆盖率

**调用**：使用 `@python-test` 或请求测试相关帮助

**示例**：
```
我有一个计算函数，需要编写全面的测试用例。
```

### 3. 调试专家代理（debug）

用于诊断和解决 Python 代码问题。

**用途**：
- 异常诊断和修复
- 性能瓶颈识别
- 内存问题诊断
- 并发问题排查

**调用**：使用 `@python-debug` 或描述遇到的问题

**示例**：
```
程序在处理大文件时内存持续增长，如何诊断和修复？
```

### 4. 性能优化专家代理（perf）

用于 Python 代码的性能分析和优化。

**用途**：
- 性能测量和分析
- 性能瓶颈优化
- 内存优化
- 并发优化

**调用**：使用 `@python-perf` 或请求性能优化帮助

**示例**：
```
我的 API 响应时间太长，如何优化性能？
```

## 开发规范

本插件遵循的核心规范包括：

### 编程规范

- **风格指南**：遵循 PEP 8 规范
- **类型提示**：使用 PEP 484 类型提示
- **命名规范**：
  - 模块：lowercase_with_underscores
  - 类：CapWords
  - 函数：lowercase_with_underscores
  - 常量：UPPERCASE_WITH_UNDERSCORES

### 项目结构

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
├── pyproject.toml
└── README.md
```

### 依赖管理

- 使用 uv 进行项目和依赖管理
- 在 pyproject.toml 中明确指定依赖版本
- 优先使用 Python 标准库
- 定期更新和维护依赖

### 测试标准

- 关键路径测试覆盖率 > 80%
- 使用 pytest 作为测试框架
- 编写清晰的测试用例名称
- 使用 fixtures 和 parametrize 提高测试效率

## 快速开始

### 初始化新项目

```bash
# 使用 uv 创建新项目
uv new my-project
cd my-project

# 添加依赖
uv pip install requests pydantic

# 运行项目
uv run python -m mypackage
```

### 创建第一个模块

```python
# src/mypackage/core.py
"""核心模块."""
from typing import List


def calculate_sum(numbers: List[int]) -> int:
    """计算数字列表的和.

    Args:
        numbers: 整数列表.

    Returns:
        列表中所有数字的和.
    """
    return sum(numbers)
```

### 编写测试

```python
# tests/test_core.py
import pytest
from mypackage.core import calculate_sum


class TestCalculateSum:
    """测试 calculate_sum 函数."""

    def test_normal_case(self):
        """正常情况."""
        result = calculate_sum([1, 2, 3, 4, 5])
        assert result == 15

    @pytest.mark.parametrize("numbers,expected", [
        ([1], 1),
        ([1, 1], 2),
        ([], 0),
    ])
    def test_various_inputs(self, numbers, expected):
        """参数化测试."""
        assert calculate_sum(numbers) == expected
```

### 配置项目

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
version = "0.1.0"
description = "My Python project"
requires-python = ">=3.8"
dependencies = [
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=22.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--cov=src/mypackage", "--cov-report=term-missing"]
```

## 最佳实践

### 1. 代码组织

- 使用 src/ 布局分隔源代码和测试
- 模块名清晰表达功能（core.py、models.py、utils.py）
- 在 __init__.py 中定义公共 API

### 2. 类型提示

- 为所有函数添加参数和返回类型提示
- 使用 Optional[T] 表示可选值
- 使用 List、Dict、Union 等容器类型
- 使用 TypeVar 实现泛型

### 3. 文档和注释

- 编写清晰的模块和函数文档字符串
- 解释为什么而不是是什么
- 为复杂算法和非显而易见的决定添加注释

### 4. 错误处理

- 定义清晰的异常层级
- 捕获具体异常，不要使用 except Exception
- 记录完整的异常信息（exc_info=True）

### 5. 性能

- 优先考虑代码可读性而不是过度优化
- 使用 profiling 工具测量关键部分的性能
- 定期进行基准测试以检测性能回归

## 常见问题

### Q: 如何使用这个插件？

A: 在 Claude Code 中描述你的 Python 开发需求，或使用 @python-dev 等代理标签。插件会自动提供相关的规范指导和最佳实践。

### Q: 支持哪些 Python 版本？

A: 本插件针对 Python 3.8+ 进行优化，推荐使用 Python 3.9 及以上版本以获得更好的类型提示支持。

### Q: 如何处理依赖管理？

A: 使用 uv 进行依赖管理。在 pyproject.toml 中声明依赖，使用 `uv sync` 同步，使用 `uv pip install` 添加新依赖。

### Q: 测试覆盖率的目标是多少？

A: 推荐关键路径 >80%，核心模块 >90%。使用 `pytest --cov` 生成覆盖率报告。

## 参考资源

### 官方文档

- [PEP 8 - 风格指南](https://www.python.org/dev/peps/pep-0008/)
- [PEP 484 - 类型提示](https://www.python.org/dev/peps/pep-0484/)
- [Python 文档](https://docs.python.org/)

### 工具文档

- [pytest 文档](https://docs.pytest.org/)
- [uv 文档](https://docs.astral.sh/uv/)
- [mypy 文档](https://mypy.readthedocs.io/)

### 相关技能

- Python 开发规范 - 完整的编码规范和最佳实践
- 测试策略 - 全面的测试设计指导
- 性能优化 - 性能分析和优化建议

## 反馈与贡献

有任何建议或发现问题，欢迎反馈和贡献！

---

**版本**：0.0.1
**最后更新**：2026-01-10
