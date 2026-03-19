[MindFlow·${任务内容}·${步骤索引}/${迭代轮数}·${任务状态-总任务的状态}] 请确认以下执行计划

### 任务编排

```mermaid
stateDiagram-v2
    [*] --> T1

    state "T1: 需求分析" as T1
    state "T2: 核心功能" as T2
    state "T3: API开发" as T3
    state "T4: 配置管理" as T4
    state "T5: 性能优化" as T5
    state "T6: 单元测试" as T6
    state "T7: API文档" as T7
    state "T8: 集成测试" as T8
    state "T9: 代码审查" as T9

    T1 --> T2
    T1 --> T3
    T1 --> T4
    T2 --> T5
    T2 --> T6
    T3 --> T6
    T3 --> T7
    T4 --> T8
    T5 --> T8
    T6 --> T8
    T7 --> T8
    T8 --> T9
    T9 --> [*]
```

### 任务清单

| 状态 | 任务ID | 任务名称 | 负责Agent | 使用Skills | 相关文件 | 依赖任务 | 验收标准 |
|------|--------|---------|-----------|-----------|---------|---------|---------|
| 📋 | T1 | 需求分析 | analyst（分析师）@project | requirements（需求分析）@project | docs/requirements.md | - | - [ ] 需求文档完整<br>- [ ] 用例清晰 |
| 📋 | T2 | 核心功能实现 | developer（开发者）@task | python:core（核心功能）@python<br>python:async（异步编程）@python | src/core.py<br>src/utils.py | T1 | - [ ] 功能实现完整<br>- [ ] 代码通过 lint |
| 📋 | T3 | API接口开发 | developer（开发者）@task | python:web（Web开发）@python<br>python:security（安全编码）@python | src/api.py<br>src/middleware.py | T1 | - [ ] API 端点完整<br>- [ ] 安全检查通过 |
| 📋 | T4 | 配置管理 | developer（开发者）@task | python:core（核心功能）@python | src/config.py | T1 | - [ ] 配置项完整<br>- [ ] 默认值合理 |
| 📋 | T5 | 性能优化 | developer（开发者）@task | python:async（异步编程）@python<br>python:core（核心功能）@python | src/core.py | T2 | - [ ] 性能指标达标<br>- [ ] 无性能回归 |
| 📋 | T6 | 单元测试 | tester（测试员）@task | python:testing（测试）@python | tests/test_core.py<br>tests/test_api.py | T2, T3 | - [ ] 覆盖率 ≥ 90%<br>- [ ] 所有测试通过 |
| 📋 | T7 | API文档 | writer（文档撰写者）@task | documentation（文档编写）@user | docs/api.md | T3 | - [ ] 文档完整<br>- [ ] 示例清晰 |
| 📋 | T8 | 集成测试 | tester（测试员）@task | python:testing（测试）@python<br>python:web（Web开发）@python | tests/test_integration.py | T4, T5, T6, T7 | - [ ] 集成测试通过<br>- [ ] E2E 场景覆盖 |
| 📋 | T9 | 代码审查 | reviewer（审查员）@task | code-review（代码审查）@code-review<br>python:core（核心功能）@python | 所有变更文件 | T8 | - [ ] 代码质量达标<br>- [ ] 无阻塞性问题 |

### 迭代验收标准

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有 CI 检查通过（lint/test/build）
- [ ] 验收标准与需求 1:1 映射
- [ ] 无新增技术债（代码复杂度 ≤ X）
- [ ] 无影响已有功能（回归测试通过）

### 任务说明（≤100字）
