# Python 文档规范

## 核心原则

### ✅ 必须遵守

1. **README 完整** - 项目必须有 README.md
2. **API 文档** - 公开 API 必须有文档
3. **代码注释** - 公开函数和类必须有文档字符串
4. **文档更新** - 代码变更时同步更新文档
5. **文档清晰** - 文档简洁明了，易于理解

### ❌ 禁止行为

- 缺少 README.md
- 公开 API 无文档
- 注释与代码不一致
- 文档包含过时信息
- 文档过于冗长

## README 规范

### README 结构

```markdown
# 项目名称

简短描述项目的主要功能和用途。

## 功能特性

- 功能 1：描述
- 功能 2：描述
- 功能 3：描述

## 快速开始

### 安装

```bash
pip install my-project
```

### 使用

```python
from my_project import main

main.run()
```

## 项目结构

```
project/
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── main.py
├── tests/
└── pyproject.toml
```

## 开发指南

### 环境要求

- Python 3.11+
- uv 包管理器

### 运行项目

```bash
# 克隆项目
git clone https://github.com/username/project.git
cd project

# 安装依赖
uv sync

# 运行项目
uv run python src/my_project/main.py
```

### 运行测试

```bash
uv run pytest
```

## API 文档

详见 [API 文档](docs/api.md)

## 贡献指南

详见 [贡献指南](CONTRIBUTING.md)

## 许可证

MIT License
```

### README 最佳实践

```markdown
# ✅ 正确 - 清晰的 README
# MyProject

一个高性能的 Python Web 框架，提供简洁的 API 和强大的功能。

## 功能特性

- 高性能：基于 ASGI，性能优异
- 简洁 API：易于使用和集成
- 类型安全：完整的类型注解
- 完整测试：单元测试和集成测试覆盖

## 快速开始

### 安装

```bash
uv pip install myproject
```

### 使用

```python
from myproject import App

app = App()

@app.route("/")
def hello():
    return "Hello, World!"

app.run(":8080")
```

# ❌ 错误 - 不完整的 README
# MyProject

Python 项目。
```

## API 文档

### API 文档结构

```markdown
# API 文档

## 用户 API

### 用户登录

**描述**

用户登录接口，验证用户名和密码，返回用户信息和访问令牌。

**请求**

- 方法：POST
- 路径：/api/user/login
- Content-Type：application/json

**请求参数**

| 参数名   | 类型   | 必填 | 说明     |
| ------- | ------ | ---- | -------- |
| username | string | 是   | 用户名   |
| password | string | 是   | 密码     |

**请求示例**

```json
{
  "username": "testuser",
  "password": "password123"
}
```

**响应**

| 字段名   | 类型   | 说明     |
| ------- | ------ | -------- |
| code    | int32  | 响应码   |
| message | string | 响应消息 |
| data    | object | 用户数据 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误码**

| 错误码 | 说明           |
| ------- | -------------- |
| 1001    | 用户名不存在   |
| 1002    | 密码错误       |
```

### API 文档最佳实践

```markdown
# ✅ 正确 - 完整的 API 文档
# API 文档

## 用户 API

### 用户登录

**描述**

用户登录接口，验证用户名和密码，返回用户信息和访问令牌。

**请求**

- 方法：POST
- 路径：/api/user/login
- Content-Type：application/json

**请求参数**

| 参数名   | 类型   | 必填 | 说明     |
| ------- | ------ | ---- | -------- |
| username | string | 是   | 用户名   |
| password | string | 是   | 密码     |

**请求示例**

```json
{
  "username": "testuser",
  "password": "password123"
}
```

# ❌ 错误 - 不完整的 API 文档
# API 文档

## 用户登录

POST /api/user/login

{
  "username": "testuser",
  "password": "password123"
}
```

## 文档字符串规范

### Google 风格文档字符串

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


# ✅ 正确 - 类文档字符串
class UserService:
    """用户服务类.

    提供用户相关的业务逻辑处理，包括用户创建、查询、更新和删除。

    Attributes:
        db: 数据库会话
        cache: 缓存客户端
    """

    def __init__(self, db: Session, cache: Cache):
        """初始化用户服务.

        Args:
            db: 数据库会话
            cache: 缓存客户端
        """
        self.db = db
        self.cache = cache


# ❌ 错误 - 缺少文档字符串
def calculate_discount(price: float, discount: float) -> float:
    return price * (1 - discount)


class UserService:
    def __init__(self, db: Session, cache: Cache):
        self.db = db
        self.cache = cache
```

### NumPy 风格文档字符串

```python
# ✅ 正确 - NumPy 风格（适合科学计算）
def calculate_statistics(data: list[float]) -> dict[str, float]:
    """计算统计数据.

    Parameters
    ----------
    data : list[float]
        输入数据列表

    Returns
    -------
    dict[str, float]
        包含均值、标准差、最小值、最大值的字典

    Examples
    --------
    >>> calculate_statistics([1, 2, 3, 4, 5])
    {'mean': 3.0, 'std': 1.414, 'min': 1, 'max': 5}
    """
    import statistics
    return {
        "mean": statistics.mean(data),
        "std": statistics.stdev(data) if len(data) > 1 else 0,
        "min": min(data),
        "max": max(data),
    }
```

### reStructuredText 风格（Sphinx）

```python
# ✅ 正确 - reStructuredText 风格（适合 Sphinx）
def authenticate_user(username: str, password: str) -> bool:
    """验证用户凭据.

    :param username: 用户名
    :type username: str
    :param password: 密码
    :type password: str
    :return: 验证成功返回 True，否则返回 False
    :rtype: bool
    :raises ValueError: 如果用户名或密码为空
    """
    if not username or not password:
        raise ValueError("Username and password are required")
    # 实现验证逻辑
    return True
```

## 类型注解作为文档

### 类型注解规范

```python
# ✅ 正确 - 类型注解即文档
from typing import Optional

def get_user(user_id: int) -> Optional[User]:
    """根据 ID 获取用户.

    类型注解已经说明了参数和返回值的类型，
    文档字符串关注行为和边界条件。

    Args:
        user_id: 用户 ID，必须大于 0

    Returns:
        用户对象，如果不存在则返回 None

    Raises:
        ValueError: 如果 user_id 小于等于 0
    """
    if user_id <= 0:
        raise ValueError("user_id must be positive")
    return db.query(User).filter_by(id=user_id).first()


# ✅ 正确 - 使用 TypeAlias 提高可读性
from typing import TypeAlias

# 类型别名
UserId: TypeAlias = int
UserData: TypeAlias = dict[str, Any]

def process_user(user_id: UserId) -> UserData:
    """处理用户数据."""
    return {"id": user_id, "processed": True}


# ❌ 错误 - 缺少类型注解
def get_user(user_id):
    """根据 ID 获取用户.

    Args:
        user_id: 用户 ID（类型不明确）

    Returns:
        用户对象（类型不明确）
    """
    return db.query(User).filter_by(id=user_id).first()
```

### 复杂类型注解

```python
# ✅ 正确 - 复杂类型的文档
from typing import Protocol

class Renderable(Protocol):
    """可渲染对象协议."""

    def render(self) -> str:
        """渲染为字符串."""
        ...

def render_all(items: list[Renderable]) -> str:
    """渲染所有可渲染对象.

    Args:
        items: 可渲染对象列表

    Returns:
        拼接后的渲染结果
    """
    return "".join(item.render() for item in items)


# ✅ 正确 - 泛型文档
from typing import TypeVar, Generic

T = TypeVar("T")

class Box(Generic[T]):
    """通用容器.

    Type Args:
        T: 包含的值类型
    """

    def __init__(self, value: T) -> None:
        """初始化容器.

        Args:
            value: 要包含的值
        """
        self.value = value

    def get(self) -> T:
        """获取包含的值."""
        return self.value
```

## 代码注释

### 导出类注释

```python
# ✅ 正确 - 公开类必须有文档字符串
class User:
    """用户实体类.

    表示系统中的用户，包含用户的基本信息和状态。
    用户数据持久化到数据库中。

    Attributes:
        id: 用户唯一标识
        username: 用户名（唯一）
        email: 邮箱地址（唯一）
        is_active: 账户是否激活
        created_at: 创建时间
    """

    def __init__(self, username: str, email: str):
        """初始化用户.

        Args:
            username: 用户名
            email: 邮箱地址
        """
        self.id: int = 0
        self.username = username
        self.email = email
        self.is_active: bool = True
        self.created_at: datetime = datetime.now()


# ❌ 错误 - 缺少文档字符串
class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
```

### 导出函数注释

```python
# ✅ 正确 - 公开函数必须有文档字符串
def send_email(to: str, subject: str, body: str) -> bool:
    """发送邮件.

    Args:
        to: 收件人邮箱地址
        subject: 邮件主题
        body: 邮件正文

    Returns:
        发送成功返回 True，失败返回 False

    Raises:
        ValueError: 如果邮箱地址格式无效
        ConnectionError: 如果邮件服务器连接失败
    """
    if not validate_email(to):
        raise ValueError(f"Invalid email address: {to}")
    # 实现发送逻辑
    return True


# ✅ 正确 - 简单函数可以简化文档
def add(a: int, b: int) -> int:
    """返回两数之和."""
    return a + b


# ❌ 错误 - 缺少文档字符串
def send_email(to: str, subject: str, body: str) -> bool:
    return True
```

### 复杂逻辑注释

```python
# ✅ 正确 - 复杂算法需要注释
def binary_search(items: list[int], target: int) -> int | None:
    """二分查找.

    使用二分查找算法在已排序列表中查找目标值。
    时间复杂度 O(log n)。

    Args:
        items: 已排序的整数列表
        target: 要查找的目标值

    Returns:
        目标值的索引，如果不存在则返回 None
    """
    left, right = 0, len(items) - 1

    while left <= right:
        # 计算中间位置，避免整数溢出
        mid = left + (right - left) // 2

        if items[mid] == target:
            return mid
        elif items[mid] < target:
            # 目标在右半部分
            left = mid + 1
        else:
            # 目标在左半部分
            right = mid - 1

    return None


# ✅ 正确 - 关键决策点需要注释
def process_payment(order: Order) -> PaymentResult:
    """处理支付."""
    # 检查订单状态
    if order.status != OrderStatus.PENDING:
        return PaymentResult(status="failed", reason="invalid_order_status")

    # 验证支付金额
    if order.total <= 0:
        return PaymentResult(status="failed", reason="invalid_amount")

    # 检查用户信用额度（VIP 用户可超额）
    if not user.is_vip and order.total > user.credit_limit:
        return PaymentResult(status="failed", reason="insufficient_credit")

    # 处理支付...
    return PaymentResult(status="success")


# ❌ 错误 - 复杂逻辑缺少注释
def process_payment(order: Order) -> PaymentResult:
    if order.status != OrderStatus.PENDING:
        return PaymentResult(status="failed", reason="invalid_order_status")
    if order.total <= 0:
        return PaymentResult(status="failed", reason="invalid_amount")
    if not user.is_vip and order.total > user.credit_limit:
        return PaymentResult(status="failed", reason="insufficient_credit")
    return PaymentResult(status="success")
```

## 变更日志维护

### CHANGELOG 规范

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 新增用户登录功能
- 新增邮件通知服务

### Changed
- 重构认证中间件
- 更新依赖版本

### Deprecated
- `UserService.get_by_name()` 将在 2.0 版本中移除

### Removed
- 移除旧版 API 端点 `/api/v1/users`

### Fixed
- 修复用户注册时的验证错误
- 修复数据库连接池泄漏问题

### Security
- 修复 XSS 漏洞
- 更新 JWT 令牌过期策略

## [1.2.0] - 2024-01-15

### Added
- 新增批量导入功能

### Fixed
- 修复分页查询错误

## [1.1.0] - 2024-01-01

### Added
- 新增用户管理 API
- 新增权限控制

## [1.0.0] - 2023-12-15

### Added
- 首次发布
```

### 变更日志最佳实践

```python
# ✅ 正确 - 废弃函数添加警告
import warnings

def old_function() -> str:
    """旧函数，已废弃.

    Deprecated:
        使用 new_function() 替代。将在 2.0 版本中移除。
    """
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2
    )
    return "old"


def new_function() -> str:
    """新函数."""
    return "new"


# ✅ 正确 - 版本兼容性处理
import sys

def get_feature() -> str:
    """获取特性（版本兼容）."""
    if sys.version_info >= (3, 11):
        # Python 3.11+ 使用新实现
        return _get_feature_new()
    else:
        # 旧版本使用兼容实现
        return _get_feature_legacy()


# ❌ 错误 - 废弃函数没有警告
def old_function() -> str:
    """旧函数."""
    return "old"
```

## 文档生成工具

### Sphinx 配置

```python
# docs/conf.py - Sphinx 配置文件
"""Sphinx 配置."""

project = "MyProject"
copyright = "2024, Author"
author = "Author"

# 扩展
extensions = [
    "sphinx.ext.autodoc",      # 自动从代码生成文档
    "sphinx.ext.napoleon",     # 支持 Google/NumPy 风格文档字符串
    "sphinx.ext.viewcode",     # 添加源码链接
    "sphinx.ext.intersphinx",  # 交叉引用
    "sphinx_autodoc_typehints",  # 类型注解支持
]

# 自动文档设置
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__"
}

# Napoleon 设置
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
```

### MkDocs 配置

```yaml
# mkdocs.yml - MkDocs 配置文件
site_name: MyProject 文档
site_description: MyProject 项目文档
site_author: Author

theme:
  name: material
  language: zh
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: 切换到暗色模式
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: 切换到亮色模式

nav:
  - 首页: index.md
  - 快速开始: quickstart.md
  - API 文档: api.md
  - 开发指南: development.md
  - 贡献指南: contributing.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - admonition
  - pymdownx.details
```

### 生成 API 文档命令

```bash
# ✅ Sphinx - 生成 HTML 文档
cd docs
sphinx-apidoc -o source ../src/my_project
make html

# ✅ MkDocs - 构建文档
mkdocs build

# ✅ MkDocs - 本地预览
mkdocs serve

# ✅ pdoc - 快速生成 API 文档
uv pip install pdoc
pdoc -o docs/html src/my_project
```

## 检查清单

提交代码前，确保：

- [ ] 项目有 README.md
- [ ] README.md 包含项目描述、功能特性、快速开始
- [ ] 公开 API 有文档
- [ ] API 文档包含请求、响应、错误码
- [ ] 公开类有文档字符串
- [ ] 公开函数有文档字符串
- [ ] 复杂逻辑有注释说明
- [ ] 注释与代码一致
- [ ] 文档清晰易懂
- [ ] 文档无过时信息
- [ ] CHANGELOG.md 已更新
- [ ] 类型注解完整
