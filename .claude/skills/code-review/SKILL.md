---
name: code-review
description: "Code review skill for static analysis, best-practice validation, test coverage analysis, and security scanning. Use when reviewing code quality, running code audits, checking SOLID/DRY/KISS compliance, analyzing test coverage, or generating improvement reports."
user-invocable: true
model: sonnet
---

# 代码审查（Code Review）

本 Skill 提供全面的代码质量检查，包括静态分析、最佳实践验证、测试覆盖率分析和安全扫描。

## 概览

**核心能力**：
1. **静态分析** - 圈复杂度、代码重复、认知复杂度
2. **代码规范** - 命名规范、注释质量、代码组织
3. **最佳实践** - SOLID原则、DRY、KISS
4. **测试覆盖** - 行覆盖率、分支覆盖率、目标≥80%
5. **安全扫描** - OWASP Top 10、依赖安全、许可证合规

**输出格式**：
- 技术报告（详细分析 + 代码示例）
- 清单报告（问题列表 + 优先级排序）
- 演示文稿（团队分享用可视化图表）

## 执行流程

### 阶段1：需求理解

明确审查范围和关注点（使用 AskUserQuestion）：
1. 审查范围：「整个项目」「特定模块」「单个文件」
2. 关注点：「代码质量」「性能」「安全」「测试覆盖率」「全部」
3. 输出格式：「技术报告」「清单报告」「演示文稿」

### 阶段2：代码分析

**静态分析**：
- 圈复杂度：目标≤10
- 代码重复：目标<5%
- 认知复杂度：目标≤15

**代码规范**：
- 命名规范（camelCase/snake_case/PascalCase）
- 注释质量（函数注释、类注释）
- 代码组织（单一职责、函数长度≤50行）

**最佳实践（SOLID + DRY + KISS + YAGNI）**：
- S - Single Responsibility（单一职责）
- O - Open/Closed（开闭原则）
- L - Liskov Substitution（里氏替换）
- I - Interface Segregation（接口隔离）
- D - Dependency Inversion（依赖倒置）

**测试覆盖率**（调用 testing skill）：
- 行覆盖率：≥80%
- 分支覆盖率：≥75%
- 函数覆盖率：≥90%

**性能检查**（调用 performance-optimization skill）：
- N+1 查询问题
- 内存泄漏
- 低效算法

**安全扫描**（调用 security-audit skill）：
- OWASP Top 10
- 依赖包漏洞（CVE）
- 敏感信息泄露

### 阶段3：问题分类

**质量问题**：命名不规范、缺少注释、违反SOLID原则、代码重复

**技术债**：
- 设计债（违反设计原则）
- 测试债（测试覆盖率低）
- 文档债（缺少文档）
- 架构债（技术栈过时）

**性能问题**：N+1查询、内存泄漏、低效算法、不必要同步操作

**安全问题**：注入漏洞、认证/授权问题、敏感信息泄露、依赖包漏洞

### 阶段4：优先级评分

三维评分模型：
```
优先级 = 严重度(0-10) × 影响范围(0-10) × 紧急度(0-10)

优先级分级：
- 高优先级（≥700）：立即修复
- 中优先级（300-699）：近期修复
- 低优先级（<300）：有时间再修复
```

### 阶段5：生成报告

根据受众选择格式：
- **技术报告**（技术团队）：详细分析 + 代码示例 + 改进建议
- **清单报告**（快速查看）：问题列表 + 优先级 + 文件位置
- **演示文稿**（团队分享）：可视化图表 + 关键问题

详细示例请参考 [examples.md](./examples.md)

## 质量评分标准

### 代码质量（总分10分）

- **可读性**（30%）：命名、注释、代码组织
- **可维护性**（30%）：模块化、耦合度、复杂度
- **可测试性**（20%）：依赖注入、接口抽象
- **安全性**（20%）：注入漏洞、敏感信息泄露

### OWASP Top 10（安全检查）

1. Broken Access Control（访问控制失效）
2. Cryptographic Failures（加密失败）
3. Injection（注入）
4. Insecure Design（不安全设计）
5. Security Misconfiguration（安全配置错误）
6. Vulnerable Components（易受攻击的组件）
7. Identification and Authentication Failures（认证失败）
8. Software and Data Integrity Failures（完整性失败）
9. Security Logging and Monitoring Failures（日志和监控失败）
10. Server-Side Request Forgery（SSRF）

## 最佳实践

### 审查前准备
- 了解项目背景和技术栈
- 确认代码规范和编码标准
- 准备静态分析工具

### 审查过程
- 结合自动化工具和人工审查
- 关注代码逻辑而非代码风格
- 提供建设性反馈
- 附带代码示例

### 审查后跟进
- 跟踪问题修复进度
- 验证修复质量
- 更新技术债清单

## 工具集成

**静态分析工具**：
- Python：pylint、flake8、mypy、radon
- JavaScript/TypeScript：ESLint、TSLint
- Go：golangci-lint、staticcheck
- Java：SonarQube、PMD、Checkstyle

**测试框架**：Jest、Pytest、JUnit、Mocha

**性能分析**：Chrome DevTools、py-spy、pprof

**安全扫描**：Bandit、Safety、npm audit、Snyk

## 相关 Skills

- **testing** - 测试策略和测试用例生成
- **performance-optimization** - 性能瓶颈定位和优化
- **security-audit** - 安全漏洞检测和修复

## 示例文档

详细的代码审查示例和报告格式请参考：
- [examples.md](./examples.md) - 3种报告格式示例 + 问题代码改进示例
