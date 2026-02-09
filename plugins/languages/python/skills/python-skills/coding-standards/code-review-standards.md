# Python 代码审查规范

## 核心原则

### ✅ 必须遵守

1. **代码质量** - 确保代码符合 PEP 8 编码规范
2. **功能正确** - 确保代码实现正确的功能
3. **测试覆盖** - 确保代码有充分的测试
4. **文档完整** - 确保文档和注释完整
5. **类型安全** - 确保类型注解完整且正确

### ❌ 禁止行为

- 审查不仔细
- 审查延迟
- 审查时只看表面
- 审查时忽略测试
- 审查时忽略类型注解
- 审查时忽略文档

## 审查原则

### 审查重点

1. **功能正确性** - 代码是否实现了预期的功能
2. **代码质量** - 代码是否符合 PEP 8 编码规范
3. **类型安全** - 类型注解是否完整
4. **测试覆盖** - 测试是否充分
5. **文档完整** - 文档和注释是否完整
6. **性能考虑** - 代码性能是否合理
7. **安全性** - 代码是否存在安全隐患

### 审查态度

- **建设性** - 提供建设性的反馈
- **尊重** - 尊重作者的劳动成果
- **及时** - 及时完成审查
- **仔细** - 仔细检查代码
- **学习** - 从审查中学习

## 审查清单

### 功能正确性

- [ ] 代码实现了预期的功能
- [ ] 边界条件已处理（空值、空列表、空字典）
- [ ] 错误处理完善
- [ ] 无逻辑错误
- [ ] 无潜在的 bug

### 代码质量

- [ ] 代码符合 PEP 8 规范
- [ ] 命名清晰有意义
- [ ] 代码结构清晰
- [ ] 无重复代码
- [ ] 代码简洁易懂
- [ ] Ruff 检查通过

### 类型安全

- [ ] 所有公共函数有类型注解
- [ ] 类型注解正确
- [ ] mypy 检查通过
- [ ] 使用 `|` 而非 `Union`（Python 3.10+）
- [ ] 复杂类型有类型别名

### 测试覆盖

- [ ] 单元测试覆盖关键逻辑
- [ ] 集成测试覆盖关键流程
- [ ] 测试用例充分
- [ ] 测试代码质量高
- [ ] 无测试失败
- [ ] 使用 pytest 框架

### 文档完整

- [ ] 公开类有文档字符串
- [ ] 公开函数有文档字符串
- [ ] 复杂逻辑有注释
- [ ] README 已更新
- [ ] API 文档已更新

### 性能考虑

- [ ] 无性能瓶颈
- [ ] 内存使用合理
- [ ] 无不必要的循环
- [ ] 数据库查询优化
- [ ] 算法复杂度合理

### 安全性

- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险
- [ ] 无 CSRF 风险
- [ ] 敏感信息加密
- [ ] 访问控制完善
- [ ] 无硬编码密钥

## 审查流程

### 审查步骤

1. **理解需求** - 理解代码要实现的功能
2. **阅读代码** - 仔细阅读代码实现
3. **运行测试** - 运行测试确保功能正确
4. **类型检查** - 运行 mypy 检查类型
5. **代码检查** - 运行 Ruff 检查代码质量
6. **检查清单** - 按照审查清单检查
7. **提供反馈** - 提供建设性的反馈
8. **确认修复** - 确认作者已修复问题

### 审查反馈

```markdown
# ✅ 正确 - 建设性的反馈

## 总体评价

代码质量很好，实现了预期的功能。有几个小问题需要修复。

## 问题

### 1. 命名问题
- `get_data` 应该改为 `get_user_by_id`，更清晰
- `tmp` 变量名不够清晰，建议改为 `buffer`

### 2. 错误处理
- 第 45 行的错误处理不完整，建议添加日志
- 第 78 行的错误被忽略，建议处理

### 3. 类型注解
- `process` 函数缺少返回类型注解
- `data` 参数类型应该是 `dict[str, Any]` 而非 `dict`

### 4. 测试覆盖
- 缺少边界条件的测试
- 建议添加错误场景测试

## 建议

1. 使用 `list comprehension` 替代手动循环
2. 添加函数文档字符串说明参数和返回值
3. 考虑使用 `@dataclass` 简化数据类定义

## 结论

修复上述问题后可以合并。

# ❌ 错误 - 不建设性的反馈

代码有问题，需要修复。
```

### 审查评论

```markdown
# ✅ 正确 - 具体的评论

## 第 45 行

```python
if err is not None:
    return err
```

建议添加日志记录：

```python
if err is not None:
    logger.error(f"Failed to get user: {err}")
    return err
```

## 第 78 行

```python
data, _ = load_data()
```

错误被忽略，建议处理：

```python
data, err = load_data()
if err is not None:
    logger.error(f"Failed to load data: {err}")
    return None
```

## 第 120 行

```python
def process(data):
```

缺少类型注解：

```python
def process(data: dict[str, Any]) -> str:
```

# ❌ 错误 - 不具体的评论

代码有问题，需要修复。
```

## 审查最佳实践

### 审查时机

- **及时审查** - 收到 PR 后及时审查
- **专注审查** - 专注审查，避免分心
- **分批审查** - 大型 PR 分批审查

### 审查方法

- **整体审查** - 先整体了解代码变更
- **细节审查** - 再仔细检查代码细节
- **运行测试** - 运行测试确保功能正确
- **本地测试** - 本地运行代码验证

### 审查沟通

- **礼貌沟通** - 礼貌地提出问题和建议
- **解释原因** - 解释为什么需要修改
- **提供示例** - 提供修改示例
- **确认理解** - 确认作者理解反馈

## 常见问题

### 命名问题

```python
# ❌ 错误 - 命名不清晰
def get_data(id: int) -> User:
    return db.query(User).filter_by(id=id).first()

# ✅ 正确 - 命名清晰
def get_user_by_id(user_id: int) -> User | None:
    """根据 ID 获取用户."""
    return db.query(User).filter_by(id=user_id).first()
```

### 错误处理问题

```python
# ❌ 错误 - 错误处理不完整
try:
    result = api_call()
except Exception:
    return None

# ✅ 正确 - 错误处理完整
try:
    result = api_call()
except APIError as err:
    logger.error(f"API call failed: {err}")
    return None
except TimeoutError as err:
    logger.warning(f"API call timeout: {err}")
    return None
```

### 类型注解问题

```python
# ❌ 错误 - 缺少类型注解
def process(data):
    return data.upper()

# ✅ 正确 - 完整的类型注解
def process(data: str) -> str:
    """处理字符串."""
    return data.upper()
```

### 测试覆盖问题

```python
# ❌ 错误 - 测试覆盖不足
def test_get_user():
    user = get_user_by_id(1)
    assert user is not None

# ✅ 正确 - 测试覆盖充分
def test_get_user_by_id():
    """测试获取用户."""
    # 测试正常情况
    user = get_user_by_id(1)
    assert user is not None
    assert user.id == 1

    # 测试用户不存在
    user = get_user_by_id(999)
    assert user is None

    # 测试无效 ID
    with pytest.raises(ValueError):
        get_user_by_id(0)
```

### 性能问题

```python
# ❌ 错误 - 性能问题
def find_user(users: list[User], user_id: int) -> User | None:
    for user in users:
        if user.id == user_id:
            return user
    return None

# ✅ 正确 - 使用字典优化查找
def build_user_index(users: list[User]) -> dict[int, User]:
    """构建用户索引."""
    return {user.id: user for user in users}

def find_user(users: dict[int, User], user_id: int) -> User | None:
    """查找用户（O(1) 复杂度）."""
    return users.get(user_id)
```

### 安全问题

```python
# ❌ 错误 - SQL 注入风险
def get_user(username: str) -> User:
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)

# ✅ 正确 - 使用参数化查询
def get_user(username: str) -> User | None:
    """根据用户名获取用户."""
    return db.query(User).filter_by(username=username).first()

# ❌ 错误 - 硬编码密钥
SECRET_KEY = "sk-1234567890abcdef"

# ✅ 正确 - 使用环境变量
from os import getenv

SECRET_KEY = getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
```

## 代码审查工具

### GitHub 集成

```yaml
# .github/codecov.yml - 代码覆盖率配置
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 1%
        base: auto
    patch:
      default:
        target: 80%
        threshold: 1%
        base: auto

# .github/CODEOWNERS - 代码所有者
# 所有 Python 文件由 python-team 审查
*.py    @python-team

# 特定目录由特定团队审查
src/auth/    @auth-team
src/api/     @api-team
```

### 自动化审查

```yaml
# .github/workflows/review.yml
name: Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run Ruff
        run: uv run ruff check .

      - name: Run mypy
        run: uv run mypy src/

      - name: Run tests
        run: uv run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### 本地审查工具

```bash
# ✅ 正确 - 使用 diff review 工具
# 安装
uv pip install diff-cover

# 使用
git diff main | diff-cover coverage.xml

# ✅ 正确 - 使用 pytest-diff
uv pip install pytest-diff

# 在 PR 中运行
uv run pytest --diff-cover
```

## 审查模板

### PR 审查模板

```markdown
<!-- 请填写此模板进行代码审查 -->

## 审查结果

- [ ] 批准
- [ ] 需要修改
- [ ] 拒绝

## 代码质量

- [ ] 符合 PEP 8 规范
- [ ] 类型注解完整
- [ ] 代码结构清晰
- [ ] 无重复代码

## 测试

- [ ] 测试覆盖充分
- [ ] 测试用例合理
- [ ] 无测试失败

## 文档

- [ ] 文档字符串完整
- [ ] 复杂逻辑有注释
- [ ] README 已更新

## 安全性

- [ ] 无明显安全问题
- [ ] 敏感信息已处理

## 其他问题

<!-- 列出其他需要修改的问题 -->

1.
2.
3.

## 建议

<!-- 提供改进建议 -->

1.
2.
3.
```

## 检查清单

审查代码前，确保：

- [ ] 理解代码要实现的功能
- [ ] 仔细阅读代码实现
- [ ] 运行测试确保功能正确
- [ ] 运行 mypy 检查类型
- [ ] 运行 Ruff 检查代码质量
- [ ] 按照审查清单检查
- [ ] 提供建设性的反馈
- [ ] 确认作者已修复问题
- [ ] 礼貌地提出问题和建议
- [ ] 解释为什么需要修改
- [ ] 提供修改示例
- [ ] 确认作者理解反馈
