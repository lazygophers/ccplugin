---
name: python-types
description: Python 类型注解与类型安全规范。涵盖 PEP 604/612/646/695 现代语法、Pydantic v2 模型、ty/pyright 严格模式、泛型/协议/Literal。在添加类型注解、修复类型检查报错、设计数据模型、写泛型代码、配置 typeCheckingMode 时使用。也触发于"类型注解"、"类型检查"、"Pydantic"、"mypy/pyright/ty 报错"。
---

# Python 类型规范 (2026)

Python 3.13+, ty Beta / pyright strict。所有公共函数必须有完整注解, 私有函数依逻辑复杂度判断。

## 类型检查器选型

| 工具 | 何时用 |
|------|--------|
| **pyright** (strict) | 默认首选, 98% spec conformance, VS Code 集成最好 |
| **ty** (Astral) | 新项目 + 已用 uv/ruff, 速度 10-60x mypy, Beta 期 (2026) 与 pyright 并存于 CI |
| **mypy** (strict) | 老项目维护期, 或依赖 mypy 插件 (django-stubs, sqlalchemy stubs) |

不要在同一项目混用 mypy + pyright 配置, 选一个为 CI 真相源。

## 现代类型语法

PEP 585 / 604 / 695, Python 3.13+ 默认可用:

```python
# 内置泛型 (PEP 585) - 不要 from typing import List
def parse(items: list[str]) -> dict[str, int]: ...

# Union 语法 (PEP 604) - 不要 Optional[X] / Union[A, B]
def find(uid: int) -> User | None: ...
def coerce(x: int | str | None) -> str: ...

# 类型别名 (PEP 695) - 不要 TypeAlias
type UserId = int
type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

# 泛型函数 (PEP 695) - 不要 TypeVar
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

# 泛型类 (PEP 695)
class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []
    def push(self, item: T) -> None: ...
    def pop(self) -> T: ...
```

## Annotated 元数据约束

携带运行时约束 (Pydantic / FastAPI 会读取):

```python
from typing import Annotated
from pydantic import Field

UserName = Annotated[str, Field(min_length=3, max_length=50)]
Port = Annotated[int, Field(ge=1, le=65535)]
```

## Literal / Final / TypedDict

```python
from typing import Literal, Final, TypedDict

Status = Literal["pending", "active", "deleted"]
MAX_CONN: Final[int] = 100

class UserDict(TypedDict):
    id: int
    name: str
    email: str
```

## Protocol (结构子类型)

替代 ABC, 不需要继承关系:

```python
from typing import Protocol

class SupportsClose(Protocol):
    def close(self) -> None: ...

def cleanup(resource: SupportsClose) -> None:
    resource.close()
```

## Pydantic v2 模型

数据校验首选, 不要手写 `__init__` 做校验:

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Annotated

class UserCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        frozen=True,
        extra="forbid",
    )

    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    age: Annotated[int, Field(ge=0, le=150)]

# v2 API
user = UserCreate.model_validate({"username": "alice", "email": "a@b.c", "age": 20})
data = user.model_dump()       # 不是 .dict()
json_str = user.model_dump_json()  # 不是 .json()
```

不再用 `@validator`, 改用 `@field_validator` / `@model_validator`。

## dataclass / msgspec / attrs 选型

| 场景 | 选择 |
|------|------|
| 内部数据容器, 无校验 | `@dataclass(slots=True, frozen=True)` |
| API 边界, 需要 JSON + 校验 | Pydantic v2 |
| 极致性能 (序列化热路径) | `msgspec.Struct` (比 Pydantic 快 5-10x) |
| 老代码维护 | `attrs` (保留即可, 新代码不用) |

## 严格模式配置

`pyproject.toml`:

```toml
[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.13"
reportMissingTypeStubs = "warning"
reportUnknownMemberType = "warning"

# 或 ty
[tool.ty.rules]
# ty 默认检查所有代码, 包括无注解函数体
```

## 常见报错与修复

| 报错 | 修复 |
|------|------|
| `Argument of type "X \| None" cannot be assigned to "X"` | 加 `if x is None: ...` 或 `assert x is not None` |
| `Object of type "None" is not subscriptable` | 同上 |
| `Type "X" is partially unknown` | 给变量显式注解或修复源头泛型 |
| `Cannot access member "x" for type "Y"` | 检查 import / 是否漏了 stub (`uv add --dev types-xxx`) |

## 反模式

- `from typing import List, Dict, Tuple, Optional, Union` (用内置泛型 + `|`)
- `Any` 当万能逃生口 (改用 `object` + `isinstance` 收窄, 或 `TypeVar`)
- `# type: ignore` 不带具体规则名 (写 `# type: ignore[arg-type]`)
- Pydantic v1 API (`.dict()`, `.parse_obj()`, `@validator`)
- 在运行时调 `typing.get_type_hints()` 做业务逻辑 (PEP 649 后行为变了, 改用 Pydantic)
