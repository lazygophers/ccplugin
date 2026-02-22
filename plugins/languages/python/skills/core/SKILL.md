---
name: core
description: Python 开发核心规范：PEP 8、命名规范、代码格式。写任何 Python 代码前必须加载。
---

# Python 开发核心规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 错误处理 | Skills(python:error) | 异常处理、错误管理 |
| 类型提示 | Skills(python:types) | 类型注解、mypy |
| 测试 | Skills(python:testing) | pytest、测试规范 |
| 异步编程 | Skills(python:async) | asyncio、并发模式 |
| Web 开发 | Skills(python:web) | FastAPI、Pydantic |

## 核心原则

### 必须遵守

1. **PEP 8** - 遵循 Python 增强提案 8
2. **类型提示** - 使用类型注解
3. **文档字符串** - 函数和类必须有 docstring
4. **代码格式** - 使用 black/ruff 格式化

### 禁止行为

- 单字母变量名（除循环变量）
- 过长的行（>88 字符）
- 缺少类型提示
- 缺少文档字符串

## 命名规范

```python
# 模块名：lowercase_with_underscores
my_module.py

# 常量：UPPERCASE_WITH_UNDERSCORES
MAX_RETRIES = 3

# 类名：PascalCase
class UserManager:
    pass

# 函数/方法：lowercase_with_underscores
def calculate_total(items):
    pass

# 私有方法：_leading_underscore
def _internal_helper():
    pass
```

## 文档字符串

```python
def calculate_average(numbers: list[float]) -> float:
    """计算数字列表的平均值.

    Args:
        numbers: 浮点数列表.

    Returns:
        平均值.

    Raises:
        ValueError: 如果列表为空.
    """
    if not numbers:
        raise ValueError("列表不能为空")
    return sum(numbers) / len(numbers)
```

## 检查清单

- [ ] 遵循 PEP 8
- [ ] 使用类型提示
- [ ] 函数有 docstring
- [ ] 行长不超过 88 字符
- [ ] 使用 black/ruff 格式化
