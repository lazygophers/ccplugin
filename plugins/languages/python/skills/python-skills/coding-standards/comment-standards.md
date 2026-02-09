# Python 注释规范

## 核心原则

### ✅ 必须遵守

1. **导出必须有注释** - 所有公共模块、类、函数必须有 docstring
2. **说明意图** - 注释说明"为什么"而不是"是什么"
3. **使用 NumPy 风格** - 统一使用 NumPy 风格的 docstring
4. **保持更新** - 代码变更时同步更新注释
5. **避免误导** - 不准确的注释比没有注释更糟糕

### ❌ 禁止行为

- 注释显而易见的代码
- 注释与代码不一致
- 过度注释
- 注释包含作者、日期等版本控制信息
- 使用行内注释解释"怎么做"（代码本身已经很清楚）

## Docstring 格式

### 模块 Docstring

```python
# ✅ 正确 - 模块 docstring
"""
用户管理模块。

提供用户注册、登录、信息更新等功能。
"""

# ❌ 错误 - 缺少模块 docstring
import os
import sys
```

### 类 Docstring

```python
# ✅ 正确 - 类 docstring（NumPy 风格）
class UserService:
    """
    用户服务类。

    提供用户相关的业务逻辑处理，包括用户创建、查询、更新和删除。

    Parameters
    ----------
    db : Database
        数据库连接实例
    cache : Cache
        缓存实例，用于提高查询性能

    Attributes
    ----------
    db : Database
        数据库连接实例
    cache : Cache
        缓存实例
    """

    def __init__(self, db: Database, cache: Cache):
        self.db = db
        self.cache = cache


# ✅ 正确 - 简单类 docstring
class User:
    """用户数据模型。"""

    pass


# ❌ 错误 - 缺少类 docstring
class UserService:
    def __init__(self, db: Database):
        self.db = db
```

### 函数 Docstring

```python
# ✅ 正确 - 完整的函数 docstring（NumPy 风格）
def create_user(username: str, email: str, password: str) -> User:
    """
    创建新用户。

    执行用户创建流程，包括数据验证、密码加密和数据库存储。
    使用 bcrypt 算法加密密码，salt rounds 为 12。

    Parameters
    ----------
    username : str
        用户名，长度 3-20 字符，仅允许字母数字和下划线
    email : str
        邮箱地址，必须是有效的邮箱格式
    password : str
        明文密码，最小长度 8 字符

    Returns
    -------
    User
        创建成功的用户对象，包含用户 ID 和创建时间

    Raises
    ------
    ValueError
        如果用户名、邮箱或密码不符合验证规则
    DuplicateError
        如果用户名或邮箱已存在

    Examples
    --------
    >>> user = create_user("john_doe", "john@example.com", "secure123")
    >>> print(user.id)
    12345
    """
    # 实现代码
    pass


# ✅ 正确 - 简单函数 docstring
def is_valid_email(email: str) -> bool:
    """
    检查邮箱格式是否有效。

    Parameters
    ----------
    email : str
        待验证的邮箱地址

    Returns
    -------
    bool
        如果邮箱格式有效返回 True，否则返回 False
    """
    return "@" in email and "." in email


# ❌ 错误 - 缺少 docstring
def create_user(username: str, email: str) -> User:
    pass
```

## 注释原则

### 解释"为什么"而非"是什么"

```python
# ✅ 正确 - 说明设计决策和原因
# 使用 lru_cache 缓存用户查询结果，减少数据库访问
# 用户数据变更不频繁，缓存有效期设置为 5 分钟
@lru_cache(maxsize=1000)
def get_user(user_id: int) -> User:
    return db.query(User).filter_by(id=user_id).first()


# ❌ 错误 - 说明"怎么做"（代码已经很清楚）
# 定义一个函数，使用 lru_cache 装饰器
@lru_cache(maxsize=1000)
def get_user(user_id: int) -> User:
    return db.query(User).filter_by(id=user_id).first()
```

### 解释复杂逻辑

```python
# ✅ 正确 - 解释复杂算法
# 使用双指针法反转链表
# 时间复杂度 O(n)，空间复杂度 O(1)
def reverse_list(head: ListNode) -> ListNode:
    prev = None
    current = head

    while current:
        # 保存下一个节点的引用
        next_node = current.next
        # 反转指针方向
        current.next = prev
        # 移动指针
        prev = current
        current = next_node

    return prev
```

### 说明性能和安全考虑

```python
# ✅ 正确 - 说明安全注意事项
# 注意：使用 secrets.token_urlsafe() 生成安全的随机 token
# 不要使用 random 模块，因为它不具备密码学安全性
def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


# ✅ 正确 - 说明性能特征
# 使用生成器表达式而非列表推导式，避免在内存中存储完整列表
# 处理大文件时可以显著减少内存占用
def process_large_file(file_path: str):
    with open(file_path) as f:
        for line in (line.strip() for line in f):
            yield process_line(line)
```

## 行内注释规范

### 放置位置

```python
# ✅ 正确 - 行内注释在代码上方
# 检查用户是否有权限访问该资源
if not user.has_permission(resource):
    raise PermissionError("无权限访问")

# ❌ 错误 - 行内注释在代码后方（除非注释非常简短）
if not user.has_permission(resource):  # 检查权限
    raise PermissionError("无权限访问")


# ✅ 正同 - 行尾注释用于解释常量值
MAX_RETRIES = 3  # 最大重试次数，避免无限循环
TIMEOUT = 30     # 超时时间（秒），根据 SLA 要求设置
```

### 注释复杂表达式

```python
# ✅ 正确 - 为复杂表达式添加注释
# 计算加权平均分：作业占 40%，期中考试占 30%，期末考试占 30%
final_score = homework * 0.4 + midterm * 0.3 + final * 0.3

# ❌ 错误 - 注释显而易见的代码
# 计算总和
total = a + b + c
```

## TODO/FIXME/HACK 标记

### 标记格式规范

```python
# ✅ 正确 - TODO 标记（未来要添加的功能）
# TODO: 添加用户头像上传功能，需要集成 S3 存储
def upload_avatar(user_id: int, file: File) -> str:
    pass


# ✅ 正确 - FIXME 标记（需要修复的问题）
# FIXME: 这里存在潜在的竞态条件，在并发场景下可能导致数据不一致
# 使用乐观锁或分布式锁解决
def update_balance(user_id: int, amount: float) -> None:
    user = get_user(user_id)
    user.balance += amount
    db.commit()


# ✅ 正确 - HACK 标记（临时解决方案）
# HACK: 由于第三方 API 限制，暂时使用轮询方式获取结果
# 后续迁移到 WebSocket 后移除此代码
def wait_for_result(task_id: str) -> dict:
    while True:
        result = api.get_result(task_id)
        if result.status == "completed":
            return result
        time.sleep(1)


# ✅ 正确 - NOTE 标记（重要说明）
# NOTE: 这个函数会被多个线程同时调用，确保它是线程安全的
def get_cached_config(key: str) -> str:
    return cache.get(key)


# ✅ 正确 - XXX 标记（需要警惕的代码）
# XXX: 这种实现方式在数据量大时性能很差，需要优化
def find_duplicates(items: list) -> list:
    duplicates = []
    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items):
            if i != j and item1 == item2:
                duplicates.append(item1)
    return duplicates
```

### 标记添加责任信息

```python
# ✅ 正确 - 包含责任人和时间线
# TODO(@yourname, 2024-06): 添加用户头像上传功能
# FIXME(@team-leads): 修复并发问题，优先级：高


# ❌ 错误 - 缺少具体描述
# TODO: 修复这个问题
# FIXME: 需要改进
```

## 注释更新要求

### 代码变更时同步更新

```python
# ❌ 错误 - 注释与代码不一致
# 返回所有活跃用户
def get_users() -> list[User]:
    return db.query(User).filter_by(is_deleted=False).all()


# ✅ 正确 - 注释与代码一致
# 返回所有未删除的用户（包括活跃和非活跃状态）
def get_users() -> list[User]:
    return db.query(User).filter_by(is_deleted=False).all()
```

### 移除过时注释

```python
# ❌ 错误 - 保留已过时的注释
# TODO: 添加邮箱验证功能
def send_email(user: User, content: str) -> None:
    # 邮箱验证功能已实现
    if not user.email_verified:
        raise ValueError("邮箱未验证")
    mail.send(user.email, content)


# ✅ 正确 - 功能完成后移除 TODO
def send_email(user: User, content: str) -> None:
    if not user.email_verified:
        raise ValueError("邮箱未验证")
    mail.send(user.email, content)
```

## 特殊注释

### Deprecated 注释

```python
# ✅ 正确 - 标记已弃用的代码
def old_authenticate(username: str, password: str) -> User:
    """
    .. deprecated::
        使用 :func:`authenticate` 替代。

        此方法使用 MD5 加密，不安全。
        将在 v2.0 版本中移除。

    Parameters
    ----------
    username : str
        用户名
    password : str
        密码

    Returns
    -------
    User
        认证成功的用户对象
    """
    # 不建议使用
    pass
```

### Security 注释

```python
# ✅ 正确 - 说明安全注意事项
# SECURITY: 密码必须使用 bcrypt 或 argon2 加密
# 绝不存储明文密码，也不使用 MD5/SHA1 等不安全的哈希算法
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))


# SECURITY: 用户输入必须经过验证和转义，防止 SQL 注入
# 使用参数化查询而非字符串拼接
def get_user_by_username(username: str) -> User:
    return db.query(User).filter(User.username == username).first()
```

### Performance 注释

```python
# ✅ 正确 - 说明性能特征
# PERFORMANCE: 时间复杂度 O(n log n)，空间复杂度 O(n)
# 使用归并排序而非快速排序，保证最坏情况下的性能
def sort_items(items: list) -> list:
    return sorted(items)
```

## 类型注释

### 类型提示与注释结合

```python
# ✅ 正确 - 使用类型提示 + docstring 说明
def calculate_discount(price: float, discount_rate: float) -> float:
    """
    计算折扣后的价格。

    Parameters
    ----------
    price : float
        原价，必须为正数
    discount_rate : float
        折扣率，范围 0-1（例如 0.2 表示 8 折）

    Returns
    -------
    float
        折扣后的价格，保留两位小数
    """
    discounted = price * (1 - discount_rate)
    return round(discounted, 2)


# ✅ 正确 - 复杂类型使用 TypeAlias
from typing import TypeAlias

# 用户 ID 与用户对象的映射
UserMap: TypeAlias = dict[int, User]

def group_by_id(users: list[User]) -> UserMap:
    """按用户 ID 分组用户对象。"""
    return {user.id: user for user in users}
```

## 检查清单

提交代码前，确保：

- [ ] 所有公共模块有 docstring
- [ ] 所有公共类有 docstring
- [ ] 所有公共函数有 docstring
- [ ] Docstring 使用 NumPy 风格
- [ ] 注释说明"为什么"而非"是什么"
- [ ] 没有注释显而易见的代码
- [ ] TODO/FIXME/HACK 有明确的描述
- [ ] 注释与代码一致
- [ ] 没有版本控制信息（作者、日期）
- [ ] 复杂逻辑有注释说明
