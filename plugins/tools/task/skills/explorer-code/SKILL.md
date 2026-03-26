---
description: 代码结构探索规范 - 符号索引、依赖分析、模式识别的执行规范
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (4000+ tokens) -->

# Skills(task:explorer-code) - 代码结构探索规范

<scope>

当你需要深度理解代码结构时使用此 skill。适用于分析代码架构和模块关系、追踪符号定义和引用关系、识别设计模式和架构决策、为重构或优化提供结构化信息，以及理解遗留代码库的组织结构。

不适用于代码质量检查（使用 linter）、性能分析（使用 profiler）、安全审计（使用 security scanner）、语义搜索（使用 RAG）。

</scope>

<core_principles>

结构分析优于语义搜索。根据 Aider 的 Repo Map 研究（2024），基于 AST 和符号索引的代码理解方法在效率上比 RAG 语义搜索高 3-4 倍。原因在于：1) 代码的结构信息（符号定义、引用关系、调用链）比自然语言描述更精确、更稳定；2) 符号索引可以精确定位，避免语义歧义；3) 结构分析可复现，不受 embedding 模型版本影响。

符号索引是代码理解的基石。必须先建立完整的符号索引（类、函数、接口、变量、类型），再分析它们之间的关系。符号索引提供了代码的骨架，是所有后续分析的基础。没有符号索引的依赖分析是盲目的，容易遗漏关键关系。

依赖关系揭示架构意图。模块间的依赖方向、强度、复杂度直接反映架构质量。强依赖（tight coupling）表示模块高度耦合，弱依赖（loose coupling）表示模块独立性好。循环依赖（circular dependency）是架构问题的信号。依赖分析不是简单地列出 import 语句，而是理解"为什么这样依赖"。

模式识别需要跨文件视角。单个文件无法完整展现设计模式。例如，工厂模式需要看创建者和产品的关系，策略模式需要看上下文和策略接口的关系，依赖注入需要看容器和组件的关系。必须结合符号索引、依赖关系、文件组织结构进行综合分析。

</core_principles>

<output_format>

代码地图 JSON Schema：

```json
{
  "project_type": "typescript|python|golang|java|rust|...",
  "modules": [
    {
      "name": "模块名称（如 auth、api、database）",
      "path": "相对路径（如 src/auth）",
      "purpose": "模块职责描述（1-2句话，说明这个模块负责什么）",
      "symbols_count": 15,
      "key_files": ["main.ts", "types.ts"],
      "visibility": "public|internal"
    }
  ],
  "key_symbols": [
    {
      "name": "符号名称（如 UserService、authenticate）",
      "type": "class|function|interface|type|constant",
      "file": "定义文件路径（相对路径）",
      "references": 12,
      "visibility": "public|private|protected",
      "description": "符号用途描述（1句话）"
    }
  ],
  "dependencies": [
    {
      "from": "模块A（如 api）",
      "to": "模块B（如 database）",
      "type": "import|extends|implements|calls",
      "strength": "strong|medium|weak",
      "symbols": ["具体依赖的符号列表"],
      "reason": "依赖原因（如 API 需要访问数据库）"
    }
  ],
  "patterns": [
    {
      "name": "模式名称（如 Factory Pattern、Singleton）",
      "description": "模式实现描述（如 使用工厂类创建不同类型的连接）",
      "locations": ["涉及的文件路径"],
      "evidence": "识别依据（代码特征，如 create() 方法返回接口类型）"
    }
  ],
  "architecture": {
    "style": "layered|microservices|event-driven|mvc|hexagonal|...",
    "layers": ["表现层", "业务逻辑层", "数据访问层"],
    "key_decisions": [
      "架构决策1（如 使用依赖注入实现模块解耦）",
      "架构决策2（如 采用事件驱动处理异步任务）"
    ]
  },
  "summary": "项目架构总结（3-5句话，包含：使用的语言/框架、项目规模、主要模块及其职责、架构风格、关键特点）"
}
```

字段说明：

- `project_type`：编程语言或主要技术栈（必填）
- `modules`：模块列表，每个模块是一组相关文件的集合（必填）
- `key_symbols`：关键符号列表，聚焦高引用数或公开 API 的符号（必填）
- `dependencies`：模块间依赖关系，包含依赖类型和强度（必填）
- `patterns`：识别出的设计模式，必须有证据支持（可选）
- `architecture`：架构风格和关键决策（必填）
- `summary`：整体总结，便于快速理解（必填）

</output_format>

<tools_guide>

## 符号索引工具

**serena:get_symbols_overview** - 获取文件符号概览（优先使用）
- 用途：批量获取文件中的所有符号定义
- 何时使用：需要了解文件的整体结构时
- 优点：效率高，一次获取所有符号
- 示例：`serena:get_symbols_overview(file_path="src/auth/service.ts")`

**serena:find_symbol** - 查找特定符号定义
- 用途：精确查找某个符号的定义位置
- 何时使用：已知符号名称，需要找到定义时
- 优点：精确定位，返回符号详细信息
- 示例：`serena:find_symbol(symbol_name="UserService", file_path="src/auth/")`

## 依赖分析工具

**serena:find_referencing_symbols** - 查找符号引用（依赖分析核心工具）
- 用途：查找哪些地方引用了某个符号
- 何时使用：需要了解符号的使用情况、追踪调用链、分析影响范围时
- 优点：精确追踪引用关系，支持跨文件分析
- 示例：`serena:find_referencing_symbols(symbol_name="authenticate", file_path="src/auth/service.ts")`

## 模式搜索工具

**serena:search_for_pattern** - 正则搜索代码模式
- 用途：使用正则表达式搜索特定代码模式
- 何时使用：需要找特定的代码结构（如所有 export、所有 class）时
- 优点：灵活，支持复杂模式
- 示例：`serena:search_for_pattern(pattern="export class.*Factory", path="src/")`

## 文件系统工具

**glob** - 文件模式匹配
- 用途：批量查找符合模式的文件
- 何时使用：需要找某类文件（如所有 .ts 文件、所有测试文件）时
- 示例：`glob(pattern="**/*.ts", directory="src/")`

**grep** - 内容搜索
- 用途：在文件内容中搜索文本
- 何时使用：需要找特定文本或关键字时
- 示例：`grep(pattern="import.*express", path="src/")`

**serena:list_dir** - 目录浏览
- 用途：列出目录内容
- 何时使用：需要了解目录结构时
- 示例：`serena:list_dir(path="src/")`

**serena:find_file** - 文件查找
- 用途：按文件名查找文件
- 何时使用：已知文件名，需要找到路径时
- 示例：`serena:find_file(filename="config.ts", path="src/")`

## 用户交互工具

**SendMessage(@main)** - 向用户报告或提问
- 用途：向用户发送消息，报告进度或请求澄清
- 何时使用：需要用户确认、提供额外信息、或报告重要发现时
- 示例：`SendMessage(to="@main", content="发现循环依赖：A → B → A，需要重构吗？")`

</tools_guide>

<workflow_principles>

工作流采用四阶段渐进式探索，每个阶段有明确的目标和转换条件。阶段之间不是严格串行，可以根据需要回溯或跳跃。

**阶段 1：目录扫描** - 建立文件树视图，识别项目类型和核心目录
- 使用 glob 获取文件列表
- 识别语言特征（package.json → TypeScript, go.mod → Go）
- 定位核心业务目录（src/internal/lib/pkg）
- 转换条件：文件树已生成，项目类型已识别

**阶段 2：符号索引** - 建立符号地图，识别关键符号和公开 API
- 使用 serena:get_symbols_overview 批量获取符号
- 统计每个模块的符号数量和复杂度
- 识别公开 API（export/public）和内部实现
- 转换条件：核心文件的符号索引已建立

**阶段 3：依赖分析** - 追踪模块间关系，建立依赖图
- 使用 serena:find_referencing_symbols 查找引用
- 识别导入/导出关系（import/export）
- 追踪继承/实现关系（extends/implements）
- 计算依赖强度（引用次数、调用深度）
- 转换条件：主要符号的引用关系已建立

**阶段 4：模式识别** - 识别设计模式和架构决策
- 基于符号和依赖识别设计模式
- 分析模块职责分离（SRP）
- 评估耦合度和内聚性
- 识别架构风格（分层/微服务/事件驱动）
- 转换条件：设计模式已识别，架构特征已总结

</workflow_principles>

<guidelines>

**必须做的事情**：
- 先扫描文件结构，再建立符号索引，避免盲目搜索
- 优先使用 serena:get_symbols_overview 批量获取符号，避免逐个查找
- 依赖分析聚焦核心模块和关键符号，避免陷入琐碎依赖
- 模式识别必须基于证据（代码特征），避免主观臆断
- 输出必须是结构化 JSON，方便后续处理和自动化分析
- 为每个模块提供职责描述，说明"这个模块负责什么"
- 依赖关系必须包含依赖原因，说明"为什么这样依赖"

**不要做的事情**：
- 不要跳过目录扫描直接分析代码（会遗漏重要文件）
- 不要忽略符号的可见性和访问控制（public/private 影响 API 设计）
- 不要只分析单个文件就下结论（设计模式需要跨文件视角）
- 不要忽略配置文件中的架构信息（package.json/tsconfig.json）
- 不要在不了解语言特性时强行识别模式（避免误判）
- 不要输出非结构化的文本报告（降低可用性）
- 不要分析所有文件（聚焦核心模块，避免信息过载）

**质量检查**：
- 符号索引覆盖了所有核心模块
- 依赖关系包含了主要模块间的关系
- 设计模式识别有具体的代码证据
- 架构风格的判断有充分的依据
- JSON 输出符合 schema 定义
- summary 字段提供了有价值的总结

</guidelines>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "已经分析了几个重要文件，可以总结了" | 必须先完成符号索引，再分析依赖，最后总结架构 |
| "这个模块很明显是单例模式" | 必须有代码证据（如私有构造函数、静态实例）支持模式识别 |
| "依赖关系很简单，A 导入了 B" | 必须分析依赖原因、强度、方向，不只是列出 import |
| "项目结构清晰，不需要生成 JSON" | 必须输出结构化 JSON，方便后续自动化处理 |
| "这个符号只在一个地方用，不重要" | 引用数不是唯一标准，公开 API 即使引用少也是关键符号 |
| "没有找到设计模式，跳过 patterns 字段" | patterns 字段可选，没有就返回空数组，不要省略字段 |

</red_flags>

<examples>

## 示例 1：TypeScript 项目分析

**输入**：分析一个 Express API 项目的代码结构

**执行步骤**：

1. 目录扫描：`glob(pattern="**/*.ts", directory="src/")`
   - 发现 src/routes/, src/controllers/, src/services/, src/models/
   - 识别为分层架构（MVC 变体）

2. 符号索引：`serena:get_symbols_overview(file_path="src/services/user.service.ts")`
   - 发现 UserService 类（public）
   - 发现 authenticate, register, getUserById 方法

3. 依赖分析：`serena:find_referencing_symbols(symbol_name="UserService")`
   - UserController 引用（控制器层 → 服务层）
   - AuthMiddleware 引用（中间件 → 服务层）

4. 模式识别：
   - 依赖注入：Controller 通过构造函数注入 Service
   - 仓储模式：Service 依赖 UserRepository 接口

**输出**：
```json
{
  "project_type": "typescript",
  "modules": [
    {
      "name": "services",
      "path": "src/services",
      "purpose": "业务逻辑层，封装核心业务规则",
      "symbols_count": 25,
      "key_files": ["user.service.ts", "auth.service.ts"],
      "visibility": "public"
    }
  ],
  "key_symbols": [
    {
      "name": "UserService",
      "type": "class",
      "file": "src/services/user.service.ts",
      "references": 8,
      "visibility": "public",
      "description": "用户管理核心服务"
    }
  ],
  "dependencies": [
    {
      "from": "controllers",
      "to": "services",
      "type": "import",
      "strength": "strong",
      "symbols": ["UserService", "AuthService"],
      "reason": "控制器依赖服务层处理业务逻辑"
    }
  ],
  "patterns": [
    {
      "name": "Dependency Injection",
      "description": "通过构造函数注入依赖，实现松耦合",
      "locations": ["src/controllers/", "src/services/"],
      "evidence": "构造函数参数声明依赖，通过容器注入"
    }
  ],
  "architecture": {
    "style": "layered",
    "layers": ["routes", "controllers", "services", "repositories"],
    "key_decisions": [
      "使用依赖注入实现层间解耦",
      "服务层通过仓储接口访问数据，支持数据源替换"
    ]
  },
  "summary": "TypeScript Express API 项目，采用分层架构（MVC变体），包含路由、控制器、服务、仓储四层。核心特点是使用依赖注入实现模块解耦，服务层封装业务逻辑，仓储层抽象数据访问。"
}
```

## 示例 2：Go 项目分析

**输入**：分析一个 Go 微服务项目的代码结构

**执行步骤**：

1. 目录扫描：识别 cmd/, internal/, pkg/ 标准 Go 项目结构
2. 符号索引：分析 internal/ 下的包和导出符号
3. 依赖分析：使用 grep 查找 import 语句，建立包依赖图
4. 模式识别：识别 interface 定义和实现，发现依赖注入模式

**输出**：
```json
{
  "project_type": "golang",
  "modules": [
    {
      "name": "internal/auth",
      "path": "internal/auth",
      "purpose": "认证授权服务，提供 JWT 生成和验证",
      "symbols_count": 12,
      "key_files": ["service.go", "jwt.go"],
      "visibility": "internal"
    }
  ],
  "dependencies": [
    {
      "from": "cmd/api",
      "to": "internal/auth",
      "type": "import",
      "strength": "strong",
      "symbols": ["NewAuthService", "Authenticate"],
      "reason": "API 服务依赖认证服务验证用户身份"
    }
  ],
  "architecture": {
    "style": "microservices",
    "layers": ["cmd (entry points)", "internal (core business)", "pkg (shared)"],
    "key_decisions": [
      "使用 internal/ 目录限制包可见性",
      "通过接口定义抽象依赖，支持 mock 测试"
    ]
  },
  "summary": "Go 微服务项目，遵循标准 Go 项目布局，使用 internal/ 限制包可见性。采用接口驱动设计，核心业务逻辑通过接口抽象依赖，便于测试和扩展。"
}
```

</examples>

<!-- /STATIC_CONTENT -->
