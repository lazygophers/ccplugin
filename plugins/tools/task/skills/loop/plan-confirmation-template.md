[MindFlow·${任务内容}·${步骤索引}/${迭代轮数}·${任务状态-总任务的状态}] 请确认以下执行计划

### 任务编排

```mermaid
stateDiagram-v2
    [*] --> T1

    state "T1: 需求分析\n━━━━━━━━━━━━\nagent: analyst（分析师）@project\nskills:\n  - requirements（需求分析）@project\nfiles:\n  - docs/requirements.md" as T1

    T1 --> T2
    T1 --> T3
    T1 --> T4

    state "T2: 核心功能实现\n━━━━━━━━━━━━\nagent: developer（开发者）@task\nskills:\n  - python:core（核心功能）@python\n  - python:async（异步编程）@python\nfiles:\n  - src/core.py\n  - src/utils.py" as T2

    state "T3: API接口开发\n━━━━━━━━━━━━\nagent: developer（开发者）@task\nskills:\n  - python:web（Web开发）@python\n  - python:security（安全编码）@python\nfiles:\n  - src/api.py\n  - src/middleware.py" as T3

    state "T4: 配置管理\n━━━━━━━━━━━━\nagent: developer（开发者）@task\nskills:\n  - python:core（核心功能）@python\nfiles:\n  - src/config.py" as T4

    T2 --> T5
    T2 --> T6
    T3 --> T6
    T3 --> T7

    state "T5: 性能优化\n━━━━━━━━━━━━\nagent: developer（开发者）@task\nskills:\n  - python:async（异步编程）@python\n  - python:core（核心功能）@python\nfiles:\n  - src/core.py" as T5

    state "T6: 单元测试\n━━━━━━━━━━━━\nagent: tester（测试员）@task\nskills:\n  - python:testing（测试）@python\nfiles:\n  - tests/test_core.py\n  - tests/test_api.py" as T6

    state "T7: API文档\n━━━━━━━━━━━━\nagent: writer（文档撰写者）@task\nskills:\n  - documentation（文档编写）@user\nfiles:\n  - docs/api.md" as T7

    T4 --> T8
    T5 --> T8
    T6 --> T8
    T7 --> T8

    state "T8: 集成测试\n━━━━━━━━━━━━\nagent: tester（测试员）@task\nskills:\n  - python:testing（测试）@python\n  - python:web（Web开发）@python\nfiles:\n  - tests/test_integration.py" as T8

    T8 --> T9

    state "T9: 代码审查\n━━━━━━━━━━━━\nagent: reviewer（审查员）@task\nskills:\n  - code-review（代码审查）@code-review\n  - python:core（核心功能）@python\nfiles:\n  - 所有变更文件" as T9

    T9 --> [*]
```

### Agent/成员 视角

```mermaid
gantt
    title 任务相对耗时分布（单位：小时）
    dateFormat YYYY-MM-DD
    axisFormat %H:%M

    section analyst（分析师）@project
    T1 需求分析 (1h)      :t1, 2024-01-01 00:00, 1h

    section developer（开发者）@task
    T2 核心功能实现 (2h)  :t2, after t1, 2h
    T3 API接口开发 (2h)   :t3, after t1, 2h
    T4 配置管理 (1h)      :t4, after t1, 1h
    T5 性能优化 (1h)      :t5, after t2, 1h

    section tester（测试员）@task
    T6 单元测试 (1h)      :t6, after t2 t3, 1h
    T8 集成测试 (1h)      :t8, after t4 t5 t6 t7, 1h

    section writer（文档撰写者）@task
    T7 API文档 (1h)       :t7, after t3, 1h

    section reviewer（审查员）@task
    T9 代码审查 (1h)      :t9, after t8, 1h
```

### 任务清单

| 任务ID | 任务名称 | 负责Agent | 使用Skills | 相关文件 | 依赖任务 |
|--------|---------|-----------|-----------|---------|---------|
| T1 | 需求分析 | analyst（分析师）@project | requirements（需求分析）@project | docs/requirements.md | - |
| T2 | 核心功能实现 | developer（开发者）@task | python:core（核心功能）@python<br>python:async（异步编程）@python | src/core.py<br>src/utils.py | T1 |
| T3 | API接口开发 | developer（开发者）@task | python:web（Web开发）@python<br>python:security（安全编码）@python | src/api.py<br>src/middleware.py | T1 |
| T4 | 配置管理 | developer（开发者）@task | python:core（核心功能）@python | src/config.py | T1 |
| T5 | 性能优化 | developer（开发者）@task | python:async（异步编程）@python<br>python:core（核心功能）@python | src/core.py | T2 |
| T6 | 单元测试 | tester（测试员）@task | python:testing（测试）@python | tests/test_core.py<br>tests/test_api.py | T2, T3 |
| T7 | API文档 | writer（文档撰写者）@task | documentation（文档编写）@user | docs/api.md | T3 |
| T8 | 集成测试 | tester（测试员）@task | python:testing（测试）@python<br>python:web（Web开发）@python | tests/test_integration.py | T4, T5, T6, T7 |
| T9 | 代码审查 | reviewer（审查员）@task | code-review（代码审查）@code-review<br>python:core（核心功能）@python | 所有变更文件 | T8 |

### 验收标准

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有 CI 检查通过（lint/test/build）
- [ ] 验收标准与需求 1:1 映射
- [ ] 无新增技术债（代码复杂度 ≤ X）
- [ ] 无影响已有功能（回归测试通过）

### 任务说明（≤100字）