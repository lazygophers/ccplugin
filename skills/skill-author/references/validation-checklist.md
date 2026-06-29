# 验证 checklist

> 产物发布前逐项查。主入口 SKILL.md Phase 5。

## 结构

- [ ] SKILL.md ≤500 行（CJK 内容留更大余量）
- [ ] description 第三人称 + key use case 前置 + 做什么+何时用 + 🔴 **< 512 字符**（项目底线）
- [ ] when_to_use < 128 字符（项目底线，若有）
- [ ] frontmatter 字段合法（16 字段全表见 [frontmatter-spec.md](frontmatter-spec.md)）
- [ ] 引用只深一层
- [ ] >100 行 reference 顶部有目录
- [ ] frontmatter YAML 语法正确（`--debug` 验证）

## 触发准确性（≠ 可发现性）

- [ ] `claude -p` 可发现性通过（能列出 + 说明何时触发）
- [ ] should-trigger 测试通过（该触发的 prompt 命中）
- [ ] should-not-trigger 测试通过（不该触发的 prompt 不命中）

## 内容

- [ ] 无时间敏感信息（或放 old patterns）
- [ ] 术语一致
- [ ] 正斜杠路径
- [ ] 复杂工作流有 checklist
- [ ] 质量关键操作有 feedback loop
- [ ] 失败模式有三段式 fallback 编码

## 代码（若含脚本）

- [ ] 脚本 solve 不 punt（显式错误处理）
- [ ] 无 voodoo constants
- [ ] 依赖显式列出
- [ ] MCP 工具用全限定名 `Server:tool`

## 验证

- [ ] eval 先行（≥3 场景，先 baseline 后对比）
- [ ] 反例黑名单成章
