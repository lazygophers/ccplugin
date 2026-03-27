# Verifier 调试和错误处理

## 高级用法

- **自定义规则**：`Skill(skill="task:verifier")` 传入custom_rules JSON
- **条件验证**：根据环境/配置调整验证标准
- **分阶段验证**：foundation(基本通过) → enhancement(覆盖≥90%) → refinement(质量+文档+性能)

## 调试模式

开启debug时输出：Status + Verified Tasks数量 + 每个任务状态和criteria通过数 + Suggestions/Failures数量

## 错误处理

验证失败时分析：
1. 收集failed_tasks列表
2. 识别常见问题：测试失败/覆盖率不足/代码质量
3. 生成建议：修复测试/添加测试/运行lint

## 重试机制

`verify_with_retry(tasks, max_retries=3)`：
- 验证失败 → 指数退避(`2^attempt`秒) → 重试
- 达到max_retries → 返回最终结果
- 异常 → 记录并重试，最后一次抛出
