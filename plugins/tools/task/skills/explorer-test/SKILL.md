---
description: 测试探索规范 - 测试框架识别、覆盖率分析、测试质量评估和缺口识别
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:explorer-test) - 测试探索规范

<scope>

当你需要深入理解项目的测试体系时使用此 skill。适用于识别测试框架和配置、分析测试覆盖率、评估测试质量和策略、识别测试缺口和改进方向。

支持的测试框架：
- **JavaScript**: Jest, Vitest, Mocha, Jasmine, Playwright, Cypress, Testing Library
- **Python**: pytest, unittest, coverage.py, tox
- **Go**: testing, testify, go test -cover, gomock
- **Java**: JUnit 5, TestNG, Mockito, Spring Test
- **Rust**: cargo test, #[test], proptest

</scope>

<core_principles>

数据驱动评估。测试质量评估必须基于实际数据（覆盖率数字、测试数量、断言模式），而非主观判断。

测试金字塔。健康的测试体系应遵循金字塔结构：大量单元测试（70%）、适量集成测试（20%）、少量 E2E 测试（10%）。偏离此比例可能意味着测试策略问题。

质量重于数量。评估断言质量（每个测试是否有有效断言）、边界覆盖、异常处理和 Mock 合理性。

精准缺口识别。测试缺口按风险排序：关键业务逻辑 > 数据处理 > 工具函数。

</core_principles>

<detection_patterns>

**测试框架识别**：

| 框架 | 识别标志 | 测试文件模式 |
|------|---------|-------------|
| Jest | `jest` in package.json | `**/*.test.{ts,js,tsx,jsx}`, `**/__tests__/**` |
| Vitest | `vitest` in package.json | `**/*.test.{ts,js}`, `**/*.spec.{ts,js}` |
| pytest | `pytest` in requirements | `**/test_*.py`, `**/*_test.py` |
| Go testing | 内置 | `**/*_test.go` |
| JUnit | `junit` in pom.xml | `**/Test*.java`, `**/*Test.java` |
| Rust | 内置 | `#[test]` in `*.rs`, `tests/` 目录 |

**Mock 框架识别**：

| Mock 框架 | 识别标志 |
|-----------|---------|
| jest.mock | `jest.mock(`, `jest.fn()` |
| unittest.mock | `from unittest.mock import`, `@patch` |
| testify/mock | `mock.Mock`, `mock.On(` |
| Mockito | `@Mock`, `when(`, `verify(` |

**覆盖率工具识别**：

| 工具 | 配置/命令 |
|------|---------|
| Istanbul/nyc | `.nycrc`, `nyc_output/` |
| Jest coverage | `jest --coverage`, `coverage/` |
| coverage.py | `.coveragerc`, `htmlcov/` |
| go cover | `go test -cover`, `-coverprofile` |
| JaCoCo | `jacoco.xml`, `target/site/jacoco/` |

</detection_patterns>

<output_format>

```json
{
  "test_framework": {
    "name": "Jest|Vitest|pytest|go testing",
    "version": "29.x",
    "config": "jest.config.ts",
    "mock_framework": "jest.mock|unittest.mock"
  },
  "test_files": {
    "total": 45,
    "unit": 30,
    "integration": 10,
    "e2e": 5,
    "pattern": "**/*.test.ts"
  },
  "coverage": {
    "lines": 78.5,
    "functions": 82.0,
    "branches": 71.3,
    "report_file": "coverage/lcov-report/index.html"
  },
  "quality": {
    "score": 7.5,
    "assertions_per_test": 2.3,
    "edge_cases_coverage": "medium",
    "mock_usage": "appropriate",
    "test_isolation": "good"
  },
  "gaps": [
    {"module": "src/auth/", "coverage": 45, "risk": "high"}
  ],
  "pyramid": {
    "shape": "healthy|inverted|missing_layer",
    "recommendation": "建议"
  },
  "summary": "测试体系总结"
}
```

</output_format>

<tools_guide>

**测试文件搜索**：
- JavaScript: `glob("**/*.test.{ts,js,tsx}")` + `glob("**/*.spec.{ts,js}")`
- Python: `glob("**/test_*.py")` + `glob("**/*_test.py")`
- Go: `glob("**/*_test.go")`
- Java: `glob("**/Test*.java")` + `glob("**/*Test.java")`

**测试模式搜索**：
- `grep("describe\\(|it\\(|test\\(")` → JS 测试块
- `grep("def test_|class Test")` → Python 测试
- `grep("func Test|func Benchmark")` → Go 测试
- `grep("@Test|@ParameterizedTest")` → Java 测试

**断言模式搜索**：
- `grep("expect\\(|assert|should")` → JS 断言
- `grep("assert |assertEqual|pytest.raises")` → Python 断言
- `grep("assert\\.|require\\.")` → Go 断言

**覆盖率分析**：
- `glob("**/coverage/**")` → 查找已有覆盖率报告
- `Bash("npx jest --coverage --silent 2>/dev/null")` → 运行覆盖率（JS）
- `Bash("go test -cover ./... 2>/dev/null")` → 运行覆盖率（Go）

</tools_guide>

<guidelines>

先识别框架再分析测试。框架决定了测试文件的组织方式和搜索模式。

如果有覆盖率报告直接使用，避免重复运行覆盖率工具（可能耗时较长）。

测试分类（单元/集成/E2E）需要根据文件位置、导入模式和测试名称来判断，不能仅看文件名。

</guidelines>
