---
description: 结果校验，验证执行结果是否符合预期
memory: project
color: cyan
model: haiku
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:verify
---

# Verify Skill

## Process

1. 对照验收标准逐一检查
2. 验证输出文件符合规范
3. 检查代码质量和风格
4. 确认所有子任务完成
5. 运行测试验证功能
6. 检查边界情况和异常处理
7. 评估质量评分
8. 输出校验结果

## Output

- 校验通过/失败判定
- 质量评分
- 不符合项清单
- 改进建议
