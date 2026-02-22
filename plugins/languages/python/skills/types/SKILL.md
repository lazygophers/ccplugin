---
name: types
description: Python 类型提示规范：类型注解、mypy 配置、泛型。使用类型提示时必须加载。
---

# Python 类型提示规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | PEP 8、命名规范 |

## 基本类型注解

```python
from typing import Optional, Union, List, Dict, Any

def greet(name: str) -> str:
    return f"Hello, {name}"

def find_user(user_id: int) -> Optional[User]:
    return users.get(user_id)

def process(data: Union[str, bytes]) -> str:
    return data.decode() if isinstance(data, bytes) else data

def get_items() -> list[dict[str, Any]]:
    return [{"id": 1, "name": "test"}]
```

## 泛型和 Protocol

```python
from typing import TypeVar, Generic, Protocol

T = TypeVar("T")

class Repository(Generic[T]):
    def find(self, id: int) -> Optional[T]:
        ...

    def save(self, entity: T) -> None:
        ...

class Comparable(Protocol):
    def __lt__(self, other: Any) -> bool:
        ...

def sort_items(items: list[Comparable]) -> list[Comparable]:
    return sorted(items)
```

## mypy 配置

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
```

## 检查清单

- [ ] 所有函数有类型注解
- [ ] 使用 Optional 表示可能为 None
- [ ] 使用 Union 或 | 表示多种类型
- [ ] mypy 检查通过
