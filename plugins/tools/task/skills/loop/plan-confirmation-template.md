[MindFlow·${任务内容}·${步骤索引}/${迭代轮数}·${任务状态-总任务的状态}] 请确认以下执行计划

### 执行流程图（任务队列 + 并行执行模型）

```mermaid
flowchart TD
    Start([开始]) --> T1

    T1["T1: 需求分析<br/>━━━━━━━━━━━━<br/>agent: analyst<br/>skills: requirements<br/>files: docs/requirements.md"]

    T1 --> T2 & T3 & T4

    T2["T2: 核心功能实现<br/>━━━━━━━━━━━━<br/>agent: developer<br/>skills: python:core<br/>files: src/core.py"]
    T3["T3: API 接口开发<br/>━━━━━━━━━━━━<br/>agent: developer<br/>skills: python:web<br/>files: src/api.py"]
    T4["T4: 配置管理<br/>━━━━━━━━━━━━<br/>agent: developer<br/>skills: python:core<br/>files: src/config.py"]

    T2 --> T5
    T2 & T3 --> T6

    T5["T5: 性能优化<br/>━━━━━━━━━━━━<br/>agent: developer<br/>skills: python:perf<br/>files: src/core.py"]
    T6["T6: 单元测试<br/>━━━━━━━━━━━━<br/>agent: tester<br/>skills: python:testing<br/>files: tests/test_core.py"]

    T3 --> T7

    T7["T7: API 文档<br/>━━━━━━━━━━━━<br/>agent: writer<br/>skills: documentation<br/>files: docs/api.md"]

    T4 & T5 & T6 & T7 --> T8

    T8["T8: 集成测试<br/>━━━━━━━━━━━━<br/>agent: tester<br/>skills: python:testing<br/>files: tests/test_integration.py"]

    T8 --> T9

    T9["T9: 代码审查<br/>━━━━━━━━━━━━<br/>agent: reviewer<br/>skills: code-review<br/>files: 所有变更文件"]

    T9 --> End([结束])

    classDef startEnd fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef task fill:#e3f2fd,stroke:#2196f3,stroke-width:2px

    class Start,End startEnd
    class T1,T2,T3,T4,T5,T6,T7,T8,T9 task
```

### 执行者视角（User Journey）

```mermaid
journey
    title Agent 执行旅程
    section 需求阶段
      需求分析: 5: analyst
    section 开发阶段
      核心功能实现: 5: developer
      API接口开发: 5: developer
      配置管理: 5: developer
    section 测试优化
      性能优化: 4: developer
      单元测试: 5: tester
      API文档: 5: writer
    section 验收阶段
      集成测试: 5: tester
      代码审查: 5: reviewer
```

### 任务清单

| 任务ID | 任务名称 | 负责Agent | 使用Skills | 相关文件 | 依赖任务 |
|--------|---------|-----------|-----------|---------|---------|
| T1 | 需求分析 | analyst | requirements | docs/requirements.md | - |
| T2 | 核心功能实现 | developer | python:core | src/core.py | T1 |
| T3 | API接口开发 | developer | python:web | src/api.py | T1 |
| T4 | 配置管理 | developer | python:core | src/config.py | T1 |
| T5 | 性能优化 | developer | python:perf | src/core.py | T2 |
| T6 | 单元测试 | tester | python:testing | tests/test_core.py | T2, T3 |
| T7 | API文档 | writer | documentation | docs/api.md | T3 |
| T8 | 集成测试 | tester | python:testing | tests/test_integration.py | T4, T5, T6, T7 |
| T9 | 代码审查 | reviewer | code-review | 所有变更文件 | T8 |

**多依赖说明：**
- **T6（单元测试）** 依赖 2 个前置任务：T2（核心功能）、T3（API接口）
- **T8（集成测试）** 依赖 4 个前置任务：T4（配置）、T5（优化）、T6（单测）、T7（文档）
- **T9（代码审查）** 依赖 T8，确保所有测试通过后才进行审查
- 多依赖任务必须等待**所有**前置任务完成后才能开始执行

### 验收标准（必须量化）

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有 CI 检查通过（lint/test/build）
- [ ] 验收标准与需求 1:1 映射
- [ ] 无新增技术债（代码复杂度 ≤ X）
- [ ] 无影响已有功能（回归测试通过）

### 简要说明（≤100字）

[任务概述]