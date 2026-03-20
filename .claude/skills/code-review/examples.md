# 代码审查示例

本文档提供代码审查的详细示例和最佳实践。

## 示例1：技术报告格式

```markdown
# 代码审查报告

## 概览
- 审查范围：./src
- 审查时间：2026-03-20
- 质量评分：7.5/10
- 技术债数量：15项
- 高危问题：3项

## 质量分析

### 可读性（7.0/10）
- ✅ 命名规范：良好（90%符合规范）
- ⚠️ 注释质量：需改进（60%函数有注释）
- ✅ 代码组织：优秀（模块化清晰）

### 可维护性（8.0/10）
- ✅ 模块化：优秀
- ✅ 耦合度：良好
- ⚠️ 圈复杂度：平均12（建议≤10）

### 可测试性（6.0/10）
- ❌ 测试覆盖率：65%（目标≥80%）
- ⚠️ 单元测试：部分缺失
- ✅ 集成测试：良好

### 安全性（8.5/10）
- ✅ SQL注入：未发现
- ⚠️ XSS漏洞：1处
- ✅ 敏感信息：未发现
```

## 示例2：问题代码和改进

### 违反单一职责原则

**问题代码**：
```python
class UserService:
    def create_user(self, data):
        # 创建用户
        user = User(**data)
        db.session.add(user)
        
        # 发送邮件
        send_welcome_email(user.email)
        
        # 记录日志
        logger.info(f"User created: {user.id}")
        
        # 更新缓存
        cache.invalidate_user_list()
        
        return user
```

**改进代码**：
```python
class UserService:
    def __init__(self, email_service, logger, cache):
        self.email_service = email_service
        self.logger = logger
        self.cache = cache
    
    def create_user(self, data):
        user = User(**data)
        db.session.add(user)
        
        # 依赖注入，职责分离
        self.email_service.send_welcome(user)
        self.logger.log_user_created(user)
        self.cache.invalidate_user_list()
        
        return user
```

## 示例3：清单报告格式

| 序号 | 问题 | 类型 | 优先级 | 文件 | 行号 | 状态 |
|------|------|------|--------|------|------|------|
| 1 | UserService 违反单一职责 | 设计债 | 900 | user_service.py | 15 | ⏳ 待修复 |
| 2 | AuthController 缺少测试 | 测试债 | 800 | auth_controller.py | 1 | ⏳ 待修复 |
| 3 | 数据库查询N+1问题 | 性能 | 750 | user_repository.py | 42 | ⏳ 待修复 |

## 示例4：演示文稿格式

```markdown
# 代码审查报告
## 2026-03-20

---

## 概览

📊 质量评分：**7.5/10**
📝 技术债：**15项**
⚠️ 高危问题：**3项**
✅ 测试覆盖率：**65%** → 目标 **80%**

---

## 🔴 高优先级问题（3项）

1. **UserService 职责过多**
2. **AuthController 无测试**
3. **数据库查询低效**
```
