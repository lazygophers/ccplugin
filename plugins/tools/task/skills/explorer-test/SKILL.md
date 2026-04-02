---
description: "探索项目测试体系：识别测试框架、分析覆盖率、评估测试质量、定位测试缺口。当需要了解测试现状、评估测试金字塔分布、发现未覆盖的高风险模块时触发。"
model: sonnet
context: fork
user-invocable: false
---


# Skills(task:explorer-test) - 测试探索

分析项目测试体系：框架识别/覆盖率/质量评估/缺口识别。支持Jest/Vitest/pytest/go testing/JUnit/Playwright/Cypress。

## 核心原则

- **数据驱动**：基于实际覆盖率数字、测试数量、断言模式评估
- **测试金字塔**：单元70% > 集成20% > E2E 10%
- **质量重于数量**：断言质量、边界覆盖、异常处理、Mock合理性
- **精准缺口**：按风险排序(业务逻辑>数据处理>工具函数)

## 识别模式

| 框架 | 标志 | 文件模式 |
|------|------|---------|
| Jest | package.json | `**/*.test.{ts,js}`, `**/__tests__/**` |
| Vitest | package.json | `**/*.test.ts`, `**/*.spec.ts` |
| pytest | requirements | `**/test_*.py`, `**/*_test.py` |
| Go | 内置 | `**/*_test.go` |
| JUnit | pom.xml | `**/Test*.java`, `**/*Test.java` |

Mock框架：`jest.mock()`/`unittest.mock`/`testify/mock`/`Mockito`

覆盖率工具：Istanbul/nyc | Jest coverage | coverage.py | go cover | JaCoCo

## 输出格式

JSON包含：`test_framework{name,version,config,mock}` + `test_files{total,unit,integration,e2e}` + `coverage{lines,functions,branches}` + `quality{score,assertions_per_test,edge_cases,mock_usage}` + `gaps[{module,coverage,risk}]` + `pyramid{shape,recommendation}`

## 工具指南

测试文件：`glob("**/*.test.{ts,js}")` | `glob("**/test_*.py")` | `glob("**/*_test.go")`
断言：`grep("expect\\(|assert|should")` | `grep("assert |assertEqual")` | `grep("assert\\.|require\\.")`
覆盖率：优先使用已有报告`glob("**/coverage/**")`，避免重复运行

## 指南

先识别框架 | 有覆盖率报告直接用 | 按文件位置/导入/名称分类测试类型

