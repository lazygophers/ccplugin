# Python 类型提示和设计模式

## 基本类型提示

### 类型提示语法

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

## 高级类型提示

### 泛型和 Protocol

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

## 常见代码模式

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
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3):
    def decorator(func):
        @wraps(func)
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

### 上下文管理器

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

## 类型安全检查

### 使用 mypy 进行静态类型检查

```bash
# 检查文件
mypy mymodule.py

# 检查整个项目
mypy .

# 严格模式
mypy --strict mymodule.py
```

### pyproject.toml 中的 mypy 配置

```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

## 常见类型提示错误

```python
# ❌ 避免：使用 Any
def process_data(data: Any) -> Any:
    return data

# ✅ 正确：使用具体类型
def process_data(data: dict[str, int]) -> list[str]:
    return [key for key in data.keys()]

# ❌ 避免：忘记返回类型
def get_user(user_id: int):
    ...

# ✅ 正确：明确返回类型
def get_user(user_id: int) -> Optional[User]:
    ...

# ❌ 避免：过度使用 Union
def compute(value: Union[int, float, str, bool]) -> Union[int, float, str]:
    ...

# ✅ 正确：使用更简洁的类型
def compute(value: int | float) -> int | float:
    ...
```

## 类型覆盖率目标

- 所有公共 API 都应有类型提示
- 内部函数建议有类型提示
- 类型覆盖率目标：> 90%
- 使用 `pyright --outputjson` 检查类型覆盖率

## 性能优化建议

```python
# ✅ 使用列表推导式
result = [x * 2 for x in range(1000)]

# ✅ 使用生成器处理大数据
def process_large_file(file_path):
    with open(file_path) as f:
        for line in f:
            yield process_line(line)

# ✅ 使用 set 进行快速查询（O(1) 查询时间）
valid_ids = {1, 2, 3, 4, 5}
if user_id in valid_ids:
    ...

# ✅ 使用 functools.lru_cache 缓存计算结果
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# ✅ 使用多进程处理 CPU 密集任务
from concurrent.futures import ProcessPoolExecutor

def parallel_compute(items: list[int]) -> list[int]:
    with ProcessPoolExecutor(max_workers=4) as executor:
        return list(executor.map(expensive_operation, items))
```

## 类型提示最佳实践

| 场景 | 推荐做法 | 说明 |
|------|---------|------|
| 可选参数 | `Optional[T]` 或 `T \| None` | 明确表示可能为 None |
| 不可变对象 | 使用 `Sequence[T]` | 比 `List[T]` 更灵活 |
| 键值对 | `dict[str, T]` 或 `Dict[str, T]` | Python 3.9+ 支持简写 |
| 可变长参数 | `*args: int` | 不需要使用 Tuple |
| 回调函数 | `Callable[[Arg1, Arg2], ReturnType]` | 清晰表达函数签名 |
| 自引用类 | `from __future__ import annotations` | 避免前向引用问题 |
