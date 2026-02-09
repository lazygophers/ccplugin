# Python 命名规范

强调**清晰、一致、符合 PEP 8**。

## 核心原则

### ✅ 必须遵守

1. **模块/包名全小写** - 使用下划线分隔多词：`my_package`, `my_module`
2. **类名 PascalCase** - `User`, `UserProfile`, `HTTPClient`
3. **函数/变量名 snake_case** - `get_user`, `user_name`, `is_active`
4. **常量 UPPER_CASE** - `MAX_RETRIES`, `DEFAULT_TIMEOUT`
5. **私有成员前缀下划线** - `_internal_method`, `_private_var`
6. **避免单字符名** - 除非是循环变量或数学计算
7. **使用描述性名称** - 名称应清楚表达其用途

### ❌ 禁止行为

- 混合命名风格（如 `getUser` 或 `User_Name`）
- 使用保留字作为变量名
- 过度缩写（`usr` 代替 `user`，但 `config` 可以）
- 使用相似名称（`user` 和 `users` 容易混淆）
- 双下划线前缀（名称修饰）除非必要
- 以数字开头的名称

## 模块和包命名

### 模块命名

```python
# ✅ 正确 - 全小写，下划线分隔
# file: user_service.py
def get_user(user_id: int) -> User:
    """获取用户"""
    pass

# file: database_connection.py
def connect():
    """连接数据库"""
    pass

# ❌ 错误 - 大写字母
# file: UserService.py
# file: databaseConnection.py

# ✅ 正确 - 简洁有意义的模块名
# file: auth.py  - 认证模块
# file: db.py    - 数据库模块（缩写可接受）
# file: http.py  - HTTP 客户端

# ❌ 避免 - 过于通用
# file: lib.py
# file: common.py
# file: utils.py  - 除非确实包含工具函数
```

### 包命名

```python
# ✅ 正确 - 包目录结构
project/
├── my_package/           # 包名全小写
│   ├── __init__.py
│   ├── auth.py           # 模块名全小写
│   ├── user_service.py
│   └── database/
│       └── __init__.py
└── tests/
    └── test_auth.py

# ✅ 正确 - 导入语句
from my_package import auth
from my_package.user_service import get_user
from my_package.database import connect

# ❌ 避免 - 包名包含大写
my_package/
├── Auth.py              # 错误
├── userService.py       # 错误
```

## 类命名

### 基本规则

```python
# ✅ 正确 - PascalCase
class User:
    """用户类"""
    pass


class UserProfile:
    """用户资料类"""
    pass


class HTTPClient:
    """HTTP 客户端"""
    pass


class XMLParser:
    """XML 解析器"""
    pass


# ❌ 错误 - 其他风格
class user:               # 错误：全小写
    pass


class user_profile:      # 错误：snake_case
    pass


class UserProfile:       # 错误：混淆为类名
    pass


class USER:              # 错误：全大写
    pass
```

### 异常类命名

```python
# ✅ 正确 - 异常类以 Error 结尾
class ValidationError(Exception):
    """验证错误"""
    pass


class AuthenticationError(Exception):
    """认证错误"""
    pass


class DatabaseConnectionError(Exception):
    """数据库连接错误"""
    pass


# ✅ 正确 - 自定义基类
class AppError(Exception):
    """应用基础异常"""
    pass


# ❌ 避免 - 不清晰的异常名
class Invalid:            # 不清晰
    pass


class FailException:     # 冗余（Exception 已说明）
    pass
```

### 抽象基类命名

```python
# ✅ 正确 - 抽象基类使用 Abstract 前缀或 ABC 后缀
from abc import ABC, abstractmethod


class AbstractParser(ABC):
    """抽象解析器"""

    @abstractmethod
    def parse(self, data: str) -> dict:
        """解析数据"""
        pass


class ParserABC(ABC):
    """解析器抽象基类"""

    @abstractmethod
    def parse(self, data: str) -> dict:
        pass


# ✅ 正确 - 使用 ABC 作为基类
class JSONParser(AbstractParser):
    """JSON 解析器"""

    def parse(self, data: str) -> dict:
        import json
        return json.loads(data)
```

## 函数命名

### 基本规则

```python
# ✅ 正确 - snake_case，动词开头
def get_user(user_id: int) -> User:
    """获取用户"""
    pass


def create_user(name: str, email: str) -> User:
    """创建用户"""
    pass


def validate_email(email: str) -> bool:
    """验证邮箱"""
    pass


def calculate_total(items: list[Item]) -> float:
    """计算总计"""
    pass


# ❌ 错误 - 其他风格
def getUser():            # camelCase（JavaScript 风格）
    pass


def Create_User():        # PascalCase（类名风格）
    pass


def calculateTotal():     # 混合大小写
    pass
```

### 布尔返回函数

```python
# ✅ 正确 - is/has/can/should 前缀
def is_valid(token: str) -> bool:
    """检查是否有效"""
    pass


def is_admin(user: User) -> bool:
    """检查是否是管理员"""
    pass


def has_permission(user: User, permission: str) -> bool:
    """检查是否有权限"""
    pass


def can_delete(user: User, resource: Resource) -> bool:
    """检查是否可以删除"""
    pass


def should_retry(response: Response) -> bool:
    """检查是否应该重试"""
    pass


# ❌ 避免 - 不清晰的布尔函数
def valid(token: str) -> bool:          # 形容词不够明确
    pass


def check_admin(user: User) -> bool:    # check 不如 is 清晰
    pass


def admin(user: User) -> bool:           # 名词不像布尔函数
    pass
```

### 转换函数

```python
# ✅ 正确 - to/from 前缀
def to_dict(obj: User) -> dict:
    """转换为字典"""
    pass


def from_dict(data: dict) -> User:
    """从字典创建"""
    pass


def to_json(obj: User) -> str:
    """转换为 JSON"""
    pass


def to_string(value: Any) -> str:
    """转换为字符串"""
    pass


# ✅ 正确 - parse 前缀表示解析
def parse_json(data: str) -> dict:
    """解析 JSON"""
    pass


def parse_xml(data: str) -> Element:
    """解析 XML"""
    pass
```

## 变量命名

### 基本规则

```python
# ✅ 正确 - snake_case，描述性
user_name = "Alice"
user_id = 12345
is_active = True
connection_pool = []

# ❌ 错误 - 其他风格
userName = "Bob"        # camelCase
user_id = 12345         # 混合大小写
IsActive = True         # PascalCase

# ✅ 正确 - 有意义的名称
user_count = len(users)
total_price = calculate_total(items)
retry_count = 3

# ❌ 避免 - 无意义或过短
n = len(users)          # 除非是数学上下文
x = 1
y = 2
val = get_value()
tmp = "temporary"
```

### 循环变量

```python
# ✅ 正确 - 短名可接受
for i in range(10):
    print(i)


for idx, item in enumerate(items):
    print(f"{idx}: {item}")


for user in users:
    print(user.name)


for key, value in dictionary.items():
    print(key, value)


# ✅ 正确 - 复数形式表示集合
users = get_users()
for user in users:
    process(user)


# ❌ 避免 - 单复数混淆
user = get_users()      # 容易混淆
for u in user:
    process(u)
```

### 临时变量

```python
# ✅ 正确 - 有意义的临时变量
temp_file = create_temp_file()
cache_key = generate_cache_key(data)
result = process_data(input_data)

# ✅ 正确 - 在短作用域中可接受
result = []
result.append(1)
result.append(2)
return result

# ❌ 避免 - 无意义的临时变量
tmp = create_temp_file()
ck = generate_cache_key(data)
res = process_data(input_data)
```

## 常量命名

### 模块级常量

```python
# ✅ 正确 - UPPER_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"
DEBUG_MODE = False


# ✅ 正确 - 分组相关常量
class Config:
    """配置常量"""

    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 30
    API_BASE_URL = "https://api.example.com"


# 或使用枚举
from enum import Enum


class Config(str, Enum):
    """配置枚举"""
    MAX_RETRIES = "3"
    DEFAULT_TIMEOUT = "30"
    API_BASE_URL = "https://api.example.com"


# ❌ 错误 - 其他风格
max_retries = 3         # 应该是大写
MaxRetries = 3          # 混合大小写
MAXRETRIES = 3          # 应该有下划线
```

### 枚举命名

```python
# ✅ 正确 - PascalCase 类名，UPPER_CASE 成员
from enum import Enum


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class HttpStatus(Enum):
    """HTTP 状态码"""
    OK = 200
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


# 使用
if user.role == UserRole.ADMIN:
    pass


# ✅ 正确 - IntEnum
class Priority(IntEnum):
    """优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


# ❌ 避免 - 小写枚举名
class userRole(Enum):    # 应该是 PascalCase
    pass
```

## 私有成员命名

### 单下划线前缀

```python
class UserService:
    """用户服务"""

    def __init__(self):
        self._client = None        # 私有实例变量
        self._cache = {}           # 私有实例变量

    def _validate_input(self, data: dict) -> bool:
        """内部验证方法（私有）"""
        return True

    def get_user(self, user_id: int) -> User:
        """公共方法"""
        self._validate_input({"id": user_id})
        return User()


# ✅ 正确 - 模块级私有函数
def _internal_helper():
    """模块内部辅助函数"""
    pass


def public_api():
    """公共 API"""
    _internal_helper()
```

### 双下划线前缀（名称修饰）

```python
class Base:
    """基类"""

    def __init__(self):
        self.__private = "private"      # 触发名称修饰
        self._protected = "protected"   # 常规私有


class Derived(Base):
    """派生类"""

    def access_base(self):
        """访问基类成员"""
        # self.__private  无法直接访问（被修饰为 _Base__private）
        return self._protected  # 可以访问


# ⚠️ 谨慎使用 - 双下划线可能导致混淆
# 通常单下划线已足够表示"私有"
```

### 特殊方法（Dunder）

```python
class MyClass:
    """类示例"""

    # ✅ 正确 - 特殊方法使用双下划线前后缀
    def __init__(self, value: int):
        """构造函数"""
        self.value = value

    def __repr__(self) -> str:
        """官方字符串表示"""
        return f"MyClass({self.value})"

    def __str__(self) -> str:
        """用户友好字符串表示"""
        return f"Value: {self.value}"

    def __eq__(self, other) -> bool:
        """相等比较"""
        if not isinstance(other, MyClass):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.value)


# ❌ 禁止 - 自定义 dunder 名称
class BadClass:
    def __my_custom_method__(self):    # 不要自定义 dunder
        pass
```

## 类型变量命名

### TypeVar 和泛型

```python
from typing import TypeVar, Generic

# ✅ 正确 - 短大写字母
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

T_co = TypeVar("T_co", covariant=True)


class Box(Generic[T]):
    """通用盒子"""

    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value


class Mapping(Generic[K, V]):
    """通用映射"""

    def put(self, key: K, value: V) -> None:
        pass

    def get(self, key: K) -> V | None:
        pass


# ✅ 正确 - 有意义的 TypeVar 名
UserId = TypeVar("UserId", bound=int)
ModelType = TypeVar("ModelType")


class Repository(Generic[ModelType]):
    """通用仓储"""

    def get(self, id: UserId) -> ModelType | None:
        pass
```

## 特殊约定

### 下划线单独使用

```python
# ✅ 正确 - 忽略不感兴趣的值
for _ in range(10):
    print("Hello")  # 不需要循环计数器


# ✅ 正确 - 忽略多个返回值中的某些
user_id, _, email = user_data  # 忽略中间的值
_, _, third = get_three_values()  # 只需要第三个


# ✅ 正确 - 表示"丢弃"
def old_function():
    """旧函数，保留但不再使用"""
    pass


# ✅ 正确 - 国际化
_ = get_translation_function()

# ✅ 正确 - 通配符导入时使用
from module import *  # 通常不推荐，但如果要用，_* 表示导入所有
```

### 双下划线单独使用

```python
# ✅ 正确 - 用于国际化的文本域标记
import gettext

_ = gettext.gettext

# 使用
print(_("Hello, World!"))  # 可被翻译工具识别
```

### 单尾下划线

```python
# ✅ 正确 - 避免与关键字冲突
class_ = MyClass()      # class 是关键字
type_ = get_type()      # type 是内置函数
lambda_ = lambda x: x   # lambda 是关键字


# ✅ 正确 - 提高可读性
def connect(host, port_):    # port_ 与 port 相关但有区别
    pass
```

## 命名冲突处理

### 与内置函数冲突

```python
# ✅ 正确 - 使用尾下划线避免冲突
def list_items(items):
    """列出项目"""
    for item in items:
        print(item)


def get_id(id_):            # id 是内置函数
    """获取 ID"""
    return id_


# ✅ 正确 - 使用同义词代替
def show_list(items):       # 避免与 list 冲突
    pass


def get_identifier(id_val):  # 避免与 id 冲突
    pass
```

### 与模块名冲突

```python
# ✅ 正确 - 导入时使用别名
import json as json_lib
import time as time_module
from datetime import datetime as DateTime

# 或者
import json
import time as _time  # 私有导入
```

## 检查清单

提交代码前，确保：

- [ ] 模块/包名使用全小写和下划线
- [ ] 类名使用 PascalCase
- [ ] 函数和变量名使用 snake_case
- [ ] 常量使用 UPPER_CASE
- [ ] 布尔函数使用 is/has/can/should 前缀
- [ ] 私有成员使用单下划线前缀
- [ ] 没有使用双下划线前缀（除非必要）
- [ ] 循环变量简洁但清晰
- [ ] 没有使用单字符变量名（除循环/数学）
- [ ] 异常类以 Error 结尾
- [ ] 避免与内置函数/关键字冲突
