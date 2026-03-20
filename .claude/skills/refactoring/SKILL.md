---
name: refactoring
description: 代码重构 - 识别重构需求、影响分析、制定计划、执行重构、验证结果
user-invocable: true
context: fork
model: sonnet
skills:
  - code-review
  - testing
---

# 代码重构（Refactoring）

本 Skill 提供系统化的重构指导，从需求识别到验证完成，确保重构安全、高效、可追溯。

## 概览

**核心能力**：
1. **重构识别** - 代码坏味道检测、技术债分析、重构优先级评估
2. **影响分析** - 依赖关系分析、变更影响范围、风险评估
3. **计划制定** - 重构步骤拆解、回滚策略、测试策略
4. **安全重构** - 小步快跑、持续验证、自动化测试
5. **质量验证** - 功能回归测试、性能对比、代码质量提升

**重构类型**：
- **提取重构**：Extract Method、Extract Class、Extract Interface
- **移动重构**：Move Method、Move Field、Move Class
- **简化重构**：Simplify Conditional、Replace Temp with Query、Consolidate Duplicate Code
- **泛化重构**：Pull Up Method、Pull Up Field、Extract Superclass

## 执行流程

### 阶段1：识别重构需求

**目标**：明确重构目标和范围

**步骤**：
1. 使用 `AskUserQuestion` 询问以下信息（如果用户输入不明确）：
   - 重构目标：「改善可读性」「降低复杂度」「消除重复」「优化性能」
   - 重构范围：「单个方法」「类」「模块」「整个项目」
   - 约束条件：「必须保持API兼容」「有时间限制」「有性能要求」

2. 检测代码坏味道：
   - **Long Method**：方法超过50行
   - **Large Class**：类超过500行或职责过多
   - **Duplicate Code**：重复代码超过5%
   - **Long Parameter List**：参数超过4个
   - **Feature Envy**：方法过度依赖其他类
   - **Data Clumps**：相同的数据项总是成组出现
   - **Primitive Obsession**：过度使用基本类型
   - **Switch Statements**：过多的switch/if-else

3. 分析技术债（调用 `code-review` skill）

### 阶段2：影响分析

**目标**：评估重构影响范围和风险

**步骤**：
1. **依赖关系分析**：
   - 使用 `serena:find_referencing_symbols` 查找所有引用
   - 识别直接依赖和间接依赖
   - 绘制依赖关系图

2. **变更影响范围**：
   - 影响的文件数量
   - 影响的模块数量
   - 影响的外部API

3. **风险评估**：
   - **高风险**：核心业务逻辑、外部API、无测试覆盖
   - **中风险**：内部API、部分测试覆盖
   - **低风险**：工具类、完整测试覆盖

### 阶段3：制定重构计划

**目标**：将重构任务拆解为安全的小步骤

**步骤**：
1. **重构步骤拆解**：
   - 每个步骤独立可验证
   - 每个步骤可独立回滚
   - 步骤之间有明确的检查点

2. **测试策略**：
   - **重构前**：补充缺失的测试（覆盖率≥80%）
   - **重构中**：每个步骤后运行测试
   - **重构后**：回归测试 + 性能对比

3. **回滚策略**：
   - Git 分支策略（feature branch）
   - 每个步骤提交一次
   - 失败时可快速回滚到任意检查点

### 阶段4：执行重构

**目标**：安全地执行重构，持续验证

**步骤**：
1. **创建安全环境**：
   ```bash
   git checkout -b refactor/description
   git commit -m "refactor: 重构前的基准版本"
   ```

2. **小步快跑**（每个步骤）：
   - 执行一个重构操作
   - 运行测试（`testing` skill）
   - 代码审查（`code-review` skill）
   - Git 提交

3. **持续验证**：
   - 功能正确性：单元测试 + 集成测试
   - 性能对比：重构前后性能指标对比
   - 代码质量：圈复杂度、代码重复率

### 阶段5：验证结果

**目标**：确保重构达到预期目标

**步骤**：
1. **功能验证**：
   - 所有测试通过（100%通过率）
   - 手动测试关键路径
   - 回归测试

2. **质量验证**：
   - 代码复杂度降低（圈复杂度≤10）
   - 代码重复率降低（<5%）
   - 可读性提升（命名更清晰、注释更完整）

3. **性能验证**：
   - 性能指标对比（响应时间、吞吐量、资源使用）
   - 性能下降不超过5%
   - 性能优化重构应有明显提升（≥20%）

4. **生成重构报告**：
   - 重构前后对比
   - 改进指标（复杂度、重复率、测试覆盖率）
   - 代码示例（重构前 vs 重构后）

## 重构模式

### 1. Extract Method（提取方法）

**适用场景**：方法过长、代码重复、职责不清

**重构前**：
```python
def process_order(order):
    # 验证订单
    if not order.items:
        raise ValueError("订单为空")
    if order.total < 0:
        raise ValueError("订单金额无效")

    # 计算折扣
    discount = 0
    if order.total > 100:
        discount = order.total * 0.1

    # 保存订单
    order.discount = discount
    order.final_total = order.total - discount
    db.save(order)
```

**重构后**：
```python
def process_order(order):
    _validate_order(order)
    discount = _calculate_discount(order.total)
    _save_order(order, discount)

def _validate_order(order):
    if not order.items:
        raise ValueError("订单为空")
    if order.total < 0:
        raise ValueError("订单金额无效")

def _calculate_discount(total):
    return total * 0.1 if total > 100 else 0

def _save_order(order, discount):
    order.discount = discount
    order.final_total = order.total - discount
    db.save(order)
```

### 2. Replace Temp with Query（用查询替换临时变量）

**适用场景**：临时变量使代码难以提取和重用

**重构前**：
```python
def get_price(self):
    base_price = self.quantity * self.item_price
    if base_price > 1000:
        return base_price * 0.95
    else:
        return base_price * 0.98
```

**重构后**：
```python
def get_price(self):
    if self._base_price() > 1000:
        return self._base_price() * 0.95
    else:
        return self._base_price() * 0.98

def _base_price(self):
    return self.quantity * self.item_price
```

### 3. Consolidate Duplicate Code（合并重复代码）

**适用场景**：多处相同或相似的代码

**重构前**：
```python
def send_email_to_admin(message):
    email = admin.email
    subject = "Admin Notification"
    send_email(email, subject, message)

def send_email_to_user(user, message):
    email = user.email
    subject = "User Notification"
    send_email(email, subject, message)
```

**重构后**：
```python
def send_notification(recipient, message, notification_type="user"):
    subject = f"{notification_type.capitalize()} Notification"
    send_email(recipient.email, subject, message)
```

## 最佳实践

### 重构前准备

- **测试先行**：重构前确保测试覆盖率≥80%
- **理解代码**：先理解代码逻辑，再开始重构
- **小步快跑**：每次只做一个小的重构操作
- **持续集成**：每个步骤后运行完整的测试套件

### 重构过程

- **遵循SOLID原则**：单一职责、开闭原则、里氏替换、接口隔离、依赖倒置
- **保持API兼容**：如需破坏性变更，使用废弃标记（@deprecated）
- **渐进式重构**：避免大规模重写，逐步改进
- **代码审查**：重要重构需要团队审查

### 重构后验证

- **功能回归**：所有测试通过
- **性能对比**：确保性能未下降
- **代码质量**：复杂度、重复率指标改善
- **文档更新**：更新相关文档和注释

## 安全检查清单

- [ ] 所有测试通过（单元测试 + 集成测试）
- [ ] 测试覆盖率≥80%
- [ ] 性能下降不超过5%
- [ ] 代码复杂度降低
- [ ] 代码重复率降低
- [ ] API兼容性保持（或有废弃标记）
- [ ] 相关文档已更新
- [ ] 代码已审查

## 工具集成

- **静态分析工具**：ESLint、Pylint、SonarQube
- **重构工具**：IDE内置重构功能、Rope（Python）、Refactoring Guru
- **测试框架**：Jest、Pytest、JUnit
- **性能分析**：Chrome DevTools、py-spy、pprof

## 相关 Skills

- **code-review** - 代码审查（识别重构需求）
- **testing** - 测试策略（重构前后验证）
- **performance-optimization** - 性能优化（性能重构）
- **architecture-review** - 架构评审（大规模重构）
