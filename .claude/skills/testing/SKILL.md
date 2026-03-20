---
name: testing
description: 测试策略 - 测试类型选择、测试用例生成、覆盖率分析、测试框架集成
user-invocable: false
context: fork
model: sonnet
---

# 测试策略（Testing Strategy）

本 Skill 提供系统化的测试策略指导，从单元测试到端到端测试，确保代码质量和可靠性。

## 概览

**核心能力**：
1. **测试类型选择** - 单元测试、集成测试、E2E测试、性能测试
2. **测试用例生成** - 基于需求和代码生成测试用例
3. **覆盖率分析** - 行覆盖、分支覆盖、函数覆盖
4. **测试框架集成** - Jest、Pytest、JUnit、Mocha
5. **Mock策略** - 依赖隔离、数据模拟

**测试金字塔**：
```
      /\      E2E测试 (10%)
     /  \
    /    \    集成测试 (20%)
   /      \
  /________\  单元测试 (70%)
```

## 执行流程

### 阶段1：测试策略选择

**目标**：根据项目特点选择合适的测试策略

**步骤**：
1. **项目分析**：
   - 项目类型（Web应用、API服务、CLI工具、库）
   - 技术栈（语言、框架）
   - 团队规模和经验

2. **测试类型选择**：
   - **单元测试**（70%）：测试单个函数或方法
   - **集成测试**（20%）：测试模块间交互
   - **E2E测试**（10%）：测试完整业务流程
   - **性能测试**（可选）：压力测试、负载测试

3. **覆盖率目标**：
   - 行覆盖率：≥80%
   - 分支覆盖率：≥75%
   - 函数覆盖率：≥90%

### 阶段2：测试用例生成

**目标**：生成全面的测试用例

**步骤**：
1. **AAA模式**（Arrange-Act-Assert）：
   ```python
   def test_user_login():
       # Arrange - 准备测试数据
       user = User(email="test@example.com", password="secret")

       # Act - 执行被测试代码
       result = login(user.email, user.password)

       # Assert - 验证结果
       assert result.success is True
       assert result.user.email == "test@example.com"
   ```

2. **覆盖场景**：
   - **正常情况**：预期输入和输出
   - **边界情况**：最小值、最大值、空值
   - **异常情况**：错误输入、异常处理
   - **并发情况**：多线程、竞态条件

3. **数据驱动测试**：
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, 2),
       (2, 4),
       (3, 6),
   ])
   def test_double(input, expected):
       assert double(input) == expected
   ```

### 阶段3：Mock策略

**目标**：隔离依赖，提高测试速度和稳定性

**步骤**：
1. **Mock类型**：
   - **Stub**：返回预定义数据
   - **Mock**：验证调用行为
   - **Spy**：记录调用情况

2. **Mock外部依赖**：
   ```python
   # Mock 数据库
   @mock.patch('app.database.get_user')
   def test_get_user_profile(mock_get_user):
       mock_get_user.return_value = User(id=1, name="Test")
       profile = get_user_profile(1)
       assert profile.name == "Test"

   # Mock HTTP请求
   @mock.patch('requests.get')
   def test_fetch_data(mock_get):
       mock_get.return_value.json.return_value = {"status": "ok"}
       data = fetch_data()
       assert data["status"] == "ok"
   ```

3. **避免过度Mock**：
   - 只Mock外部依赖（数据库、API、文件系统）
   - 不要Mock被测试代码本身
   - 优先使用真实依赖（内存数据库、测试容器）

### 阶段4：覆盖率分析

**目标**：评估测试覆盖率，识别未测试代码

**步骤**：
1. **生成覆盖率报告**：
   ```bash
   # Python
   pytest --cov=src --cov-report=html

   # JavaScript
   jest --coverage

   # Go
   go test -cover ./...
   ```

2. **分析覆盖率**：
   - 行覆盖率：已执行代码行 / 总代码行
   - 分支覆盖率：已执行分支 / 总分支
   - 函数覆盖率：已调用函数 / 总函数

3. **识别未覆盖代码**：
   - 错误处理分支
   - 边界情况
   - 并发代码

### 阶段5：测试框架集成

**目标**：配置测试框架和CI集成

**步骤**：
1. **框架选择**：
   - **Python**：Pytest（推荐）、Unittest
   - **JavaScript/TypeScript**：Jest（推荐）、Mocha + Chai
   - **Go**：内置testing包、Testify
   - **Java**：JUnit（推荐）、TestNG

2. **CI集成**：
   ```yaml
   # GitHub Actions
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run tests
           run: npm test
         - name: Upload coverage
           run: bash <(curl -s https://codecov.io/bash)
   ```

3. **测试配置**：
   ```javascript
   // jest.config.js
   module.exports = {
     testEnvironment: 'node',
     coverageThreshold: {
       global: {
         lines: 80,
         branches: 75,
         functions: 90
       }
     }
   };
   ```

## 测试类型

### 1. 单元测试（Unit Tests）

**定义**：测试单个函数或方法

**示例**：
```python
def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
```

**最佳实践**：
- 测试单一功能
- 快速执行（<100ms）
- 无外部依赖
- 可重复运行

### 2. 集成测试（Integration Tests）

**定义**：测试模块间交互

**示例**：
```python
def test_user_registration():
    # 测试用户注册流程（涉及数据库、邮件服务）
    user = register_user("test@example.com", "password")
    assert user.email == "test@example.com"
    assert user.verified is False

    # 验证数据库记录
    db_user = db.query(User).filter_by(email="test@example.com").first()
    assert db_user is not None
```

**最佳实践**：
- 测试模块交互
- 使用测试数据库
- 测试后清理数据
- 执行时间适中（<1s）

### 3. E2E测试（End-to-End Tests）

**定义**：测试完整业务流程

**示例**：
```javascript
// Playwright E2E测试
test('user can login', async ({ page }) => {
  await page.goto('https://example.com/login');
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('https://example.com/dashboard');
});
```

**最佳实践**：
- 测试关键业务流程
- 使用真实环境
- 数量少而精
- 允许较慢执行（<10s）

### 4. 性能测试（Performance Tests）

**定义**：测试系统性能

**示例**：
```python
import time

def test_api_response_time():
    start = time.time()
    response = api.get_users()
    duration = time.time() - start

    assert duration < 0.2  # 响应时间 < 200ms
    assert len(response) > 0
```

**最佳实践**：
- 设置性能基线
- 监控性能趋势
- 隔离性能测试
- 使用专业工具（JMeter、k6）

## 测试最佳实践

### 测试命名

**好的命名**：
- `test_user_login_with_valid_credentials_should_succeed`
- `test_divide_by_zero_should_raise_error`
- `test_empty_cart_should_have_zero_total`

**不好的命名**：
- `test1`
- `test_function`
- `test_works`

### 测试隔离

- 每个测试独立运行
- 不依赖执行顺序
- 测试后清理状态
- 使用 setUp/tearDown

### 测试可读性

```python
# 好的测试
def test_user_can_update_profile():
    # Given - 准备用户数据
    user = create_user(name="Old Name")

    # When - 执行更新操作
    updated_user = update_profile(user.id, name="New Name")

    # Then - 验证结果
    assert updated_user.name == "New Name"

# 不好的测试
def test_update():
    u = User(n="A")
    u2 = f(u.id, "B")
    assert u2.n == "B"
```

## 工具集成

### Python
- **框架**：Pytest、Unittest
- **Mock**：unittest.mock、pytest-mock
- **覆盖率**：coverage.py、pytest-cov
- **E2E**：Playwright、Selenium

### JavaScript/TypeScript
- **框架**：Jest、Mocha + Chai
- **Mock**：Jest mocks、Sinon.js
- **覆盖率**：Jest coverage、Istanbul
- **E2E**：Playwright、Cypress

### Go
- **框架**：testing包、Testify
- **Mock**：gomock、testify/mock
- **覆盖率**：go test -cover
- **E2E**：httptest包

## 输出格式

### 测试报告

```markdown
## 测试报告

### 覆盖率
- 行覆盖率：85%（目标：≥80%）✓
- 分支覆盖率：78%（目标：≥75%）✓
- 函数覆盖率：92%（目标：≥90%）✓

### 测试统计
- 单元测试：120个（100%通过）
- 集成测试：25个（100%通过）
- E2E测试：8个（100%通过）

### 未覆盖代码
- `user_service.py:45-50` - 错误处理分支
- `payment.py:120-125` - 超时重试逻辑

### 建议
1. 补充错误处理分支测试
2. 添加超时场景测试
3. 提升分支覆盖率到80%
```

## 相关 Skills

- **code-review** - 代码审查（测试质量检查）
- **refactoring** - 重构指导（重构前补充测试）
- **performance-optimization** - 性能优化（性能测试）
