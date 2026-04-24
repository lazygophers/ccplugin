# Python 插件

> Python 开发插件 - 提供 Python 开发规范、最佳实践和代码智能支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install python@ccplugin-market
```

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
  - **现代 Python** - 充分利用 Python 3.14+ 特性

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

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | Python 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | Python 核心规范 |
| Skill | `error` | 错误处理规范 |
| Skill | `types` | 类型提示规范 |
| Skill | `testing` | 测试策略 |
| Skill | `async` | 异步编程规范 |
| Skill | `web` | Web 开发规范 |

## 使用方式

### 1. 开发专家代理（dev）

用于 Python 代码开发和架构设计。

**用途**：
- 开发新功能
- 设计代码架构
- 优化代码实现
- 解决技术问题

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

**示例**：
```
我的 API 响应时间太长，如何优化性能？
```

## 开发规范

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

## 参考资源

### 官方文档

- [PEP 8 - 风格指南](https://www.python.org/dev/peps/pep-0008/)
- [PEP 484 - 类型提示](https://www.python.org/dev/peps/pep-0484/)
- [Python 文档](https://docs.python.org/)

### 工具文档

- [pytest 文档](https://docs.pytest.org/)
- [uv 文档](https://docs.astral.sh/uv/)
- [mypy 文档](https://mypy.readthedocs.io/)

## 许可证

AGPL-3.0-or-later
