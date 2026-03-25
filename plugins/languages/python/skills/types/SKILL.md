---
description: Python 类型系统最佳实践 - PEP 695 泛型、Pydantic v2、mypy strict mode。现代 Python 类型安全的核心规范。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Python 类型系统最佳实践

## 适用 Agents

- **python:dev** - 开发阶段使用
- **python:debug** - 类型错误调试
- **python:test** - 测试代码类型注解

## 相关 Skills

- **Skills(python:core)** - 基础规范
- **Skills(python:error)** - 错误处理类型（Result、Option）
- **Skills(python:web)** - Web 框架的类型集成

## 核心原则（PEP 695 & Pydantic v2）

### 1. 完整类型注解（PEP 484）

所有公共 API 必须包含类型注解：

```python
# ✅ 正确：完整类型注解
def fetch_user(user_id: int) -> User | None:
    """获取用户（Python 3.10+ union 语法）"""
    return database.get(user_id)

# ❌ 错误：缺少类型注解
def fetch_user(user_id):
    return database.get(user_id)
```

### 2. 泛型类型（PEP 695 - Python 3.12+）

使用新的泛型语法：

```python
# ✅ 新语法（Python 3.12+）
def first[T](items: list[T]) -> T | None:
    """获取列表第一个元素（泛型函数）"""
    return items[0] if items else None

class Container[T]:
    """泛型容器（类型参数）"""
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# ⚠️ 旧语法（Python 3.11-）- 向后兼容
from typing import TypeVar, Generic

T = TypeVar('T')

class OldContainer(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
```

### 3. Pydantic v2 模型

**核心改进**：
- 性能提升 5-50 倍（Rust 核心）
- 新的配置系统（`model_config`）
- 新的验证器语法

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Annotated, Self

class User(BaseModel):
    """用户模型（Pydantic v2 风格）"""
    model_config = ConfigDict(
        str_strip_whitespace=True,      # 自动去除空格
        validate_assignment=True,        # 赋值时验证
        frozen=False,                    # 是否不可变
    )

    id: int
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    age: Annotated[int, Field(ge=0, le=150)]

    # 字段验证器（v2 语法）
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('username must be alphanumeric')
        return v.lower()

    # 模型验证器（v2 语法）
    @model_validator(mode='after')
    def check_age_consistency(self) -> Self:
        if self.age < 18 and not self.email.endswith('@school.edu'):
            raise ValueError('minors must use school email')
        return self
```

**v1 → v2 迁移要点**：
- `Config` → `model_config`（ConfigDict）
- `@validator` → `@field_validator` / `@model_validator`
- `.dict()` → `.model_dump()`
- `.json()` → `.model_dump_json()`

### 4. 类型别名（Python 3.12+）

```python
# ✅ 新语法（Python 3.12+）
type UserId = int
type UserName = Annotated[str, Field(min_length=3, max_length=50)]
type UserDict = dict[str, User]

def get_user(user_id: UserId) -> User:
    ...

# ⚠️ 旧语法（向后兼容）
UserId = int
UserName = str
UserDict = Dict[str, User]
```

### 5. Protocol（鸭子类型）

优先使用 Protocol 而非 ABC：

```python
from typing import Protocol

class Drawable(Protocol):
    """可绘制对象协议"""
    def draw(self) -> None: ...
    def get_bounds(self) -> tuple[int, int, int, int]: ...

class Circle:
    def draw(self) -> None:
        print("Drawing circle")

    def get_bounds(self) -> tuple[int, int, int, int]:
        return (0, 0, 100, 100)

def render(obj: Drawable) -> None:
    """渲染可绘制对象"""
    obj.draw()  # 任何有 draw() 方法的对象都可以

# Circle 自动符合 Drawable 协议，无需继承
render(Circle())
```

### 6. TypedDict（结构化字典）

```python
from typing import TypedDict, NotRequired

class UserDict(TypedDict):
    """用户字典类型"""
    id: int
    username: str
    email: str
    age: NotRequired[int]  # 可选字段（Python 3.11+）

def create_user(data: UserDict) -> User:
    return User(**data)

# ✅ 正确
user_data: UserDict = {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
}

# ❌ 错误：mypy 会报错
invalid_data: UserDict = {
    "id": "not_an_int",  # 类型错误
    "username": "alice"
}
```

### 7. Literal 和 Enum

```python
from typing import Literal
from enum import Enum

# Literal 用于固定值
Status = Literal["pending", "running", "completed", "failed"]

def get_task_status() -> Status:
    return "completed"  # ✅ 只能返回这 4 个值之一

# Enum 用于复杂枚举
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

def update_status(status: TaskStatus) -> None:
    print(f"Status: {status.value}")

update_status(TaskStatus.COMPLETED)
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "简单函数不需要类型" | ✅ 是否所有公共函数都有类型注解？ |
| "Any 类型足够灵活" | ✅ 是否滥用 `Any`（应该 < 5%）？ |
| "运行时类型检查更安全" | ✅ 是否优先使用静态类型检查（mypy）？ |
| "Pydantic v1 够用了" | ✅ 是否迁移到 Pydantic v2（性能提升 5-50 倍）？ |
| "旧的泛型语法更兼容" | ✅ 是否使用 Python 3.12+ PEP 695 语法？ |
| "TypedDict 太复杂" | ✅ 字典参数是否使用 TypedDict？ |

## mypy 配置最佳实践

### pyproject.toml

```toml
[tool.mypy]
python_version = "3.13"
strict = true

# 严格检查
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true

# 第三方库类型
ignore_missing_imports = false

# 性能优化
cache_dir = ".mypy_cache"
incremental = true

# 每个模块单独配置
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false  # 测试文件可以放宽
```

### 运行 mypy

```bash
# 严格模式检查
mypy --strict src/

# 生成覆盖率报告
mypy --html-report mypy-report src/

# 只检查特定文件
mypy src/models.py src/api.py
```

## 工具集成

### ruff 类型注解检查

```toml
[tool.ruff.lint]
select = [
    "ANN",  # 强制类型注解
]

ignore = [
    "ANN101",  # missing-type-self（不强制 self 注解）
    "ANN102",  # missing-type-cls（不强制 cls 注解）
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN"]  # 测试文件不强制类型注解
```

## 完整示例

### 泛型仓储模式

```python
from typing import Protocol

class Entity(Protocol):
    """实体协议"""
    id: int

class Repository[T: Entity]:
    """泛型仓储（Python 3.12+ 语法）"""

    def __init__(self) -> None:
        self._data: dict[int, T] = {}

    def find(self, id: int) -> T | None:
        """查找实体"""
        return self._data.get(id)

    def save(self, entity: T) -> None:
        """保存实体"""
        self._data[entity.id] = entity

    def find_all(self) -> list[T]:
        """查找所有实体"""
        return list(self._data.values())

# 使用
class User:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

user_repo = Repository[User]()
user_repo.save(User(1, "Alice"))
user = user_repo.find(1)
```

### Pydantic v2 完整示例

```python
from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Annotated

class Address(BaseModel):
    """地址模型"""
    street: str
    city: str
    country: str = "USA"

class User(BaseModel):
    """用户模型（展示所有 Pydantic v2 特性）"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    id: int
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    age: Annotated[int, Field(ge=0, le=150)]
    address: Address | None = None

    @computed_field
    @property
    def display_name(self) -> str:
        """计算字段"""
        return f"{self.username} ({self.email})"

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('username must be alphanumeric')
        return v.lower()

# 使用
user = User(
    id=1,
    username="Alice",
    email="alice@example.com",
    age=25,
    address=Address(street="123 Main St", city="NYC")
)

print(user.model_dump())       # v2: 导出字典
print(user.model_dump_json())  # v2: 导出 JSON
```

## 检查清单

### 类型注解
- [ ] 所有公共函数包含完整类型注解
- [ ] 使用 Python 3.10+ union 语法（`|` 而非 `Union`）
- [ ] 使用 `Annotated` 添加元数据约束
- [ ] 泛型使用 Python 3.12+ PEP 695 语法

### Pydantic
- [ ] 使用 Pydantic v2 语法
- [ ] `model_config` 替代 `Config`
- [ ] `@field_validator` 替代 `@validator`
- [ ] `.model_dump()` 替代 `.dict()`

### mypy 检查
- [ ] 运行 `mypy --strict` 无错误
- [ ] 没有 `# type: ignore` 注释（除非必要）
- [ ] `Any` 类型使用 < 5%
- [ ] 第三方库有 type stubs

### Protocol 和 TypedDict
- [ ] 优先使用 Protocol 而非 ABC
- [ ] 字典参数使用 TypedDict
- [ ] 固定值使用 Literal
