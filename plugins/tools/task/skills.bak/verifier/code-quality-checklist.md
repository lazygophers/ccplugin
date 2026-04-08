# Code Quality Checklist (Stage 2)

## 概述
Stage 2 验证关注"做得好不好"，即代码质量和最佳实践。
仅在 Stage 1 通过后执行。

## CAN SUGGEST - 质量审查

质量问题记录在 passed 输出的 suggestions 数组中，质量分判定由 Loop 的 QualityGate 阶段负责。

### 1. 测试质量
- [ ] 测试覆盖率达标（AAA 模式）
- [ ] 包含边界情况测试
- [ ] 包含异常情况测试
- [ ] 测试命名清晰、可读

### 2. 代码标准
- [ ] 通过 lint 检查（无新增警告）
- [ ] 命名规范一致
- [ ] 无硬编码魔法数字
- [ ] 适当的错误处理

### 3. 性能考量
- [ ] 无明显性能问题（N+1 查询、无限循环风险）
- [ ] 资源正确释放
- [ ] 适当的缓存策略

### 4. 安全检查
- [ ] 无明显安全漏洞（注入、XSS）
- [ ] 敏感信息未硬编码
- [ ] 输入验证完整

## 输出格式

```json
{
  "stage": "code_quality",
  "status": "passed",
  "quality_score": 85,
  "suggestions": [
    {
      "severity": "warning|info",
      "category": "testing|style|performance|security",
      "suggestion": "增加边界测试用例",
      "file": "src/auth.ts",
      "line": 42
    }
  ]
}
```

## 处理规则
- Stage 2 始终输出 quality_score 和 suggestions（如有）
- 质量分是否达标由 Loop 的 QualityGate 阶段判定（非 Verifier 职责）
- suggestions 作为优化建议附在 passed 输出中，不影响 status 判定
