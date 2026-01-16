---
name: python
description: Python 开发规范和最佳实践指导，包括代码风格、项目结构、依赖管理、测试策略和性能优化
---

# Python 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、命名约定、文档规范 | 快速入门 |
| [type-hints-patterns.md](type-hints-patterns.md) | 类型提示、设计模式、mypy 配置 | 类型设计和架构 |
| [testing-deployment.md](testing-deployment.md) | 依赖管理、项目结构、测试策略、部署 | 开发工具和质量保证 |

## 🎯 总体原则

### 核心哲学

1. **简洁优雅**（Zen of Python）

   - 可读性极其重要
   - 明确优于隐晦
   - 简单优于复杂
   - 复杂优于繁杂

2. **现代 Python**

   - 使用 Python 3.8+ 的现代特性
   - 充分利用类型提示
   - 学习和应用最新的库和工具

3. **工程化实践**

   - 遵循行业标准和最佳实践
   - 建立清晰的项目结构
   - 使用自动化工具保证质量

4. **实用至上**
   - 优先可读性和可维护性
   - 避免过度设计和过度优化
   - 根据实际需求选择方案

## 📋 代码规范

### 命名规范（PEP 8）

**命名规范**：

```python
# 模块和文件名：lowercase_with_underscores
my_module.py
data_processing.py

# 常量：UPPERCASE_WITH_UNDERSCORES
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# 类名：CapWords（PascalCase）
class UserManager:
    pass

class DataProcessor:
    pass

# 函数和方法名：lowercase_with_underscores
def calculate_total(items):
    pass

def process_data(data, config=None):
    pass

# 私有方法：_leading_underscore
def _internal_helper():
    pass

# 受保护方法：__double_leading_underscore（谨慎使用）
def __internal_only():
    pass

# 避免单字母变量名（除了循环变量）
for i in range(10):  # ✅
    process(i)

for index in large_collection:  # ✅
    process_item(index)

i = calculate_something()  # ❌ 避免
```

**代码格式**：

```python
# ✅ 推荐：清晰的空行分隔
class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)


# ❌ 避免：密集的代码
class UserManager:
    def __init__(self):
        self.users = []
    def add_user(self, user):
        self.users.append(user)

# ✅ 推荐：行长不超过 88 字符（black 标准）
# 如果超过，使用隐式续行或换行
result = some_function(
    argument_one,
    argument_two,
    argument_three,
)

# ❌ 避免：超长行
result = some_function(argument_one, argument_two, argument_three, argument_four)
```

### 文档字符串（Docstring）

**函数文档字符串**：

```python
def calculate_average(numbers: List[float]) -> float:
    """计算数字列表的平均值.

    使用 NumPy 风格的 docstring。

    Args:
        numbers: 浮点数列表，不能为空.

    Returns:
        列表中所有数字的平均值.

    Raises:
        ValueError: 如果列表为空.
        TypeError: 如果列表中包含非数字类型.

    Examples:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
        >>> calculate_average([10.5, 20.5])
        15.5
    """
    if not numbers:
        raise ValueError("numbers 不能为空")
    return sum(numbers) / len(numbers)
```

**类文档字符串**：

```python
class DataProcessor:
    """处理和转换数据的类.

    这个类提供了多种数据处理方法，包括清理、转换和验证。

    Attributes:
        config: 处理器配置字典.
        logger: 日志记录器实例.

    Example:
        >>> processor = DataProcessor(config={'format': 'json'})
        >>> result = processor.process(data)
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
```

### 注释原则

```python
# ✅ 好的注释：解释为什么，而不是是什么
# 使用缓存避免重复查询数据库
cached_result = get_from_cache(key)

# ❌ 坏的注释：重复代码
# 从缓存获取结果
cached_result = get_from_cache(key)

# ✅ 为复杂算法添加注释
# 使用两指针技术在 O(n) 时间内找到目标对
def find_pair(numbers: List[int], target: int) -> Optional[tuple]:
    seen = set()
    for num in numbers:
        complement = target - num
        if complement in seen:
            return (complement, num)
        seen.add(num)
    return None

# ✅ 为非显而易见的决定添加注释
# Redis key 的过期时间是 1 小时，因为用户会话通常在 30-45 分钟内完成
CACHE_EXPIRE_SECONDS = 3600
```

## 扩展文档

参见 [type-hints-patterns.md](type-hints-patterns.md) 了解完整的类型提示、设计模式、mypy 配置和性能优化指南。

参见 [testing-deployment.md](testing-deployment.md) 了解项目结构、依赖管理、测试规范、工具链配置和部署最佳实践。
