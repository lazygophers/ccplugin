# Python 代码格式规范

## 核心原则

### ✅ 必须遵守

1. **使用 Ruff** - 项目统一使用 Ruff 进行代码格式化和检查
2. **自动格式化** - 代码提交前必须运行格式化工具
3. **导入排序** - 导入语句按标准库、第三方库、本地库分组
4. **行长度限制** - 默认 88 字符，可配置 100 字符
5. **类型注解** - 使用现代类型注解语法（Python 3.11+）
6. **字符串引号** - 优先使用双引号，三引号字符串除外

### ❌ 禁止行为

- 手动格式化而不使用工具
- 混乱导入顺序
- 超过行长度限制
- 不一致的空行使用
- 混用单双引号
- 尾随空格

## Ruff 配置

### 基础配置

```toml
# pyproject.toml
[tool.ruff]
# 行长度
line-length = 88

# 目标 Python 版本
target-version = "py311"

# 扫描的文件
include = ["*.py", "*.pyi"]

# 排除的目录
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

[tool.ruff.lint]
# 启用的规则集
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
]

# 忽略的规则
ignore = [
    "E501",  # 行长度（由 formatter 处理）
]

# 每个文件允许的未使用导入
unfixable = ["F401"]

[tool.ruff.lint.isort]
# 导入排序顺序
known-first-party = ["myapp"]

[tool.ruff.format]
# 使用双引号
quote-style = "double"

# 缩进样式
indent-style = "space"

# 保留魔法尾随逗号
skip-magic-trailing-comma = false

# 行结束符
line-ending = "auto"
```

### 命令行使用

```bash
# 检查代码问题
ruff check .

# 自动修复可修复的问题
ruff check --fix .

# 格式化代码
ruff format .

# 检查格式（不修改）
ruff format --check .

# 同时检查和格式化
ruff check --fix . && ruff format .

# 查看特定规则
ruff rule E501

# 排除特定文件
ruff check --ignore F401 .
```

## 导入规范

### 导入分组

```python
# ✅ 正确 - 标准库、第三方库、本地库分组
# 标准库
import os
import sys
from pathlib import Path
from typing import Any, Optional

# 第三方库
import httpx
from pydantic import BaseModel
from fastapi import FastAPI

# 本地库
from myapp.config import settings
from myapp.models import User
from myapp.services import auth_service


# ❌ 错误 - 混乱导入
import os
import httpx
from myapp.config import settings
from pathlib import Path
from myapp.models import User
```

### 导入顺序

```python
# ✅ 正确 - 按字母排序
import os
import sys
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from myapp.config import settings
from myapp.models import User


# ❌ 错误 - 未排序
import sys
import os
from pathlib import Path
from typing import Optional, Any
```

### 导入别名

```python
# ✅ 正确 - 标准库别名
import os as os_module
import json as json_lib

# ✅ 正确 - 常见第三方库别名
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf

# ✅ 正确 - 避免冲突
from myapp.utils import string as string_utils
from myapp.validators import string as string_validators


# ❌ 避免 - 不必要的别名
import os as o           # 过于简短
import json as j         # 无意义
import httpx as http     # 原名已清晰
```

### 相对导入

```python
# ✅ 正确 - 使用显式相对导入
from . import models
from .services import auth_service
from ..utils import helper
from ..config import settings


# ✅ 正确 - 顶层包使用绝对导入
from myapp.models import User
from myapp.services import auth_service


# ❌ 避免 - 隐式相对导入（Python 3 已移除）
from models import User
from services import auth_service
```

## 行长度

### 默认配置（88 字符）

```python
# ✅ 正确 - 合理的行长度
def get_user(user_id: int) -> User | None:
    """获取用户信息"""
    return db.query(User).filter_by(id=user_id).first()


# ✅ 正确 - 超长时拆分
def get_user_with_profile(
    user_id: int,
    include_deleted: bool = False,
    eager_load: list[str] | None = None,
) -> User | None:
    """获取用户信息（含资料）"""
    query = db.query(User)
    if not include_deleted:
        query = query.filter_by(deleted_at=None)
    return query.first()


# ✅ 正确 - 方法调用拆分
result = long_function_name(
    argument1="value1",
    argument2="value2",
    argument3="value3",
)


# ✅ 正确 - 使用反斜杠拆分（必要时）
url = (
    "https://api.example.com/v1/"
    "users/{user_id}/profile?include={include}"
).format(user_id=123, include="all")
```

### 长字符串处理

```python
# ✅ 正确 - 使用隐式字符串连接
long_string = (
    "This is a very long string that spans multiple lines "
    "without using explicit string concatenation operators."
)

# ✅ 正确 - 使用格式化
message = (
    f"User {user.name} (ID: {user.id}) has "
    f"successfully completed {task_count} tasks."
)

# ✅ 正确 - 三引号字符串
help_text = """
This is a multi-line string that preserves formatting.
It is useful for help messages and documentation.
"""

# ❌ 避免 - 硬编码 URL 在一行
url = "https://api.example.com/v1/users/123/profile?include=all&detailed=true&expanded=true"

# ✅ 正确 - URL 拆分
url = (
    "https://api.example.com/v1/users/123/profile"
    "?include=all&detailed=true&expanded=true"
)
```

## 空行规范

### 文件级空行

```python
# ✅ 正确 - 文件结构
"""模块文档字符串"""

# 导入
import os
from typing import Any

# 常量
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30


# 类和函数定义
class MyClass:
    """类定义"""

    def method1(self):
        """方法 1"""
        pass


def function1():
    """函数 1"""
    pass


def function2():
    """函数 2"""
    pass
```

### 类和函数空行

```python
# ✅ 正确 - 顶层定义之间空两行
class User:
    """用户类"""
    pass


class Order:
    """订单类"""
    pass


def get_user():
    """获取用户"""
    pass


def create_order():
    """创建订单"""
    pass


# ✅ 正确 - 类内部方法之间空一行
class UserService:
    """用户服务"""

    def get_user(self, user_id: int) -> User:
        """获取用户"""
        pass

    def create_user(self, data: dict) -> User:
        """创建用户"""
        pass

    def update_user(self, user_id: int, data: dict) -> User:
        """更新用户"""
        pass
```

### 函数内部空行

```python
# ✅ 正确 - 逻辑块之间空一行
def process_order(order: Order) -> None:
    """处理订单"""
    # 验证订单
    if not order.is_valid():
        raise ValidationError("Invalid order")

    # 检查库存
    for item in order.items:
        if not check_stock(item.product_id, item.quantity):
            raise OutOfStockError(item.product_id)

    # 扣减库存
    for item in order.items:
        decrease_stock(item.product_id, item.quantity)

    # 更新订单状态
    order.status = OrderStatus.PROCESSED
    order.save()
```

## 类型注解

### 基本类型注解

```python
# ✅ 正确 - Python 3.11+ 内置类型（不需要导入）
def greet(name: str) -> str:
    """打招呼"""
    return f"Hello, {name}!"


def calculate(a: int, b: int) -> int:
    """计算"""
    return a + b


def get_items() -> list[str]:  # Python 3.9+
    """获取项目列表"""
    return ["a", "b", "c"]


def get_mapping() -> dict[str, int]:  # Python 3.9+
    """获取映射"""
    return {"a": 1, "b": 2}


# ✅ 正确 - 可选类型
from typing import Optional  # Python < 3.10 或用于复杂场景


def get_user(user_id: int) -> User | None:  # Python 3.10+
    """获取用户"""
    return db.query(User).filter_by(id=user_id).first()


# 或使用 Optional（兼容性更好）
def get_user_legacy(user_id: int) -> Optional[User]:
    """获取用户（兼容写法）"""
    return db.query(User).filter_by(id=user_id).first()
```

### 复杂类型注解

```python
# ✅ 正确 - 联合类型
def process(value: int | str | None) -> str:
    """处理值"""
    if value is None:
        return "empty"
    return str(value)


# ✅ 正确 - 多个返回类型
def fetch_data() -> tuple[bool, str | None, int]:
    """获取数据"""
    return True, "data", 200


from typing import TypeAlias  # Python 3.10+


# ✅ 正确 - 类型别名
UserId: TypeAlias = int
UserData: TypeAlias = dict[str, Any]


def get_user_data(user_id: UserId) -> UserData:
    """获取用户数据"""
    return {"id": user_id, "name": "Alice"}


# ✅ 正确 - 泛型
from typing import TypeVar, Generic

T = TypeVar("T")


class Box(Generic[T]):
    """通用盒子"""

    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value


# ✅ 正确 - Protocol
from typing import Protocol


class Renderable(Protocol):
    """可渲染协议"""

    def render(self) -> str:
        """渲染为字符串"""
        ...
```

### 类型注解位置

```python
# ✅ 正确 - 函数定义
def function(
    arg1: str,
    arg2: int,
    arg3: bool = False,
) -> dict[str, Any]:
    """函数定义"""
    return {"arg1": arg1, "arg2": arg2, "arg3": arg3}


# ✅ 正确 - 类属性
class User:
    """用户类"""

    id: int
    name: str
    email: str | None = None

    def __init__(self, id: int, name: str, email: str | None = None):
        self.id = id
        self.name = name
        self.email = email


# ✅ 正确 - 类型存根（.pyi 文件）
def complex_function(
    data: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
    *,
    verbose: bool = False,
) -> tuple[bool, str | None]:
    """复杂函数"""
    ...
```

## 字符串引号规范

### 基本规则

```python
# ✅ 正确 - 使用双引号
message = "Hello, World!"
greeting = f"Welcome, {name}!"
path = "/home/user/documents"

# ✅ 正确 - 字符串包含双引号时使用单引号
quote = 'He said, "Hello!"'

# ✅ 正确 - 三引号字符串使用双引号
docstring = """
This is a multi-line string.
It preserves line breaks and formatting.
"""

# ❌ 避免 - 不一致的引号
message1 = 'Hello'
message2 = "World"  # 混用
```

### f-string 规范

```python
# ✅ 正确 - f-string 使用双引号
name = "Alice"
greeting = f"Hello, {name}!"
result = f"The result is {calculate():.2f}"

# ✅ 正确 - f-string 中使用表达式
status = f"User is {'active' if user.is_active else 'inactive'}"

# ✅ 正确 - 复杂表达式
message = (
    f"User {user.name} (ID: {user.id}) "
    f"has {len(user.orders)} orders"
)

# ❌ 避免 - 在 f-string 中使用复杂逻辑
# 应该提前计算
result = f"Value: {complex_calculation(x, y, z) * 2 + 1}"
```

## 缩进和空格

### 缩进

```python
# ✅ 正确 - 使用 4 空格缩进
def function():
    if condition:
        do_something()
        if another_condition:
            do_another_thing()


# ✅ 正确 - 悬挂缩进
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one, var_two, var_three, var_four)


# ✅ 正确 - 对齐缩进
def long_function_name(
    var_one: int,
    var_two: int,
    var_three: int,
) -> None:
    print(var_one, var_two)


# ❌ 错误 - 使用 Tab 缩进
def function():
	if condition:  # Tab
		do_something()
```

### 空格使用

```python
# ✅ 正确 - 运算符周围有空格
x = 1 + 2
y = x * 3
z = x / y

# ✅ 正确 - 逗号后有空格
function(arg1, arg2, arg3)
items = [1, 2, 3, 4]

# ✅ 正确 - 冒号后有空格（切片除外）
mapping = {"key": "value"}
for i in range(10):
    pass

# ✅ 正确 - 切片无空格
items[1:10]
items[:5]
items[3:]

# ❌ 错误 - 多余空格
x=1+2        # 运算符无空格
function(arg1,arg2)  # 逗号后无空格
mapping = {"key":"value"}  # 冒号后无空格
items [0]     # 索引前空格
```

### 空格避免

```python
# ✅ 正确 - 括号内无空格
function(arg1, arg2)
spam(1)
dict_instance["key"]

# ✅ 正确 - 切片无空格
seq[index]

# ✅ 正确 - 函数注解冒号后无空格
def function(arg: int) -> int:
    return arg


# ❌ 错误 - 括号内多余空格
function( arg1, arg2 )
spam( 1 )
dict_instance [ "key" ]

# ❌ 错误 - 切片有多余空格
seq[ index ]
seq[ index : ]
seq[ index : 10 ]
```

## 注释和文档字符串

### 文档字符串格式

```python
# ✅ 正确 - Google 风格
def calculate_discount(price: float, discount: float) -> float:
    """计算折后价格.

    Args:
        price: 原价
        discount: 折扣率（0-1）

    Returns:
        折后价格

    Raises:
        ValueError: 如果价格或折扣率无效

    Examples:
        >>> calculate_discount(100, 0.2)
        80.0
    """
    if price < 0 or discount < 0 or discount > 1:
        raise ValueError("Invalid price or discount")
    return price * (1 - discount)


# ✅ 正确 - 简单函数单行
def add(a: int, b: int) -> int:
    """返回两数之和."""
    return a + b
```

### 行内注释

```python
# ✅ 正确 - 注释与代码至少空两格
result = calculate()  # 计算结果

# ✅ 正确 - 有意义的注释
# 使用二分查找提高性能
index = binary_search(items, target)

# ❌ 错误 - 无意义的注释
result = calculate()  # 计算结果并赋值给result

# ❌ 错误 - 注释与代码无间隔
result = calculate()# 计算结果
```

## 检查清单

提交代码前，确保：

- [ ] 代码已通过 `ruff format .` 格式化
- [ ] 代码已通过 `ruff check --fix .` 检查
- [ ] 导入按标准库、第三方库、本地库分组
- [ ] 导入按字母排序
- [ ] 行长度不超过 88 字符（或配置的 100）
- [ ] 顶层定义之间空两行
- [ ] 类方法之间空一行
- [ ] 使用 4 空格缩进
- [ ] 运算符周围有空格
- [ ] 字符串优先使用双引号
- [ ] 函数有类型注解
- [ ] 复杂类型使用 `|` 而非 `Union`（Python 3.10+）
