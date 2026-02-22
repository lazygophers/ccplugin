---
name: error
description: Python 错误处理规范：异常处理、错误管理、日志记录。处理错误时必须加载。
---

# Python 错误处理规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | PEP 8、命名规范 |

## 异常处理原则

### 必须遵守

1. **具体异常** - 捕获具体的异常类型
2. **日志记录** - 异常必须记录日志
3. **资源清理** - 使用 context manager
4. **自定义异常** - 创建有意义的异常类

### 禁止行为

- 裸 except
- 吞掉异常
- 使用 print 打印错误

## 异常处理模式

```python
# ✅ 正确
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据处理失败: {e}")
    raise
except FileNotFoundError as e:
    logger.warning(f"文件不存在: {e}")
    return None

# ❌ 禁止
try:
    result = process_data(data)
except:
    pass
```

## 自定义异常

```python
class ValidationError(Exception):
    """数据验证错误."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
```

## Context Manager

```python
# ✅ 使用 with 语句
with open("file.txt") as f:
    content = f.read()

# ✅ 自定义 context manager
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.time()
    try:
        yield
    finally:
        logger.info(f"{name} 耗时: {time.time() - start:.2f}s")
```

## 检查清单

- [ ] 捕获具体异常
- [ ] 异常记录日志
- [ ] 使用 context manager
- [ ] 无裸 except
