# 开发规范

Python 插件遵循的开发规范和最佳实践。

## 编程规范

### 必须遵守

1. **风格指南**：遵循 PEP 8 规范
2. **类型提示**：使用 PEP 484 类型提示
3. **文档字符串**：使用 PEP 257 文档字符串
4. **命名规范**：遵循 Python 命名约定

### 推荐实践

1. **现代 Python**：使用 Python 3.8+ 特性
2. **uv 管理**：使用 uv 进行依赖管理
3. **src 布局**：使用 src/ 目录结构
4. **pytest 测试**：使用 pytest 测试框架

## 代码风格

### 格式化

```bash
# 使用 ruff 格式化
ruff format .

# 使用 ruff 检查
ruff check .
```

### 导入顺序

```python
# 标准库
import os
import sys
from typing import Optional

# 第三方库
import requests
from fastapi import FastAPI

# 本地模块
from mypackage import core
from mypackage.utils import helper
```

### 文档字符串

```python
def calculate_sum(numbers: list[int]) -> int:
    """计算数字列表的和.

    Args:
        numbers: 整数列表.

    Returns:
        列表中所有数字的和.

    Raises:
        ValueError: 如果列表为空.

    Example:
        >>> calculate_sum([1, 2, 3])
        6
    """
    if not numbers:
        raise ValueError("列表不能为空")
    return sum(numbers)
```

## 项目结构

### 标准结构

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
├── README.md
└── .gitignore
```

### pyproject.toml

```toml
[project]
name = "mypackage"
version = "0.1.0"
description = "My package"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 测试规范

### 测试命名

```python
# 测试文件：test_module.py
# 测试类：TestClassName
# 测试方法：test_function_name
```

### 测试结构

```python
import pytest

class TestFeature:
    """功能测试."""

    @pytest.fixture
    def setup(self):
        """测试准备."""
        return {}

    def test_normal_case(self, setup):
        """正常情况测试."""
        pass

    def test_edge_case(self, setup):
        """边界情况测试."""
        pass

    def test_error_case(self, setup):
        """错误情况测试."""
        with pytest.raises(ValueError):
            raise ValueError("error")
```

### 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 依赖管理

### 使用 uv

```bash
# 初始化项目
uv init

# 添加依赖
uv add requests

# 添加开发依赖
uv add --dev pytest

# 安装所有依赖
uv sync

# 运行脚本
uv run python -m mypackage
```

## 性能优化

### 性能测量

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.3f}s")

with timer("process"):
    process_data()
```

### 常见优化

1. **使用生成器**：避免创建大列表
2. **使用内置函数**：比手写循环快
3. **使用缓存**：`@functools.lru_cache()`
4. **使用异步**：I/O 密集型任务

## 安全规范

### 输入验证

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    name: str
    age: int

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be empty')
        return v
```

### 敏感数据处理

```python
import os
from typing import Optional

def get_api_key() -> str:
    """从环境变量获取 API 密钥."""
    key = os.environ.get('API_KEY')
    if not key:
        raise ValueError('API_KEY not set')
    return key
```
