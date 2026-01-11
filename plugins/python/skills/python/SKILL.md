---
name: python
description: Python 开发规范和最佳实践指导，包括代码风格、项目结构、依赖管理、测试策略和性能优化
auto-activate: always:true
---

# Python 开发规范

## 🎯 总体原则

### 核心哲学

1. **简洁优雅**（Zen of Python）

   - 可读性极其重要
   - 明确优于隐晦
   - 简单优于复杂
   - 复杂优于繁杂

2. **现代 Python**

   - 使用 Python 3.8+ 的现代特性
   - 充分利用类型提示
   - 学习和应用最新的库和工具

3. **工程化实践**

   - 遵循行业标准和最佳实践
   - 建立清晰的项目结构
   - 使用自动化工具保证质量

4. **实用至上**
   - 优先可读性和可维护性
   - 避免过度设计和过度优化
   - 根据实际需求选择方案

## 📋 代码规范

### 风格指南（PEP 8）

**命名规范**：

```python
# 模块和文件名：lowercase_with_underscores
my_module.py
data_processing.py

# 常量：UPPERCASE_WITH_UNDERSCORES
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# 类名：CapWords（PascalCase）
class UserManager:
    pass

class DataProcessor:
    pass

# 函数和方法名：lowercase_with_underscores
def calculate_total(items):
    pass

def process_data(data, config=None):
    pass

# 私有方法：_leading_underscore
def _internal_helper():
    pass

# 受保护方法：__double_leading_underscore（谨慎使用）
def __internal_only():
    pass

# 避免单字母变量名（除了循环变量）
for i in range(10):  # ✅
    process(i)

for index in large_collection:  # ✅
    process_item(index)

i = calculate_something()  # ❌ 避免
```

**代码格式**：

```python
# ✅ 推荐：清晰的空行分隔
class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)


# ❌ 避免：密集的代码
class UserManager:
    def __init__(self):
        self.users = []
    def add_user(self, user):
        self.users.append(user)

# ✅ 推荐：行长不超过 88 字符（black 标准）
# 如果超过，使用隐式续行或换行
result = some_function(
    argument_one,
    argument_two,
    argument_three,
)

# ❌ 避免：超长行
result = some_function(argument_one, argument_two, argument_three, argument_four)
```

### 类型提示（PEP 484）

**基本类型提示**：

```python
from typing import Optional, List, Dict, Union, Callable, Any
from pathlib import Path

# 基础类型
def greet(name: str) -> str:
    return f"Hello, {name}!"

# 可选类型
def find_user(user_id: int) -> Optional[dict]:
    # 如果返回可能为 None，使用 Optional
    ...

# 容器类型
def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}

# Union 类型（多种可能）
def parse_value(value: Union[str, int, float]) -> float:
    return float(value)

# 回调函数类型
def apply_transformation(
    data: List[int],
    transformer: Callable[[int], int]
) -> List[int]:
    return [transformer(x) for x in data]

# 现代 Python 3.10+ 使用 | 替代 Union
def parse_value(value: str | int | float) -> float:
    return float(value)
```

**高级类型提示**：

```python
from typing import TypeVar, Generic, Protocol
from dataclasses import dataclass

# 类型变量（泛型）
T = TypeVar('T')

def get_first(items: List[T]) -> T:
    return items[0]

# Protocol（结构子类型）
class Serializable(Protocol):
    def to_dict(self) -> dict:
        ...

def save_object(obj: Serializable):
    return obj.to_dict()

# 数据类（推荐用于数据结构）
@dataclass
class User:
    id: int
    name: str
    email: Optional[str] = None
    age: int = 0
```

### 文档字符串（Docstring）

**函数文档字符串**：

```python
def calculate_average(numbers: List[float]) -> float:
    """计算数字列表的平均值.

    使用 NumPy 风格的 docstring。

    Args:
        numbers: 浮点数列表，不能为空.

    Returns:
        列表中所有数字的平均值.

    Raises:
        ValueError: 如果列表为空.
        TypeError: 如果列表中包含非数字类型.

    Examples:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
        >>> calculate_average([10.5, 20.5])
        15.5
    """
    if not numbers:
        raise ValueError("numbers 不能为空")
    return sum(numbers) / len(numbers)
```

**类文档字符串**：

```python
class DataProcessor:
    """处理和转换数据的类.

    这个类提供了多种数据处理方法，包括清理、转换和验证。

    Attributes:
        config: 处理器配置字典.
        logger: 日志记录器实例.

    Example:
        >>> processor = DataProcessor(config={'format': 'json'})
        >>> result = processor.process(data)
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
```

### 注释原则

```python
# ✅ 好的注释：解释为什么，而不是是什么
# 使用缓存避免重复查询数据库
cached_result = get_from_cache(key)

# ❌ 坏的注释：重复代码
# 从缓存获取结果
cached_result = get_from_cache(key)

# ✅ 为复杂算法添加注释
# 使用两指针技术在 O(n) 时间内找到目标对
def find_pair(numbers: List[int], target: int) -> Optional[tuple]:
    seen = set()
    for num in numbers:
        complement = target - num
        if complement in seen:
            return (complement, num)
        seen.add(num)
    return None

# ✅ 为非显而易见的决定添加注释
# Redis key 的过期时间是 1 小时，因为用户会话通常在 30-45 分钟内完成
CACHE_EXPIRE_SECONDS = 3600
```

## 🏗️ 项目结构

### 推荐目录布局

```
my-project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── __main__.py              # 包的入口点
│       ├── core.py                  # 核心逻辑
│       ├── models.py                # 数据模型
│       ├── utils.py                 # 通用工具
│       ├── exceptions.py            # 自定义异常
│       ├── config.py                # 配置管理
│       └── api/
│           ├── __init__.py
│           ├── handlers.py          # API 处理器
│           └── schemas.py           # 数据模式
│
├── tests/
│   ├── conftest.py                  # pytest 共享 fixtures
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_models.py
│   ├── integration/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   └── test_database.py
│   └── benchmarks/
│       └── bench_core.py
│
├── docs/
│   ├── api.md
│   ├── development.md
│   └── deployment.md
│
├── scripts/                         # 辅助脚本
│   ├── setup_dev.sh
│   └── migrate.py
│
├── pyproject.toml                   # 项目配置
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

### pyproject.toml 最小配置

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

## 📦 依赖管理

### 使用 uv 管理依赖

**初始化项目**：

```bash
# 创建新项目
uv new my-project
cd my-project

# 或在现有项目中初始化
uv init

# 同步依赖
uv sync
```

**添加依赖**：

```bash
# 添加生产依赖
uv pip install requests

# 添加开发依赖（使用 --extra dev）
uv pip install --extra dev pytest

# 安装特定版本
uv pip install "requests==2.28.0"

# 安装版本范围
uv pip install "requests>=2.28.0,<3.0.0"
```

**管理依赖版本**：

```bash
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

## 🧪 测试规范

### 测试结构

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

## 🚀 最佳实践

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

### 4. 上下文管理器

```python
from contextlib import contextmanager

# ✅ 使用上下文管理器管理资源
@contextmanager
def get_database_connection():
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()

# 使用
with get_database_connection() as conn:
    result = conn.query("SELECT * FROM users")
```

### 5. 性能优化建议

```python
# ✅ 使用列表推导式
result = [x * 2 for x in range(1000)]

# ✅ 使用生成器处理大数据
def process_large_file(file_path):
    with open(file_path) as f:
        for line in f:
            yield process_line(line)

# ✅ 使用 set 进行快速查询
valid_ids = {1, 2, 3, 4, 5}
if user_id in valid_ids:
    ...
```

## 📝 常见代码模式

### 单例模式

```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# 使用
config = Singleton()
```

### 工厂模式

```python
class DataProcessor:
    @staticmethod
    def create(processor_type: str) -> 'BaseProcessor':
        if processor_type == 'json':
            return JSONProcessor()
        elif processor_type == 'csv':
            return CSVProcessor()
        raise ValueError(f"Unknown processor: {processor_type}")
```

### 装饰器模式

```python
def retry(max_attempts: int = 3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
        return wrapper
    return decorator

@retry(max_attempts=3)
def unreliable_operation():
    ...
```

## ✅ 完成检查清单

在提交代码前，确保满足以下条件：

- [ ] 所有代码符合 PEP 8 规范
- [ ] 所有函数都有类型提示
- [ ] 所有公共 API 都有文档字符串
- [ ] 没有 type checking 错误（mypy strict）
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 没有硬编码的值
- [ ] 代码可读性高，符合 DRY 原则
- [ ] 没有明显的性能问题
- [ ] 异常处理完善

---

遵循这些规范可以帮助你写出高质量、可维护的 Python 代码。
