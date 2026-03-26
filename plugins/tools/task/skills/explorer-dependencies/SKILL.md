---
description: 依赖探索规范 - 依赖树分析、安全审计、版本管理和许可证合规检查
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:explorer-dependencies) - 依赖探索规范

<scope>

当你需要深入理解项目的依赖关系时使用此 skill。适用于分析依赖树结构、检查安全漏洞、评估版本管理策略、验证许可证合规性。

支持的包管理器：
- **JavaScript**: npm, yarn, pnpm
- **Python**: pip, poetry, pipenv, uv
- **Go**: go mod
- **Java**: Maven, Gradle
- **Rust**: Cargo

</scope>

<core_principles>

安全优先。依赖分析的首要目标是识别安全风险，包括已知漏洞（CVE）、恶意包和供应链攻击风险。

直接 vs 间接依赖。直接依赖是项目明确声明的，间接依赖通过传递引入。间接依赖往往是安全风险的主要来源。

版本锁定策略。分析版本锁定策略（exact/range/latest），评估更新风险和兼容性。

许可证合规。不同开源许可证有不同要求（MIT/Apache/GPL/AGPL），必须确保依赖许可证与项目兼容。

</core_principles>

<detection_patterns>

**包管理器识别**：

| 包管理器 | 配置文件 | Lock 文件 |
|---------|---------|----------|
| npm | `package.json` | `package-lock.json` |
| yarn | `package.json` | `yarn.lock` |
| pnpm | `package.json` | `pnpm-lock.yaml` |
| pip | `requirements.txt`, `setup.py` | — |
| poetry | `pyproject.toml` | `poetry.lock` |
| uv | `pyproject.toml` | `uv.lock` |
| go mod | `go.mod` | `go.sum` |
| Maven | `pom.xml` | — |
| Gradle | `build.gradle`, `build.gradle.kts` | `gradle.lockfile` |
| Cargo | `Cargo.toml` | `Cargo.lock` |

**Monorepo 识别**：

| 工具 | 识别标志 |
|------|---------|
| Lerna | `lerna.json` |
| Nx | `nx.json` |
| Turborepo | `turbo.json` |
| pnpm workspace | `pnpm-workspace.yaml` |

</detection_patterns>

<output_format>

```json
{
  "package_manager": {
    "name": "npm|yarn|pnpm|pip|poetry|go mod|cargo|maven",
    "lock_file": "package-lock.json|yarn.lock|go.sum",
    "config": "package.json|pyproject.toml|go.mod"
  },
  "dependencies": {
    "direct": 42,
    "dev": 28,
    "transitive": 303,
    "total": 345,
    "duplicates": [
      {"name": "lodash", "versions": ["4.17.21", "4.17.15"]}
    ]
  },
  "security": {
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 12
    },
    "details": [...]
  },
  "outdated": [...],
  "licenses": {
    "MIT": 280,
    "Apache-2.0": 45,
    "compliance_issues": [...]
  },
  "summary": "依赖分析总结"
}
```

</output_format>

<tools_guide>

**包管理器配置搜索**：
- `glob("**/package.json")` + `glob("**/go.mod")` + `glob("**/Cargo.toml")`
- `glob("**/pyproject.toml")` + `glob("**/requirements*.txt")`
- `glob("**/pom.xml")` + `glob("**/build.gradle*")`

**Lock 文件搜索**：
- `glob("**/package-lock.json")` + `glob("**/yarn.lock")` + `glob("**/pnpm-lock.yaml")`
- `glob("**/go.sum")` + `glob("**/Cargo.lock")` + `glob("**/poetry.lock")`

**依赖分析命令**：
- npm: `Bash("npm ls --depth=0 --json 2>/dev/null")`
- pip: `Bash("pip list --format=json 2>/dev/null")`
- go: `Bash("go list -m all 2>/dev/null")`
- cargo: `Bash("cargo tree --depth 1 2>/dev/null")`

**安全审计命令**：
- npm: `Bash("npm audit --json 2>/dev/null")`
- pip: `Bash("pip-audit --format=json 2>/dev/null")`
- go: `Bash("govulncheck ./... 2>/dev/null")`
- cargo: `Bash("cargo audit --json 2>/dev/null")`

**过时依赖检查**：
- npm: `Bash("npm outdated --json 2>/dev/null")`
- pip: `Bash("pip list --outdated --format=json 2>/dev/null")`
- go: `Bash("go list -m -u all 2>/dev/null")`

**Monorepo 识别**：
- `glob("**/lerna.json")` + `glob("**/nx.json")` + `glob("**/turbo.json")`
- `glob("**/pnpm-workspace.yaml")`

</tools_guide>

<guidelines>

先识别包管理器再分析依赖。包管理器决定了可用的分析命令和输出格式。

优先使用 lock 文件分析间接依赖。lock 文件包含完整的依赖树，比运行命令更快速可靠。

安全审计结果按严重级别排序。critical 和 high 需要立即关注，medium 和 low 可以计划修复。

注意 Monorepo 场景。多包项目可能有不同的依赖版本，需要分别分析。

</guidelines>
