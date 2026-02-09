# Python 架构设计和工具链

## 架构设计规范

### 核心分层架构

```
API Layer (FastAPI/Starlette handlers)
    ↓
Service Layer (业务逻辑)
    ↓
Repository Layer (数据访问)
    ↓
Database/External Services
```

**关键特性**：

- ✅ **三层清晰分离** - API → Service → Repository，单向依赖
- ✅ **依赖注入** - 使用 fastapi.Depends 或自定义 DI 容器
- ✅ **异步优先** - 使用 async/await 处理 I/O 操作
- ✅ **类型安全** - 全面使用 Pydantic 模型验证数据
- ✅ **配置管理** - 使用 pydantic-settings 管理配置

### 设计原则

1. **分层架构**
   - **API 层**：路由定义、请求验证、响应格式化
   - **Service 层**：业务逻辑实现、事务编排
   - **Repository 层**：数据访问抽象、ORM 操作

2. **依赖注入**
   - 使用 fastapi.Depends 注入依赖
   - 避免全局可变状态
   - 便于单元测试和模块替换

3. **异步优先**
   - 数据库操作使用异步驱动（asyncpg/aiomysql）
   - HTTP 客户端使用 httpx
   - 避免阻塞事件循环

4. **类型安全**
   - 所有数据模型使用 Pydantic 定义
   - 函数签名包含完整类型提示
   - 使用 mypy 进行静态类型检查

## 项目结构

### 推荐目录布局

```
project/
├── pyproject.toml               # 项目配置
├── uv.lock                      # 依赖锁文件
├── README.md
├── .gitignore
├── .env.example                 # 环境变量示例
├── src/                         # 源代码根目录
│   └── myapp/                   # 主包
│       ├── __init__.py
│       ├── main.py              # 应用入口
│       ├── config.py            # 配置定义
│       ├── dependencies.py      # 依赖注入
│       │
│       ├── api/                 # API 层
│       │   ├── __init__.py
│       │   ├── v1/              # API 版本
│       │   │   ├── __init__.py
│       │   │   ├── router.py    # 路由聚合
│       │   │   ├── users.py     # 用户相关路由
│       │   │   └── auth.py      # 认证相关路由
│       │   └── deps.py          # 依赖项
│       │
│       ├── models/              # Pydantic 模型
│       │   ├── __init__.py
│       │   ├── user.py          # 用户模型
│       │   ├── auth.py          # 认证模型
│       │   └── common.py        # 通用模型
│       │
│       ├── schemas/             # 数据库 Schema
│       │   ├── __init__.py
│       │   └── user.py          # ORM 模型
│       │
│       ├── services/            # Service 层（业务逻辑）
│       │   ├── __init__.py
│       │   ├── user_service.py  # 用户服务
│       │   └── auth_service.py  # 认证服务
│       │
│       ├── repositories/        # Repository 层（数据访问）
│       │   ├── __init__.py
│       │   ├── base.py          # 基础 Repository
│       │   └── user.py          # 用户 Repository
│       │
│       ├── core/                # 核心功能
│       │   ├── __init__.py
│       │   ├── security.py      # 安全相关
│       │   ├── config.py        # 配置加载
│       │   └── exceptions.py    # 自定义异常
│       │
│       └── utils/               # 工具函数
│           ├── __init__.py
│           └── helpers.py
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置
│   ├── test_api/                # API 测试
│   ├── test_services/           # Service 测试
│   └── test_repositories/       # Repository 测试
│
├── scripts/                     # 脚本目录
│   ├── init_db.py               # 数据库初始化
│   └── migrate.py               # 数据库迁移
│
└── docs/                        # 文档目录
    └── api.md
```

### 包组织规则

**api 文件夹规则**：

- ✅ 按功能模块组织路由（users.py, posts.py 等）
- ✅ 使用 APIRouter 进行模块化路由
- ✅ 业务逻辑委托给 services 层
- ✅ 请求验证使用 Pydantic 模型

**services 文件夹规则**：

- ✅ 按领域组织（user_service.py, post_service.py 等）
- ✅ 函数名清晰体现功能（create_user, get_user_by_id）
- ✅ 处理业务逻辑和事务编排
- ✅ 抛出业务语义的异常

**repositories 文件夹规则**：

- ✅ 封装数据访问细节
- ✅ 提供增删改查的基础方法
- ✅ 支持复杂查询构建
- ✅ 与 ORM 解耦

**models 文件夹规则**：

- ✅ 使用 Pydantic 定义数据模型
- ✅ 区分请求模型和响应模型
- ✅ 使用 Config 类配置模型行为
- ✅ 提供模型验证和序列化

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
uv add fastapi uvicorn pydantic

# 添加开发依赖
uv add --dev pytest pytest-cov ruff mypy

# 安装特定版本
uv add "requests==2.28.0"

# 安装版本范围
uv add "requests>=2.28.0,<3.0.0"

# 显示已安装的包
uv pip list

# 更新包
uv add requests --upgrade

# 移除依赖
uv remove requests
```

### 依赖原则

- ✅ **最小化依赖**：只添加必要的依赖
- ✅ **优先标准库**：优先使用 Python 标准库
- ✅ **明确版本**：在 pyproject.toml 中明确指定版本约束
- ✅ **定期更新**：定期检查和更新依赖，关注安全公告
- ❌ **避免过宽的版本范围**：避免 `requests>=2.0` 这样的宽范围

## 代码生成

### dataclass 代码生成

```python
from dataclasses import dataclass
from typing import Optional

# ✅ 使用 dataclass 简化数据类定义
@dataclass
class User:
    """用户实体."""
    id: int
    name: str
    email: str
    age: Optional[int] = None

    def is_adult(self) -> bool:
        """检查是否成年."""
        return (self.age or 0) >= 18
```

### Pydantic 模型生成

```python
from pydantic import BaseModel, Field, EmailStr, validator

# ✅ 使用 Pydantic 定义数据模型
class UserCreate(BaseModel):
    """用户创建请求模型."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('name 不能为空')
        return v.strip()

class UserResponse(BaseModel):
    """用户响应模型."""
    id: int
    name: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True  # 支持从 ORM 模型创建
```

### 使用 datamodel-code-generator

```bash
# 安装代码生成工具
uv add --dev datamodel-code-generator

# 从 JSON Schema 生成 Pydantic 模型
datamodel-codegen --input schema.json --output models.py

# 从 OpenAPI 规范生成
datamodel-codegen --input openapi.json --output models/
```

## 工具链配置

### Ruff（统一 linter 和 formatter）

**pyproject.toml 配置**：

```toml
[tool.ruff]
# 目标 Python 版本
target-version = "py311"

# 行长度
line-length = 88

# 指定要检查的规则
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]

# 排除的目录
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.per-file-ignores]
"tests/__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["myapp"]
```

**使用 Ruff**：

```bash
# 检查代码
uv run ruff check .

# 自动修复问题
uv run ruff check --fix .

# 格式化代码
uv run ruff format .

# 检查格式（不修改）
uv run ruff format --check .
```

### mypy（类型检查）

**pyproject.toml 配置**：

```toml
[tool.mypy]
# Python 版本
python_version = "3.11"

# 严格模式
strict = true

# 显示错误代码
show_error_codes = true

# 彩色输出
color_output = true

# 按模块配置
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "third_party_lib.*"
ignore_missing_imports = true
```

**使用 mypy**：

```bash
# 检查整个项目
uv run mypy .

# 检查特定模块
uv run mypy src/myapp/services/

# 严格模式
uv run mypy --strict .

# 生成 HTML 报告
uv run mypy --html-report ./mypy-report src/
```

### pytest（测试框架）

**pyproject.toml 配置**：

```toml
[tool.pytest.ini_options]
# 测试路径
testpaths = ["tests"]

# Python 路径
pythonpath = ["src"]

# 默认选项
addopts = [
    "--cov=myapp",           # 覆盖率
    "--cov-report=term-missing",
    "--cov-report=html",
    "--strict-markers",       # 严格标记
    "--asyncio-mode=auto",    # 异步测试
]

# 标记定义
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

**使用 pytest**：

```bash
# 运行所有测试
uv run pytest

# 运行特定文件
uv run pytest tests/test_users.py

# 运行特定测试
uv run pytest tests/test_users.py::test_create_user

# 显示详细输出
uv run pytest -v

# 显示打印输出
uv run pytest -s

# 运行标记的测试
uv run pytest -m unit
uv run pytest -m "not slow"

# 并行运行（需要 pytest-xdist）
uv run pytest -n auto
```

### pre-commit（Git 钩子）

**安装 pre-commit**：

```bash
uv add --dev pre-commit
```

**.pre-commit-config.yaml**：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

**安装钩子**：

```bash
# 安装 pre-commit 钩子
uv run pre-commit install

# 手动运行所有钩子
uv run pre-commit run --all-files

# 更新钩子版本
uv run pre-commit autoupdate
```

## 开发工作流

### 完整开发流程

1. **编写代码**

   ```bash
   # 创建新模块
   touch src/myapp/services/new_service.py
   ```

2. **格式化和检查**

   ```bash
   # 格式化代码
   uv run ruff format .

   # 检查并自动修复
   uv run ruff check --fix .
   ```

3. **类型检查**

   ```bash
   # 运行 mypy
   uv run mypy src/
   ```

4. **运行测试**

   ```bash
   # 运行所有测试
   uv run pytest

   # 查看覆盖率
   uv run pytest --cov=myapp --cov-report=html
   ```

5. **提交代码**

   ```bash
   # Pre-commit 钩子自动运行检查
   git add .
   git commit -m "feat: add new feature"
   ```

## 关键检查清单

提交代码前的完整检查：

- [ ] 代码符合分层架构（API → Service → Repository）
- [ ] 所有函数都有类型提示
- [ ] 所有 Pydantic 模型都有验证规则
- [ ] 没有类型检查错误（mypy 通过）
- [ ] 代码已格式化（ruff format 通过）
- [ ] 没有 linter 错误（ruff check 通过）
- [ ] 测试覆盖率达标（> 80%）
- [ ] 所有测试通过
- [ ] 异步操作使用 async/await
- [ ] 配置使用 pydantic-settings 管理
- [ ] 依赖已更新到 pyproject.toml
- [ ] uv.lock 已同步（uv sync）

## 常见问题

**Q: 为什么使用 Repository 模式而不是直接在 Service 中操作数据库？**
A: Repository 模式提供了数据访问的抽象层，使代码更易测试和维护，同时也便于切换数据源。

**Q: 如何处理数据库事务？**
A: 使用 SQLAlchemy 的异步事务或在 Service 层使用事务装饰器，确保数据一致性。

**Q: 为什么使用 Pydantic 而不是 dataclass？**
A: Pydantic 提供强大的数据验证、序列化和文档生成功能，更适合 Web API 开发。

**Q: 如何测试异步代码？**
A: 使用 pytest-asyncio 插件，在测试函数上使用 `@pytest.mark.asyncio` 装饰器。

**Q: uv 和 pip 有什么区别？**
A: uv 是用 Rust 编写的现代化包管理器，比 pip 快 10-100 倍，内置虚拟环境管理和依赖锁定功能。

## 性能优化建议

```python
# ✅ 使用连接池
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# ✅ 使用缓存
from functools import lru_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@lru_cache(maxsize=128)
def get_cached_data(key: str) -> str:
    ...

# ✅ 批量操作
async def create_users(users: list[UserCreate]) -> list[User]:
    # 批量插入而非逐个插入
    ...

# ✅ 异步并发
import asyncio

async def fetch_multiple_data():
    results = await asyncio.gather(
        fetch_data1(),
        fetch_data2(),
        fetch_data3(),
    )
    return results
```
