# Python 项目结构规范

## 核心原则

### ✅ 必须遵守

1. **明确布局选择** - 根据项目类型选择 src/ 布局或扁平布局
2. **包内一致性** - 同一项目中保持一致的目录结构
3. **分离关注点** - 测试、文档、配置与源代码分离
4. **清晰的命名** - 包名和模块名简洁且有意义
5. **配置集中** - 项目配置文件集中在项目根目录

### ❌ 禁止行为

- 将测试文件与源代码混在同一目录
- 创建过深的目录层级（超过 4 层）
- 使用不规范的包名（如 `my_project`、`test`）
- 在包内使用相对导入（`from .. import`）
- 忽略 `__init__.py` 文件的作用

## 推荐目录布局

### src/ 布局（推荐用于库项目）

src/ 布局将源代码放在 `src/` 目录下，避免测试代码意外导入未安装的项目代码。

```
my-package/
├── src/                           # 源代码目录
│   └── my_package/                # 主包目录
│       ├── __init__.py            # 包初始化文件
│       ├── core/                  # 核心功能模块
│       │   ├── __init__.py
│       │   └── models.py
│       ├── api/                   # API 接口模块
│       │   ├── __init__.py
│       │   └── routes.py
│       └── utils/                 # 工具模块
│           ├── __init__.py
│           └── helpers.py
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── conftest.py                # pytest 配置和共享 fixture
│   ├── unit/                      # 单元测试
│   │   ├── __init__.py
│   │   └── test_models.py
│   └── integration/               # 集成测试
│       ├── __init__.py
│       └── test_api.py
│
├── docs/                          # 文档目录
│   ├── source/
│   └── build/
│
├── pyproject.toml                 # 项目配置文件
├── README.md                      # 项目说明
├── LICENSE                        # 许可证
├── .gitignore                     # Git 忽略文件
├── .python-version                # Python 版本（如 3.11）
└── uv.lock                        # 依赖锁文件
```

### 扁平布局（推荐用于应用/服务项目）

扁平布局适用于应用程序、脚本和微服务，源代码直接在项目根目录。

```
my-service/
├── my_service/                    # 主包目录
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   ├── config.py                  # 配置管理
│   ├── dependencies.py            # 依赖注入
│   │
│   ├── api/                       # API 层
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py             # 请求/响应模型
│   │
│   ├── core/                      # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── domain.py              # 领域模型
│   │   └── services.py            # 业务服务
│   │
│   ├── infrastructure/            # 基础设施层
│   │   ├── __init__.py
│   │   ├── database.py            # 数据库
│   │   ├── cache.py               # 缓存
│   │   └── messaging.py           # 消息队列
│   │
│   └── utils/                     # 工具模块
│       ├── __init__.py
│       └── helpers.py
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/                       # 端到端测试
│
├── scripts/                       # 脚本目录
│   ├── init_db.py
│   └── migrate.py
│
├── pyproject.toml
├── README.md
├── .env.example                   # 环境变量示例
├── .gitignore
└── .python-version
```

### 单包项目（简单项目）

对于小型项目或单包库，可以使用更简单的结构。

```
my-tool/
├── my_tool/                       # 主包
│   ├── __init__.py
│   ├── cli.py                     # 命令行接口
│   ├── core.py                    # 核心功能
│   └── utils.py                   # 工具函数
│
├── tests/
│   ├── __init__.py
│   └── test_my_tool.py
│
├── pyproject.toml
└── README.md
```

## 包组织规则

### 包命名规范

```python
# ✅ 正确 - 全小写，使用下划线分隔单词
my_package
user_service
payment_gateway
data_processing

# ❌ 错误 - 使用大写或驼峰
MyPackage
myPackage
user_service
```

### 模块命名规范

```python
# ✅ 正确 - 全小写，使用下划线分隔单词
user_models.py
auth_service.py
database_utils.py
http_client.py

# ❌ 错误 - 使用大写或驼峰
UserModels.py
authService.py
```

### __init__.py 的作用

```python
# ✅ 正确 - 使用 __init__.py 导出公共 API
# my_package/__init__.py
"""
用户管理包。

提供用户注册、登录、信息管理等功能。
"""

from my_package.core import User, UserService
from my_package.api import create_app

__all__ = [
    "User",
    "UserService",
    "create_app",
    "__version__",
]

__version__ = "1.0.0"


# ✅ 正确 - 简单的 __init__.py
# my_package/utils/__init__.py
from my_package.utils.helpers import format_name, validate_email

__all__ = ["format_name", "validate_email"]


# ❌ 错误 - 在 __init__.py 中编写大量逻辑
# my_package/__init__.py
class User:
    pass

def authenticate():
    pass

# 这些应该放在单独的模块中
```

## 配置文件位置

### pyproject.toml

项目的主配置文件，位于项目根目录。

```toml
# ✅ 正确 - pyproject.toml 基本结构
[project]
name = "my-package"
version = "1.0.0"
description = "我的项目描述"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "typer>=0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
]

[project.scripts]
my-cli = "my_package.cli:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]  # 扁平布局需要，src 布局不需要
```

### 环境配置

```
# ✅ 正确 - 环境配置文件管理
my-service/
├── .env.example              # 环境变量示例（提交到版本控制）
├── .env.local                # 本地开发环境（不提交）
├── .env.test                 # 测试环境（不提交）
└── .env.production           # 生产环境（不提交）


# .env.example 内容示例
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=False
```

## 测试目录组织

### 标准测试结构

```
tests/
├── __init__.py
├── conftest.py                # 共享的 fixtures 和配置
│
├── unit/                      # 单元测试
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
│
├── integration/               # 集成测试
│   ├── __init__.py
│   ├── test_database.py
│   └── test_api.py
│
└── e2e/                       # 端到端测试（可选）
    ├── __init__.py
    └── test_user_flow.py
```

### conftest.py 使用

```python
# ✅ 正确 - conftest.py 组织共享 fixtures
# tests/conftest.py
import pytest
from my_package.core import User
from my_package.database import SessionLocal

@pytest.fixture
def db_session():
    """创建测试数据库会话。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        session.rollback()

@pytest.fixture
def test_user(db_session):
    """创建测试用户。"""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user


# tests/integration/conftest.py
# 集成测试专用的 fixtures
@pytest.fixture(scope="session")
def test_database():
    """设置测试数据库。"""
    # 初始化测试数据库
    yield
    # 清理测试数据库
```

## 模块组织最佳实践

### 按功能分层

```
my_service/
├── api/                       # API 层 - 处理 HTTP 请求
│   ├── routes.py
│   ├── schemas.py             # Pydantic 模型
│   └── middleware.py
│
├── core/                      # 核心业务逻辑
│   ├── services.py            # 业务服务
│   ├── domain.py              # 领域模型
│   └── exceptions.py          # 自定义异常
│
├── infrastructure/            # 基础设施
│   ├── database.py
│   ├── cache.py
│   └── external_apis.py
│
└── utils/                     # 通用工具
    └── helpers.py
```

### 避免循环导入

```
# ✅ 正确 - 单向依赖
api/ → core/ → infrastructure/

# ❌ 错误 - 循环依赖
api/ → core/ → api/
```

### 模块大小控制

```python
# ✅ 正确 - 单一职责，模块简洁
# models.py - 只包含数据模型
class User:
    pass

class Order:
    pass


# ❌ 错误 - 模块过于庞大
# models.py - 包含所有内容
class User:
    pass

class Order:
    pass

def create_user():
    pass

def send_email():
    pass

class Database:
    pass
```

## src/ 布局 vs 扁平布局

### 使用 src/ 布局的场景

- ✅ 开发库/包（发布到 PyPI）
- ✅ 需要安装后使用的项目
- ✅ 想要避免测试代码导入未安装的源代码

```bash
# src/ 布局的运行方式
uv run python -m my_package.main
# 或
my-cli  # 如果配置了 [project.scripts]
```

### 使用扁平布局的场景

- ✅ 开发应用程序/服务
- ✅ 微服务项目
- ✅ 简单脚本或工具

```bash
# 扁平布局的运行方式
uv run python -m my_service.main
# 或
uv run my_service/main.py
```

## 配置文件最佳实践

### pyproject.toml 配置

```toml
# ✅ 正确 - 完整的配置
[project]
name = "my-service"
version = "1.0.0"
description = "我的服务"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "fastapi>=0.100.0",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21",
    "ruff>=0.1",
    "mypy>=1.5",
]

[project.urls]
Homepage = "https://github.com/user/my-service"
Documentation = "https://my-service.readthedocs.io"
Repository = "https://github.com/user/my-service"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_service"]  # src 布局

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --cov=my_service --cov-report=term-missing"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## 检查清单

项目结构设计时，确保：

- [ ] 根据项目类型选择合适的布局（src/ 或扁平）
- [ ] 包名使用全小写和下划线
- [ ] 测试目录与源代码分离
- [ ] 配置文件集中在项目根目录
- [ ] 使用 pyproject.toml 统一管理配置
- [ ] 每个包都有 `__init__.py`
- [ ] 避免循环导入
- [ ] 模块职责单一，避免过大
- [ ] 使用 conftest.py 组织共享 fixtures
- [ ] 环境变量文件有 .env.example
