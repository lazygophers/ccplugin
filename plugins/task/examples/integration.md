# 插件集成指南

Task Plugin 可以与其他 Claude Code 插件集成,提供更强大的任务管理能力。

## 支持的集成

### 1. Context Plugin - 上下文管理

将任务讨论和决策保存为会话上下文,方便后续查看和恢复。

**适用场景**:
- 记录任务讨论过程
- 保存设计决策
- 团队协作交流记录

### 2. Memory Plugin - 记忆管理

将任务相关的知识点和决策存储到知识图谱,建立知识关联。

**适用场景**:
- 存储技术决策
- 记录问题解决方案
- 积累经验教训

### 3. Knowledge Plugin - 知识库管理

将任务文档和解决方案添加到向量数据库,支持语义搜索。

**适用场景**:
- 创建技术文档
- 分享最佳实践
- 搜索类似问题

## 集成使用示例

### Context Plugin 集成

#### 1. 保存任务讨论

```python
from task.integration.context import get_context_integration

# 获取集成实例
ctx = get_context_integration()

# 保存任务讨论
await ctx.save_task_context(
    task_id="tk-001",
    content="讨论了登录功能的实现方案,决定使用 JWT 进行身份验证",
    role="assistant"
)

# 保存用户评论
await ctx.save_task_comment(
    task_id="tk-001",
    comment="建议添加 2FA 双因素认证",
    author="张三"
)
```

#### 2. 检索任务历史

```python
# 检索任务上下文
contexts = await ctx.retrieve_task_context("tk-001", limit=10)

# 格式化显示
discussion = await ctx.get_task_discussion("tk-001")
print(discussion)
# 输出:
# ## 任务 tk-001 讨论历史
#
# 🤖 讨论了登录功能的实现方案,决定使用 JWT 进行身份验证
# 👤 建议添加 2FA 双因素认证
```

### Memory Plugin 集成

#### 1. 存储技术决策

```python
from task.integration.memory import get_memory_integration

# 获取集成实例
mem = get_memory_integration()

# 存储决策
await mem.store_task_decision(
    task_id="tk-001",
    decision="使用 JWT 进行身份验证,Token 有效期 24 小时",
    tags=["authentication", "security", "jwt"],
    metadata={"author": "tech-lead", "date": "2025-01-15"}
)

# 存储学习收获
await mem.store_task_learning(
    task_id="tk-001",
    learning="JWT 需要妥善保管密钥,建议使用环境变量存储",
    tags=["security", "best-practice"]
)
```

#### 2. 存储问题解决方案

```python
# 存储解决方案
await mem.store_task_solution(
    task_id="tk-002",
    problem="数据库连接池耗尽导致服务不可用",
    solution="增加连接池大小到 50,并设置连接超时时间为 30 秒",
    tags=["database", "performance", "troubleshooting"]
)

# 搜索类似解决方案
solutions = await mem.search_similar_solutions("数据库性能问题")
for sol in solutions:
    print(sol["content"])
```

#### 3. 获取任务知识

```python
# 获取任务相关的所有知识点
knowledge = await mem.get_task_knowledge("tk-001")
print(knowledge)
# 输出:
# ## 任务 tk-001 相关知识
#
# ### 1. 使用 JWT 进行身份验证,Token 有效期 24 小时
# **标签**: task:tk-001, decision, authentication, security, jwt
#
# ### 2. JWT 需要妥善保管密钥,建议使用环境变量存储
# **标签**: task:tk-001, learning, security, best-practice
```

### Knowledge Plugin 集成

#### 1. 添加任务文档

```python
from task.integration.knowledge import get_knowledge_integration

# 获取集成实例
kb = get_knowledge_integration()

# 添加技术文档
await kb.add_task_documentation(
    task_id="tk-001",
    content="""
# JWT 身份验证实现指南

## 概述
JWT (JSON Web Token) 是一种开放标准,用于在各方之间安全地传输信息。

## 实现步骤
1. 安装 PyJWT 库: pip install pyjwt
2. 配置密钥: export JWT_SECRET_KEY=your-secret-key
3. 创建 Token: jwt.encode(payload, secret_key, algorithm='HS256')
4. 验证 Token: jwt.decode(token, secret_key, algorithms=['HS256'])

## 安全建议
- 使用强密钥 (至少 32 字符)
- 设置合理的过期时间 (建议 24 小时)
- 使用 HTTPS 传输
- 不在 Token 中存储敏感信息
""",
    source="技术设计文档",
    metadata={"author": "tech-lead", "version": "1.0"}
)
```

#### 2. 添加解决方案

```python
# 添加完整解决方案
await kb.add_task_solution(
    task_id="tk-002",
    title="数据库连接池优化方案",
    description="""
应用在高并发场景下出现数据库连接池耗尽的问题,导致服务响应缓慢甚至不可用。
错误信息: PoolExhaustedError: QueuePool limit of size 10 overflow 5 reached
""",
    solution="""
1. 增加连接池大小
   - 修改配置: SQLALCHEMY_POOL_SIZE = 50
   - 修改配置: SQLALCHEMY_MAX_OVERFLOW = 10

2. 设置连接超时
   - 修改配置: SQLALCHEMY_POOL_TIMEOUT = 30

3. 添加连接回收机制
   - 修改配置: SQLALCHEMY_POOL_RECYCLE = 3600

4. 监控连接使用情况
   - 添加日志: engine.pool.status()
   - 配置告警: 连接使用率 > 80%

实施后,系统在相同并发下运行稳定,连接使用率保持在 60% 以下。
""",
    tags=["database", "performance", "sqlalchemy"]
)
```

#### 3. 搜索相关知识

```python
# 搜索任务知识
results = await kb.search_task_knowledge("JWT 身份验证")
for doc in results:
    print(f"来源: {doc['source']}")
    print(f"内容: {doc['content'][:100]}...")

# 搜索类似任务
similar = await kb.search_similar_tasks("实现用户登录功能")
for task in similar:
    task_id = task["metadata"]["task_id"]
    print(f"类似任务: {task_id}")
```

#### 4. 添加经验教训

```python
# 任务完成后总结经验
await kb.add_task_lessons_learned(
    task_id="tk-001",
    lessons=[
        "JWT 密钥应该从环境变量读取,不要硬编码",
        "Token 有效期要根据业务需求平衡安全性和用户体验",
        "需要实现 Token 刷新机制,避免用户频繁登录",
        "要对 Token 进行签名验证,防止伪造",
    ],
    tags=["security", "authentication", "best-practice"]
)

# 获取任务参考文档
references = await kb.get_task_references("tk-001")
print(references)
```

## 完整工作流示例

### 场景: 实现新功能并记录知识

```python
from task.server import (
    handle_task_create,
    handle_task_update,
    handle_task_close
)
from task.integration.context import get_context_integration
from task.integration.memory import get_memory_integration
from task.integration.knowledge import get_knowledge_integration

# 1. 创建任务
result = await handle_task_create(session, {
    "title": "实现用户注册功能",
    "description": "支持邮箱注册,需要邮件验证",
    "task_type": "feature",
    "priority": 1
})

task_id = "tk-003"  # 从返回结果中获取

# 2. 记录讨论过程 (Context Plugin)
ctx = get_context_integration()
await ctx.save_task_context(
    task_id=task_id,
    content="讨论注册流程: 填写表单 → 发送验证邮件 → 点击链接验证 → 注册成功",
    role="assistant"
)

# 3. 开始开发
await handle_task_update(session, {
    "task_id": task_id,
    "status": "in_progress"
})

# 4. 记录技术决策 (Memory Plugin)
mem = get_memory_integration()
await mem.store_task_decision(
    task_id=task_id,
    decision="使用 SendGrid 作为邮件服务商,验证链接 24 小时有效",
    tags=["email", "verification", "sendgrid"]
)

# 5. 遇到问题并解决
await mem.store_task_solution(
    task_id=task_id,
    problem="邮件发送失败,提示 API key 无效",
    solution="检查发现环境变量未设置,添加 SENDGRID_API_KEY 后解决",
    tags=["troubleshooting", "email", "configuration"]
)

# 6. 完成开发
await handle_task_close(session, {
    "task_id": task_id,
    "reason": "功能开发完成并通过测试"
})

# 7. 创建文档 (Knowledge Plugin)
kb = get_knowledge_integration()
await kb.add_task_solution(
    task_id=task_id,
    title="用户注册功能实现指南",
    description="实现带邮件验证的用户注册功能",
    solution="""
## 技术栈
- Flask (Web 框架)
- SendGrid (邮件服务)
- SQLAlchemy (数据库 ORM)

## 实现步骤
1. 创建用户模型和数据表
2. 实现注册表单和验证
3. 配置 SendGrid API
4. 生成验证 Token
5. 发送验证邮件
6. 实现验证链接处理

## 关键代码
\`\`\`python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_verification_email(email, token):
    message = Mail(
        from_email='noreply@example.com',
        to_emails=email,
        subject='验证您的邮箱',
        html_content=f'点击链接验证: {verify_url}?token={token}'
    )
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    sg.send(message)
\`\`\`

## 测试清单
- [x] 正常注册流程
- [x] 重复邮箱检查
- [x] 验证邮件发送
- [x] 验证链接过期处理
- [x] 已验证用户重复验证
""",
    tags=["registration", "email", "flask", "sendgrid"]
)

# 8. 总结经验教训
await kb.add_task_lessons_learned(
    task_id=task_id,
    lessons=[
        "验证 Token 要设置过期时间,避免安全风险",
        "邮件发送要做好错误处理和重试机制",
        "环境变量要在部署文档中明确说明",
        "邮件模板要做好国际化支持",
    ],
    tags=["registration", "best-practice"]
)

print(f"✅ 任务 {task_id} 完成,知识已记录")
```

## 集成架构

```
┌──────────────────────────────────────────────────────────┐
│                    Claude Code                           │
└──────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Task Plugin  │   │Context Plugin │   │Memory Plugin  │
│               │   │               │   │               │
│  - 任务管理   │←→│  - 上下文     │←→│  - 记忆图谱   │
│  - 依赖关系   │   │  - 会话记录   │   │  - 知识关联   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Knowledge Plugin     │
                │                       │
                │  - 向量数据库         │
                │  - 语义搜索           │
                └───────────────────────┘
```

## 集成状态

当前版本 (v0.1.0):
- ✅ 集成接口定义
- ✅ 集成辅助类实现
- ✅ 使用示例文档
- ⏳ MCP 跨插件调用 (待实现)
- ⏳ 集成测试 (待实现)

未来版本 (v0.2.0+):
- [ ] 实现 MCP 跨插件通信
- [ ] 自动同步任务状态
- [ ] 智能推荐相关知识
- [ ] 集成统一搜索

## 注意事项

### 1. 插件可用性

集成功能是可选的,Task Plugin 可以独立运行:

```python
from task.integration import is_plugin_available

# 检查插件是否可用
if await is_plugin_available("context"):
    # 使用 Context 集成
    ctx = get_context_integration()
    await ctx.save_task_context(...)
else:
    # 降级处理
    print("Context Plugin 未安装,跳过上下文保存")
```

### 2. 性能考虑

集成调用可能涉及网络通信,建议:
- 使用异步调用避免阻塞
- 批量操作减少调用次数
- 实现缓存机制
- 设置合理超时时间

### 3. 错误处理

集成调用可能失败,需要优雅降级:

```python
try:
    await ctx.save_task_context(task_id, content)
except Exception as e:
    # 记录错误但不中断主流程
    logger.warning(f"保存上下文失败: {e}")
    # 继续执行任务操作
```

### 4. 数据一致性

任务数据是主数据源,集成数据是辅助:
- 任务删除时,相关的上下文/记忆/知识可以保留
- 集成数据失败不影响任务操作
- 定期清理孤立的集成数据

## 开发指南

### 添加新的集成

1. 在 `src/task/integration/` 创建新模块
2. 实现集成辅助类
3. 添加使用示例到本文档
4. 编写集成测试

### 测试集成

```bash
# 运行集成测试
uv run pytest tests/test_integration.py -v

# 测试特定集成
uv run pytest tests/test_integration.py::test_context_integration -v
```

## 参考资源

- [Context Plugin 文档](../../context/README.md)
- [Memory Plugin 文档](../../memory/README.md)
- [Knowledge Plugin 文档](../../knowledge/README.md)
- [MCP 协议规范](https://modelcontextprotocol.io)

---

**最后更新**: 2025-01-15
**版本**: 0.1.0
