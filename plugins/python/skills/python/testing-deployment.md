# Python 测试、依赖管理和最佳实践

## 依赖管理（uv）

### 初始化项目

```bash
# 创建新项目
uv new my-project
cd my-project

# 或在现有项目中初始化
uv init

# 同步依赖
uv sync
```

### 添加和管理依赖

```bash
# 添加生产依赖
uv pip install requests

# 添加开发依赖（使用 --extra dev）
uv pip install --extra dev pytest

# 安装特定版本
uv pip install "requests==2.28.0"

# 安装版本范围
uv pip install "requests>=2.28.0,<3.0.0"

# 显示已安装的包
uv pip list

# 更新包
uv pip install --upgrade requests

# 生成 requirements.txt（如果需要）
uv pip export > requirements.txt
```

### 依赖原则

- ✅ **最小化依赖**：只添加必要的依赖
- ✅ **优先标准库**：优先使用 Python 标准库
- ✅ **明确版本**：在 pyproject.toml 中明确指定版本约束
- ✅ **定期更新**：定期检查和更新依赖，关注安全公告
- ❌ **避免过宽的版本范围**：避免 `requests>=2.0` 这样的宽范围

## pyproject.toml 配置

### 完整项目配置示例

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
version = "0.1.0"
description = "My Python package"
readme = "README.md"
requires-python = ">=3.8"
authors = [
    {name = "Author Name", email = "author@example.com"}
]
keywords = ["python", "example"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]
dependencies = [
    "requests>=2.28.0",
    "pydantic>=1.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=22.0",
    "ruff>=0.1.0",
    "mypy>=0.990",
]

[tool.setuptools]
packages = ["mypackage"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.ruff]
line-length = 88
select = ["E", "F", "W"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--cov=mypackage", "--cov-report=term-missing"]
```

## 测试规范

### 测试结构和最佳实践

```python
# tests/test_core.py
import pytest
from mypackage.core import calculate_average, ValidationError


class TestCalculateAverage:
    """测试 calculate_average 函数."""

    def test_normal_case(self):
        """正常情况."""
        result = calculate_average([1, 2, 3, 4, 5])
        assert result == 3.0

    @pytest.mark.parametrize("numbers,expected", [
        ([1], 1.0),
        ([2, 2], 2.0),
    ])
    def test_various_inputs(self, numbers, expected):
        """参数化测试."""
        assert calculate_average(numbers) == expected

    def test_empty_list_raises_error(self):
        """异常情况."""
        with pytest.raises(ValueError):
            calculate_average([])
```

### 测试覆盖率目标

- **关键路径**：> 80%
- **核心模块**：> 90%
- **工具函数**：> 70%

**运行测试**：

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_core.py

# 显示覆盖率
pytest --cov=mypackage

# 生成 HTML 覆盖率报告
pytest --cov=mypackage --cov-report=html
```

## 最佳实践

### 1. 异常处理

```python
# ✅ 定义清晰的异常层级
class ApplicationError(Exception):
    """应用基异常."""
    pass

class ValidationError(ApplicationError):
    """验证错误."""
    pass

class DataError(ApplicationError):
    """数据错误."""
    pass

# ✅ 捕获具体异常
try:
    process_data(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
except DataError as e:
    logger.error(f"Data error: {e}")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

### 2. 日志最佳实践

```python
import logging

# ✅ 使用模块级别的 logger
logger = logging.getLogger(__name__)

# ✅ 使用结构化日志
logger.info("User login", extra={
    'user_id': user_id,
    'ip': request.ip,
    'timestamp': datetime.now()
})

# ✅ 包含异常信息
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

### 3. 配置管理

```python
from dataclasses import dataclass
from pydantic import BaseSettings

# ✅ 使用 pydantic 管理配置
class Settings(BaseSettings):
    database_url: str
    debug: bool = False
    timeout: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

## 代码质量工具

### Black（代码格式化）

```bash
# 格式化代码
black mymodule.py

# 检查格式（不修改）
black --check mymodule.py
```

### Ruff（快速 linter）

```bash
# 检查代码
ruff check mymodule.py

# 自动修复
ruff check --fix mymodule.py
```

### mypy（类型检查）

```bash
# 检查文件
mypy mymodule.py

# 检查整个项目
mypy .

# 严格模式
mypy --strict mymodule.py
```

## 完成检查清单

在提交代码前，确保满足以下条件：

- [ ] 所有代码符合 PEP 8 规范（使用 black 检查）
- [ ] 所有函数都有类型提示
- [ ] 所有公共 API 都有文档字符串
- [ ] 没有 type checking 错误（mypy strict）
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 没有硬编码的值
- [ ] 代码可读性高，符合 DRY 原则
- [ ] 没有明显的性能问题
- [ ] 异常处理完善
- [ ] 依赖版本已明确指定

## 常见问题和解决方案

### 虚拟环境管理

```bash
# 使用 uv 的虚拟环境支持
uv venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows
```

### 处理循环依赖

- 重构代码以避免循环导入
- 使用延迟导入：在函数内部导入
- 使用类型提示的字符串形式：`"ClassName"`

### 版本冲突解决

```bash
# 查看依赖树
uv pip show --verbose requests

# 升级所有依赖
uv pip install --upgrade

# 锁定特定版本
# 在 pyproject.toml 中指定精确版本
```

### 性能监控

```bash
# 使用 timeit 测试代码性能
python -m timeit 'sum(range(100))'

# 使用 cProfile 进行性能分析
python -m cProfile -s cumulative mymodule.py
```
