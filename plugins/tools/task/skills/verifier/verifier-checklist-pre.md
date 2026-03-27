# Verifier 验证检查清单

## 验证前

| 检查项 | 要求 |
|--------|------|
| 任务完成性 | 所有任务 completed、无遗漏、有验收标准、依赖已满足 |
| 验收标准 | 可量化可验证、避免绝对词汇(all/always/never)、符合 SMART |
| 结构化标准 | 必需字段(id/type/description/priority)完整、type特定字段匹配(exact_match→verification_method, quantitative_threshold→metric+operator+threshold)、priority∈{required,recommended}、operator∈{>=,<=,>,<,==} |
| 环境工具 | 测试环境就绪、工具可用、服务已启动、CI/CD正常 |

## 验证中

| 维度 | 检查项 |
|------|--------|
| 功能 | 核心功能实现、符合需求规格、边界条件正确、异常处理完善 |
| 测试 | 单元覆盖率≥90%、集成测试覆盖关键路径、边界测试+异常测试完整 |
| 代码质量 | Lint 0错误0警告、格式规范、圈复杂度<10 |
| 性能 | 响应时间达标、无内存泄漏、并发性能达标 |
| 安全 | 输入验证、XSS/SQL注入防护、权限检查、敏感数据加密 |
