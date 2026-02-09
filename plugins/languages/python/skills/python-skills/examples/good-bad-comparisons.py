"""
Python 代码风格综合对比示例

本文件展示了命名、格式化、类型注解、错误处理的 Good/Bad 对比。
遵循 python-skills 中的各项规范。
"""

from typing import Any, TypeVar, Generic, Optional, Union
import logging


# =============================================================================
# 1. 命名规范对比
# =============================================================================

# ✅ 正确 - 类名使用 PascalCase
class UserService:
    """用户服务类."""

    def __init__(self):
        self._client = None  # 私有属性使用单下划线


class UserProfile:
    """用户资料类."""

    pass


class HTTPClient:
    """HTTP 客户端类."""

    pass


# ❌ 错误 - 类名使用其他风格
class _userServiceBad:  # 错误：全小写
    """用户服务类."""
    pass


class _user_profileBad:  # 错误：snake_case
    """用户资料类."""
    pass


class _USERBad:  # 错误：全大写
    """用户类."""
    pass


# ✅ 正确 - 函数名使用 snake_case
def get_user(user_id: int) -> dict:
    """获取用户."""
    return {"id": user_id}


def create_user(name: str, email: str) -> dict:
    """创建用户."""
    return {"name": name, "email": email}


def validate_email(email: str) -> bool:
    """验证邮箱."""
    return "@" in email


def calculate_total(items: list) -> float:
    """计算总计."""
    return sum(items)


# ❌ 错误 - 函数名使用其他风格
def _getUserBad():  # 错误：camelCase（JavaScript 风格）
    pass


def _Create_UserBad():  # 错误：PascalCase（类名风格）
    pass


def _calculateTotalBad():  # 错误：混合大小写
    pass


# ✅ 正确 - 布尔函数使用 is/has/can/should 前缀
def is_valid(token: str) -> bool:
    """检查是否有效."""
    return len(token) > 0


def is_admin(user: dict) -> bool:
    """检查是否是管理员."""
    return user.get("is_admin", False)


def has_permission(user: dict, permission: str) -> bool:
    """检查是否有权限."""
    return permission in user.get("permissions", [])


def can_delete(user: dict, resource: dict) -> bool:
    """检查是否可以删除."""
    return user.get("id") == resource.get("owner_id")


def should_retry(response: dict) -> bool:
    """检查是否应该重试."""
    return response.get("status_code", 200) >= 500


# ❌ 错误 - 布尔函数命名不清晰
def _validBad(token: str) -> bool:  # 形容词不够明确
    return len(token) > 0


def _check_adminBad(user: dict) -> bool:  # check 不如 is 清晰
    return user.get("is_admin", False)


def _adminBad(user: dict) -> bool:  # 名词不像布尔函数
    return user.get("is_admin", False)


# ✅ 正确 - 变量名使用 snake_case
_user_name = "Alice"
_user_id = 12345
_is_active = True
_connection_pool = []


# ❌ 错误 - 变量名使用其他风格（注释掉避免未使用警告）
# userName = "Bob"  # camelCase
# userId = 12345  # 混合大小写
# IsActive = True  # PascalCase


# ✅ 正确 - 常量使用 UPPER_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"
DEBUG_MODE = False


# ❌ 错误 - 常量使用其他风格（注释掉避免未使用警告）
# max_retries = 3  # 应该是大写
# MaxRetries = 3  # 混合大小写
# MAXRETRIES = 3  # 应该有下划线


# =============================================================================
# 2. 格式化规范对比
# =============================================================================

# ✅ 正确 - 标准缩进和空格
def process_data(items: list[dict]) -> list[dict]:
    """处理数据."""
    results = []

    for item in items:
        # 标准缩进（4 个空格）
        if item.get("active"):
            processed = {
                "id": item["id"],
                "name": item["name"].upper(),
            }
            results.append(processed)

    return results


# ❌ 错误 - 不一致的缩进
def _process_dataBad(items):
    """处理数据 - 错误缩进."""
    results = []
    for item in items:
    # 错误：缩进不一致（有时 2 空格，有时 4 空格）
      if item.get("active"):
        processed = {
    "id": item["id"],  # 错误：缩进混乱
        }
        results.append(processed)
    return results


# ✅ 正确 - 运算符周围有空格
_a, _b, _c = 1, 2, 3
_result = _a + _b * _c
_x, _y = 5, 8
_value = (_x > 0) and (_y < 10)
_flag = True or False


# ❌ 错误 - 运算符周围缺少空格（注释掉避免语法错误）
# result = a+b*c  # 难以阅读
# value = (x>0)and(y<10)  # 更难阅读


# ✅ 正确 - 逗号后有空格
def func_good(a: int, b: int, c: int) -> None:
    """函数定义 - 逗号后有空格."""
    pass


_items_good = [1, 2, 3, 4, 5]
_data_good = {"key": "value", "name": "test"}


# ❌ 错误 - 逗号后缺少空格（使用不同的函数名避免重定义）
def _funcBad(a:int,b:int,c:int) -> None:  # 难以阅读
    pass


_items_bad = [1,2,3,4,5]  # 难以阅读
_data_bad = {"key":"value","name":"test"}  # 难以阅读


# ✅ 正确 - 适当的空行分隔
class User:
    """用户类."""

    def __init__(self, name: str):
        """初始化."""
        self.name = name

    def get_name(self) -> str:
        """获取姓名."""
        return self.name

    def set_name(self, name: str) -> None:
        """设置姓名."""
        self.name = name


# ❌ 错误 - 缺少空行分隔
class _UserBad:
    """用户类 - 缺少空行."""

    def __init__(self, name: str):
        """初始化."""
        self.name = name
    # 错误：方法之间应该有空行
    def get_name(self):
        """获取姓名."""
        return self.name
    # 错误：方法之间应该有空行
    def set_name(self, name: str):
        """设置姓名."""
        self.name = name


# =============================================================================
# 3. 类型注解对比
# =============================================================================

# ✅ 正确 - 完整的类型注解
def fetch_user(user_id: int) -> dict[str, Any] | None:
    """获取用户."""
    users = {1: {"name": "Alice"}}
    return users.get(user_id)


def create_user_full(name: str, email: str, age: int = 18) -> dict[str, Any]:
    """创建用户."""
    return {"name": name, "email": email, "age": age}


def process_items(items: list[dict[str, Any]]) -> list[str]:
    """处理项目."""
    return [item.get("name", "") for item in items]


# ❌ 错误 - 缺少类型注解
def _fetch_userBad(user_id):  # 缺少参数和返回类型
    users = {1: {"name": "Alice"}}
    return users.get(user_id)


def _create_userBad(name, email, age=18):  # 缺少类型注解
    return {"name": name, "email": email, "age": age}


# ✅ 正确 - 使用 TypeVar 和 Generic
T = TypeVar("T")


class Box(Generic[T]):
    """通用盒子."""

    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value


# 使用示例
_int_box: Box[int] = Box(42)
_str_box: Box[str] = Box("hello")


# ❌ 错误 - 使用 Any 而非泛型
class _BoxBad:
    """通用盒子 - 使用 Any."""

    def __init__(self, value: Any):
        self.value = value

    def get(self) -> Any:  # 失去类型安全
        return self.value


# ✅ 正确 - Optional 和 Union 的正确写法（Python 3.10+）
def get_user_name(user: dict[str, Any] | None) -> str | None:
    """获取用户姓名."""
    if user is None:
        return None
    return user.get("name")


def parse_value(value: str | int | float) -> float:
    """解析数值."""
    return float(value)


# ✅ 兼容 - Optional 和 Union（Python 3.9-）
def get_user_name_compat(user: Optional[dict[str, Any]]) -> Optional[str]:
    """获取用户姓名（兼容写法）."""
    if user is None:
        return None
    return user.get("name")


def parse_value_compat(value: Union[str, int, float]) -> float:
    """解析数值（兼容写法）."""
    return float(value)


# =============================================================================
# 4. 错误处理对比
# =============================================================================

logger = logging.getLogger(__name__)


# ✅ 正确 - 多行处理 + 统一日志格式
def read_file_correct(path: str) -> str:
    """读取文件 - 正确的错误处理."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as e:
        logger.error("file not found: %s", e)
        return ""
    except PermissionError as e:
        logger.error("permission denied: %s", e)
        raise
    except OSError as e:
        logger.error("os error: %s", e)
        raise


# ❌ 错误 - 静默失败
def _read_fileBad_silent(path: str) -> str:
    """读取文件 - 静默失败."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        pass  # 忽略错误 - 调用者不知道发生了什么
    return ""


# ❌ 错误 - 裸 except
def _read_fileBad_bare(path: str) -> str:
    """读取文件 - 裸 except."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:  # 捕获所有异常，包括 KeyboardInterrupt
        pass
    return ""


# ✅ 正确 - 具体的异常类型
def divide_correct(a: float, b: float) -> float:
    """除法 - 正确的异常处理."""
    try:
        return a / b
    except ZeroDivisionError as e:
        logger.error("division by zero: %s", e)
        raise ValueError("Cannot divide by zero") from e


# ❌ 错误 - 过于宽泛的异常捕获
def _divideBad(a: float, b: float) -> float:
    """除法 - 过于宽泛的异常捕获."""
    try:
        return a / b
    except Exception as e:  # 捕获所有异常
        logger.error("error: %s", e)
        raise


# ✅ 正确 - 异常链
def validate_age_correct(age: int) -> None:
    """验证年龄 - 正确的异常链."""
    try:
        if age < 0:
            raise ValueError("Age cannot be negative")
        if age > 150:
            raise ValueError("Age seems unrealistic")
    except ValueError as e:
        logger.error("age validation failed: %s", e)
        raise ValueError(f"Invalid age: {age}") from e


# ❌ 错误 - 不保留原始异常
def _validate_ageBad(age: int) -> None:
    """验证年龄 - 丢失原始异常."""
    try:
        if age < 0:
            raise ValueError("Age cannot be negative")
    except ValueError:
        # 丢失了原始异常信息
        raise ValueError("Invalid age")


# =============================================================================
# 5. 文档字符串对比
# =============================================================================

# ✅ 正确 - Google 风格文档字符串
def calculate_discount(
    price: float,
    discount_rate: float,
    tax_rate: float = 0.1,
) -> float:
    """计算折后价格（含税）.

    Args:
        price: 原始价格
        discount_rate: 折扣率（0-1 之间）
        tax_rate: 税率，默认 0.1

    Returns:
        折后含税价格

    Raises:
        ValueError: 当价格或折扣率为负数时

    Examples:
        >>> calculate_discount(100, 0.2)
        88.0
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    if discount_rate < 0 or discount_rate > 1:
        raise ValueError("Discount rate must be between 0 and 1")

    discounted = price * (1 - discount_rate)
    return discounted * (1 + tax_rate)


# ✅ 正确 - 简洁的文档字符串
def is_valid_email(email: str) -> bool:
    """检查邮箱是否有效.

    Args:
        email: 邮箱地址

    Returns:
        是否有效
    """
    return "@" in email and "." in email


# ❌ 错误 - 无文档字符串
def _calculate_discountBad(price, discount_rate, tax_rate=0.1):
    """无文档字符串示例."""
    # 没有文档字符串，不清楚函数用途
    if price < 0:
        raise ValueError("Price cannot be negative")
    return price * (1 - discount_rate) * (1 + tax_rate)


# =============================================================================
# 6. 列表推导式对比
# =============================================================================

# ✅ 正确 - 简洁的列表推导式
_numbers = [1, 2, 3, 4, 5]
_squares = [x ** 2 for x in _numbers]
_even_numbers = [x for x in _numbers if x % 2 == 0]


# ✅ 正确 - 可读的复杂列表推导式（适当换行）
_users_list = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
]

_adult_names = [
    user["name"]
    for user in _users_list
    if user.get("age", 0) >= 18
]


# ❌ 错误 - 过于复杂的列表推导式
# 以下代码难以阅读，应该拆分为多行或使用循环
_adult_namesBad = [
    user["name"]
    for user in _users_list
    if user.get("age", 0) >= 18 and user["name"].startswith("A")
]


# =============================================================================
# 7. 导入顺序对比
# =============================================================================

# ✅ 正确 - 标准导入顺序（示例注释）
# 1. 标准库导入
# import asyncio
# import logging
# from datetime import datetime
# from typing import Any

# 2. 第三方库导入
# from fastapi import FastAPI
# from pydantic import BaseModel

# 3. 本地导入
# from app.models import User
# from app.services import UserService


# ❌ 错误 - 混乱的导入顺序（示例注释）
# from fastapi import FastAPI  # 第三方库
# import logging  # 标准库
# from app.models import User  # 本地导入
# from datetime import datetime  # 标准库
# from pydantic import BaseModel  # 第三方库
# from app.services import UserService  # 本地导入


# =============================================================================
# 8. 字符串格式化对比
# =============================================================================

# ✅ 正确 - 使用 f-string（Python 3.6+）
_name = "Alice"
_age = 30
_message = f"User {_name} is {_age} years old"


# ✅ 正确 - 复杂格式化使用 .format()
_template = "User {name} is {age} years old and lives in {city}"
_message2 = _template.format(name="Bob", age=25, city="New York")


# ❌ 错误 - 使用 % 格式化（过时）
_message_old = "User %s is %d years old" % (_name, _age)


# ❌ 错误 - 过度使用 + 连接字符串
_message_concat = "User " + _name + " is " + str(_age) + " years old"  # 不推荐


# =============================================================================
# 9. 类定义对比
# =============================================================================

# ✅ 正确 - 标准类定义顺序
class UserClass:
    """用户类."""

    # 类属性
    DEFAULT_AGE: int = 18

    def __init__(self, name: str, age: int = DEFAULT_AGE):
        """初始化."""
        self.name = name
        self._age = age  # 私有属性

    @property
    def age(self) -> int:
        """获取年龄."""
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        """设置年龄."""
        if value < 0:
            raise ValueError("Age cannot be negative")
        self._age = value

    def greet(self) -> str:
        """打招呼."""
        return f"Hello, I'm {self.name}"

    def __repr__(self) -> str:
        """官方字符串表示."""
        return f"UserClass(name='{self.name}', age={self._age})"


# ❌ 错误 - 混乱的类定义顺序
class _UserClassBad:
    """用户类 - 定义顺序混乱."""

    def greet(self):
        """打招呼."""
        return f"Hello, I'm {self.name}"

    DEFAULT_AGE = 18  # 属性应该在方法之前

    def __init__(self, name, age=DEFAULT_AGE):
        """初始化."""
        self.name = name
        self._age = age

    # 缺少 property 装饰器
    def get_age(self):
        """获取年龄."""
        return self._age


# =============================================================================
# 运行示例
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=== 命名规范示例 ===")
    user = UserService()
    print(f"Class name: {user.__class__.__name__}")

    print("\n=== 类型注解示例 ===")
    result = fetch_user(1)
    print(f"Fetch result: {result}")

    print("\n=== 字符串格式化示例 ===")
    print(f"User {_name} is {_age} years old")

    print("\n=== 列表推导式示例 ===")
    print(f"Squares: {_squares}")
    print(f"Even numbers: {_even_numbers}")
    print(f"Adult names: {_adult_names}")

    print("\n=== 折扣计算示例 ===")
    discounted_price = calculate_discount(100, 0.2)
    print(f"Discounted price: {discounted_price}")

    print("\n=== 类定义示例 ===")
    user_instance = UserClass("Alice", 30)
    print(user_instance.greet())
    print(repr(user_instance))
