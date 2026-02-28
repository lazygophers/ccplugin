# 快速开始

Python 插件快速入门指南。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market
```

## 初始化新项目

### 1. 创建项目

```bash
# 使用 uv 创建项目
uv new my-project
cd my-project

# 或手动创建
mkdir my-project && cd my-project
uv init
```

### 2. 配置项目

编辑 `pyproject.toml`：

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My Python project"
requires-python = ">=3.11"

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 3. 创建目录结构

```bash
mkdir -p src/mypackage tests
touch src/mypackage/__init__.py
touch tests/__init__.py
```

## 开发流程

### 创建模块

```python
# src/mypackage/core.py
"""核心模块."""
from typing import Optional


class Calculator:
    """计算器类."""

    def add(self, a: int, b: int) -> int:
        """加法运算.

        Args:
            a: 第一个数
            b: 第二个数

        Returns:
            两数之和
        """
        return a + b

    def divide(self, a: int, b: int) -> Optional[float]:
        """除法运算.

        Args:
            a: 被除数
            b: 除数

        Returns:
            商，如果除数为0则返回None
        """
        if b == 0:
            return None
        return a / b
```

### 编写测试

```python
# tests/test_core.py
import pytest
from mypackage.core import Calculator


class TestCalculator:
    """计算器测试."""

    @pytest.fixture
    def calc(self):
        return Calculator()

    def test_add(self, calc):
        """测试加法."""
        assert calc.add(1, 2) == 3
        assert calc.add(-1, 1) == 0

    def test_divide(self, calc):
        """测试除法."""
        assert calc.divide(6, 2) == 3.0
        assert calc.divide(1, 0) is None

    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
    ])
    def test_add_parametrized(self, calc, a, b, expected):
        """参数化测试."""
        assert calc.add(a, b) == expected
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_core.py

# 运行并显示覆盖率
uv run pytest --cov=src --cov-report=term-missing
```

## 使用代理

### 开发新功能

```
请帮我实现一个用户管理模块，支持 CRUD 操作
```

Python 开发专家会：
1. 设计模块结构
2. 实现核心功能
3. 添加类型提示
4. 编写文档字符串

### 编写测试

```
为用户管理模块编写完整的测试用例
```

测试专家会：
1. 设计测试策略
2. 编写单元测试
3. 添加边界测试
4. 确保覆盖率

### 调试问题

```
程序在并发请求时出现数据竞争问题
```

调试专家会：
1. 分析问题原因
2. 定位问题代码
3. 提供修复方案
4. 添加防护措施

## 常用命令

```bash
# 格式化代码
uv run ruff format .

# 检查代码
uv run ruff check .

# 运行测试
uv run pytest

# 类型检查
uv run mypy src/

# 运行项目
uv run python -m mypackage
```

## 下一步

- 阅读 [开发规范](standards.md) 了解详细规范
- 查看 [技能系统](skills.md) 学习各种技能
- 参考 [代理系统](agents.md) 了解代理能力
