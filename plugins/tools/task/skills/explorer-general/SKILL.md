---
description: 通用项目探索规范 - 快速理解项目全貌、识别技术栈、目录结构和核心模块的执行规范
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (3000+ tokens) -->

# Skills(task:explorer-general) - 通用项目探索规范

<scope>

当你需要快速理解项目全貌时使用此 skill。适用于首次接触新项目需要建立宏观理解、识别项目技术栈和开发工具链、映射项目目录结构和核心模块、为后续深入分析建立基础，以及生成标准化的项目概览报告。

不适用于深入代码实现细节分析（使用 explorer-code）、性能优化分析（使用 profiler）、安全审计（使用 security-auditor）。

</scope>

<core_principles>

宏观优先原则要求先理解项目的整体定位和架构，再深入具体模块。通过阅读文档和配置文件建立全局视角，避免陷入局部代码的细节。这样做的原因是：整体理解提供正确的心智模型，局部细节只有在整体框架下才有意义，过早深入会导致时间浪费和理解偏差。

文档驱动策略优先阅读 README.md、CLAUDE.md、配置文件等文档，而不是直接深入代码。文档是项目作者对项目最准确的描述，包含架构决策、设计理念、使用说明，能够在最短时间内建立理解。只有在文档不足时才需要通过代码推断。

快速定位原则遵循 80/20 原则，在 5 分钟内完成项目全貌的建立。重点识别关键信息：项目类型、技术栈、核心模块、依赖关系。避免过度探索每个细节，保持高效的探索速度。

标准化输出确保探索结果以统一的 JSON 格式输出，包含项目名称、描述、技术栈、目录结构、核心模块、依赖统计、项目类型。标准化格式便于后续工具处理、存档和检索。

</core_principles>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "README.md 不存在，直接扫描代码吧" | 文档驱动是核心原则，必须先尝试查找所有可能的文档（README、CLAUDE.md、docs/），确认完全缺失后才能扫描代码 |
| "这个目录有 100 个文件，我都读一遍" | 快速定位原则要求在 5 分钟内完成，不能深入每个文件，应该基于命名和结构推断 |
| "技术栈不确定，我猜一个吧" | 技术栈必须基于配置文件确认（package.json、go.mod 等），不能凭空猜测，不确定时应标注 |
| "输出一段文字说明就行了" | 输出格式必须是标准 JSON，文字总结只是辅助，不能替代结构化输出 |
| "这个项目太复杂，需要 30 分钟" | 项目探索的目标是宏观理解，不是完全理解，必须在 5 分钟内完成，复杂项目优先识别主要部分 |
| "没找到 package.json，肯定不是 Node.js 项目" | 技术栈识别需要检查多种可能性（package.json、go.mod、pyproject.toml 等），不能仅凭单一文件判断 |

</red_flags>

<output_format>

标准输出格式（JSON）：

```json
{
  "project_name": "项目名称",
  "description": "项目描述（来自 README.md 或配置文件）",
  "tech_stack": {
    "language": "主要语言（如 JavaScript、Go、Python、Rust）",
    "framework": "主要框架（如 React、Express、Django、Actix）",
    "build_tool": "构建工具（如 Vite、Webpack、Make、Cargo）",
    "test_framework": "测试框架（如 Jest、Go testing、pytest、cargo test）",
    "package_manager": "包管理器（如 npm、yarn、pnpm、go modules、pip、cargo）"
  },
  "directory_structure": [
    {"path": "src/", "purpose": "源代码目录"},
    {"path": "tests/", "purpose": "测试代码目录"},
    {"path": "docs/", "purpose": "文档目录"}
  ],
  "core_modules": [
    {
      "name": "认证模块",
      "path": "src/auth/",
      "purpose": "用户认证和授权"
    },
    {
      "name": "API 路由",
      "path": "src/routes/",
      "purpose": "HTTP 路由定义"
    }
  ],
  "dependencies": {
    "production": 25,
    "development": 15,
    "key_deps": ["react", "express", "prisma"]
  },
  "project_type": "frontend|backend|fullstack|library|cli|monorepo",
  "uncertainty": {
    "tech_stack": false,
    "modules": false,
    "notes": "如有不确定的地方，在此说明"
  }
}
```

字段说明：
- `project_name`: 项目名称，优先从 package.json、go.mod、README.md 中提取
- `description`: 项目描述，优先从 README.md 的开头段落或配置文件的 description 字段提取
- `tech_stack`: 技术栈信息，基于配置文件确认，不能猜测
  - `language`: 主要编程语言，基于配置文件和文件扩展名判断
  - `framework`: 主要框架，从 dependencies 中识别
  - `build_tool`: 构建工具，从配置文件和脚本中识别
  - `test_framework`: 测试框架，从 devDependencies 或测试目录识别
  - `package_manager`: 包管理器，基于 lock 文件判断（package-lock.json → npm）
- `directory_structure`: 目录结构列表，只包含核心目录（src/、tests/、docs/ 等）
- `core_modules`: 核心模块列表，基于目录名称和位置推断职责，不深入代码
- `dependencies`: 依赖统计
  - `production`: 生产依赖数量
  - `development`: 开发依赖数量
  - `key_deps`: 关键依赖列表（3-5 个最重要的依赖）
- `project_type`: 项目类型，基于目录结构和配置文件判断
- `uncertainty`: 不确定性标注，如果技术栈或模块推断不够确定，必须在此说明

</output_format>

<tech_stack_detection>

## 技术栈检测规则

### JavaScript/TypeScript 项目

配置文件：`package.json`（必须）、`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml`（包管理器）

语言识别：
- 检查 `package.json` 中的 `dependencies` 是否包含 `typescript`
- 检查项目根目录是否存在 `tsconfig.json`
- 如果存在 TypeScript 相关配置，语言为 TypeScript，否则为 JavaScript

框架识别（优先级从高到低）：
- React：`dependencies` 包含 `react`
- Vue：`dependencies` 包含 `vue`
- Angular：`dependencies` 包含 `@angular/core`
- Express：`dependencies` 包含 `express`
- Next.js：`dependencies` 包含 `next`
- Nuxt：`dependencies` 包含 `nuxt`

构建工具识别：
- Vite：`devDependencies` 包含 `vite` 或 `scripts` 包含 `vite`
- Webpack：`devDependencies` 包含 `webpack`
- Rollup：`devDependencies` 包含 `rollup`
- Parcel：`devDependencies` 包含 `parcel`

测试框架识别：
- Jest：`devDependencies` 包含 `jest`
- Vitest：`devDependencies` 包含 `vitest`
- Mocha：`devDependencies` 包含 `mocha`
- Cypress：`devDependencies` 包含 `cypress`

包管理器识别：
- npm：存在 `package-lock.json`
- yarn：存在 `yarn.lock`
- pnpm：存在 `pnpm-lock.yaml`

### Go 项目

配置文件：`go.mod`（必须）、`go.sum`

语言识别：存在 `go.mod` 即为 Go 项目，从 `go.mod` 的第一行提取 Go 版本

框架识别（基于 `require` 中的依赖）：
- Gin：包含 `github.com/gin-gonic/gin`
- Echo：包含 `github.com/labstack/echo`
- Fiber：包含 `github.com/gofiber/fiber`
- Chi：包含 `github.com/go-chi/chi`
- gRPC：包含 `google.golang.org/grpc`

构建工具：通常为 `go build`，检查 `Makefile` 或 `.github/workflows` 确认

测试框架：Go 内置测试框架（`testing` 包），检查是否有 `_test.go` 文件

包管理器：Go modules（`go.mod`）

### Python 项目

配置文件：`pyproject.toml`（推荐）、`requirements.txt`、`setup.py`、`poetry.lock` / `Pipfile`

语言识别：存在上述配置文件之一即为 Python 项目，从 `pyproject.toml` 或 `setup.py` 提取 Python 版本

框架识别：
- Django：依赖包含 `django`
- Flask：依赖包含 `flask`
- FastAPI：依赖包含 `fastapi`
- Tornado：依赖包含 `tornado`

构建工具识别：
- Poetry：存在 `poetry.lock` 或 `pyproject.toml` 中的 `[tool.poetry]`
- setuptools：存在 `setup.py`
- pip：存在 `requirements.txt`

测试框架识别：
- pytest：依赖包含 `pytest`
- unittest：Python 内置，检查是否有 `test_*.py` 文件
- nose：依赖包含 `nose`

包管理器识别：
- Poetry：存在 `poetry.lock`
- pip：存在 `requirements.txt`
- Pipenv：存在 `Pipfile`

### Rust 项目

配置文件：`Cargo.toml`（必须）、`Cargo.lock`

语言识别：存在 `Cargo.toml` 即为 Rust 项目

框架识别（基于 `[dependencies]`）：
- Actix：包含 `actix-web`
- Rocket：包含 `rocket`
- Axum：包含 `axum`
- Tokio：包含 `tokio`（异步运行时）

构建工具：Cargo（Rust 内置）

测试框架：Rust 内置测试框架（`#[test]`）

包管理器：Cargo（Rust 内置）

</tech_stack_detection>

<directory_patterns>

## 常见项目类型的目录结构模式

### Frontend 项目

典型目录：
- `src/` 或 `app/`：源代码
- `public/`：静态资源
- `components/`：组件库
- `pages/` 或 `views/`：页面/视图
- `assets/`：图片、字体等资源
- `styles/` 或 `css/`：样式文件
- `tests/` 或 `__tests__/`：测试代码
- `dist/` 或 `build/`：构建输出（通常在 .gitignore 中）

判断依据：
- 存在 `public/` 或 `static/` 目录
- 存在 `components/` 或 `pages/` 目录
- package.json 中包含前端框架依赖（React、Vue、Angular）

### Backend 项目

Go 项目典型目录：
- `cmd/`：可执行文件入口
- `internal/`：内部包，不可被外部导入
- `pkg/`：公共包，可被外部导入
- `api/`：API 定义（如 OpenAPI、gRPC proto）
- `configs/`：配置文件
- `scripts/`：脚本文件
- `tests/`：测试代码

Node.js 后端项目典型目录：
- `src/`：源代码
- `routes/` 或 `controllers/`：路由和控制器
- `models/`：数据模型
- `services/`：业务逻辑
- `middlewares/`：中间件
- `config/`：配置文件
- `tests/`：测试代码

判断依据：
- 存在 `cmd/`、`internal/`、`api/`（Go 项目）
- 存在 `routes/`、`controllers/`、`models/`（Node.js/Python 项目）
- 不存在 `public/`、`components/`、`pages/`

### Fullstack 项目

典型目录：
- `frontend/` 或 `client/`：前端代码
- `backend/` 或 `server/`：后端代码
- `shared/` 或 `common/`：共享代码
- `packages/`（Monorepo）：多个独立包

判断依据：
- 同时存在前端和后端特征目录
- 存在明确的前后端分离结构

### Library 项目

典型目录：
- `src/` 或 `lib/`：库源代码
- `tests/`：测试代码
- `docs/`：文档
- `examples/`：使用示例
- 通常没有 `cmd/`、`pages/`、`routes/` 等应用层目录

判断依据：
- package.json 中 `main` 或 `exports` 字段指向库入口
- go.mod 中模块路径不包含 `/cmd/`
- 存在 `examples/` 目录

### CLI 项目

典型目录：
- `cmd/`：命令行入口（Go 项目）
- `bin/`：可执行文件
- `internal/`：内部逻辑
- `pkg/`：公共包
- 通常没有 `public/`、`pages/`、`components/`

判断依据：
- package.json 中存在 `bin` 字段
- 存在 `cmd/` 目录（Go 项目）
- README.md 中包含命令行使用示例

### Monorepo 项目

典型目录：
- `packages/`：多个独立包
- `apps/`：多个应用
- `libs/`：共享库
- 根目录存在 `workspace` 配置（pnpm-workspace.yaml、lerna.json）

判断依据：
- package.json 中存在 `workspaces` 字段
- 存在 pnpm-workspace.yaml、lerna.json、nx.json
- 存在多个子项目，每个子项目有独立的 package.json

</directory_patterns>

<tools_guide>

## 工具使用指南

### Read - 文件读取

用途：读取文档和配置文件，建立项目理解基础。

优先读取的文件（按顺序）：
1. `README.md`：项目介绍、使用说明、架构概述
2. `CLAUDE.md`：开发规范、架构决策、团队约定
3. `.claude/memory/MEMORY.md`：项目记忆索引
4. 配置文件：
   - JavaScript/TypeScript：`package.json`
   - Go：`go.mod`
   - Python：`pyproject.toml` 或 `requirements.txt`
   - Rust：`Cargo.toml`

使用示例：
```python
# 读取 README.md
readme = Read("README.md")

# 读取配置文件
package_json = Read("package.json")
```

### serena:list_dir - 目录浏览

用途：扫描目录结构，识别核心目录。

参数：
- `path`：目录路径（相对或绝对）
- `depth`：扫描深度（建议 1 或 2，避免过深）
- `include_hidden`：是否包含隐藏文件（通常设为 false）

使用示例：
```python
# 扫描根目录，深度为 1
root_structure = serena.list_dir(path=".", depth=1, include_hidden=False)

# 扫描 src/ 目录，深度为 2
src_structure = serena.list_dir(path="src", depth=2, include_hidden=False)
```

注意事项：
- 深度不要超过 2，避免扫描时间过长
- 关注目录数量和文件数量，而非具体内容
- 根据目录命名推断用途，不要深入每个文件

### serena:find_file - 文件搜索

用途：搜索特定文件，确认配置文件存在。

参数：
- `pattern`：文件名模式（支持通配符）
- `path`：搜索路径（可选）

使用示例：
```python
# 搜索 package.json
package_files = serena.find_file(pattern="package.json")

# 搜索所有 .md 文件
md_files = serena.find_file(pattern="*.md")

# 在 src/ 目录下搜索 .go 文件
go_files = serena.find_file(pattern="*.go", path="src")
```

### serena:search_for_pattern - 模式搜索

用途：在配置文件中搜索特定字段或依赖。

参数：
- `pattern`：搜索模式（支持正则表达式）
- `path`：搜索路径（可选）
- `file_pattern`：文件名模式（可选）

使用示例：
```python
# 在 package.json 中搜索 "react"
react_usage = serena.search_for_pattern(
    pattern="react",
    file_pattern="package.json"
)

# 搜索所有 import 语句
imports = serena.search_for_pattern(
    pattern=r'import .* from',
    file_pattern="*.ts"
)
```

注意事项：
- 仅在需要精确匹配时使用，优先使用 Read 读取整个文件
- 避免在大量文件上使用，限制搜索范围

### SendMessage - 用户沟通

用途：向用户报告探索进度和结果。

使用场景：
1. 在探索开始时，报告当前阶段（如 "正在扫描项目文档..."）
2. 在探索过程中，报告发现的关键信息（如 "识别到 React + TypeScript 技术栈"）
3. 在探索结束时，发送简短总结（然后输出完整 JSON）

使用示例：
```python
# 报告进度
SendMessage(
    recipient="@main",
    content="正在扫描项目文档和配置文件..."
)

# 报告结果总结
SendMessage(
    recipient="@main",
    content="""项目探索完成：
- 项目类型：前端应用
- 技术栈：React + TypeScript + Vite
- 核心模块：5 个（认证、路由、组件库、状态管理、工具）
- 依赖数量：生产 25 个，开发 15 个
- 关键依赖：react、react-router、zustand

详细报告已生成（JSON 格式）。"""
)
```

</tools_guide>

<guidelines>

必须先读取 README.md 和配置文件，再扫描目录结构。优先使用文档中的信息，避免基于代码推测。技术栈识别必须基于配置文件确认，不能猜测。输出格式必须是标准 JSON，包含所有必需字段。

不要跳过文档阅读阶段，不要深入每个文件的实现细节，不要在配置文件缺失时猜测技术栈。不要花费超过 5 分钟在项目探索上，不要输出不完整的 JSON。

发现项目结构不符合常见模式时，使用 SendMessage(@main) 说明情况。发现配置文件缺失或不完整时，在 `uncertainty` 字段中标注。对于 Monorepo 项目，优先识别整体结构，不要深入每个子项目。

</guidelines>

<!-- /STATIC_CONTENT -->
