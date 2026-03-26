---
description: API 探索规范 - REST/GraphQL/gRPC API 端点分析、参数提取、认证机制识别
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:explorer-api) - API 探索规范

<scope>

当你需要深入理解项目的 API 设计和规范时使用此 skill。适用于分析 REST API 端点和参数、解析 GraphQL schema 和 resolver、提取 OpenAPI/Swagger 定义、识别认证和授权机制、理解 API 版本管理策略。

支持的 API 类型：
- **REST**: OpenAPI 3.x, Swagger 2.0, 自定义路由
- **GraphQL**: Schema SDL, Introspection, Code-first
- **gRPC**: Protocol Buffers, Service definitions
- **WebSocket**: Socket.io, ws

</scope>

<core_principles>

规范文件优先。如果项目有 OpenAPI/Swagger/GraphQL schema 定义文件，这些是 API 的权威来源。优先分析规范文件，再补充代码中的路由定义。

端点完整性。必须识别所有 API 端点，包括文档中未记录的隐藏端点。通过搜索路由注册代码来确保完整性。

契约驱动。API 的核心价值是其契约（请求参数、响应格式、错误处理）。必须完整提取每个端点的输入输出规范。

安全维度。认证和授权是 API 安全的基础。必须识别认证方式、授权策略和保护机制。

</core_principles>

<detection_patterns>

**规范文件识别**：

| 类型 | 文件模式 | 识别标志 |
|------|---------|---------|
| OpenAPI 3.x | `openapi.yaml/json`, `swagger.yaml/json` | `openapi: "3.x"` |
| Swagger 2.0 | `swagger.yaml/json` | `swagger: "2.0"` |
| GraphQL SDL | `schema.graphql`, `*.gql` | `type Query {` |
| Protocol Buffer | `*.proto` | `service XxxService {` |

**路由注册模式**：

| 框架 | 路由模式 |
|------|---------|
| Express | `app.get("/path", handler)`, `router.use()` |
| NestJS | `@Get("/path")`, `@Controller("/api")` |
| FastAPI | `@app.get("/path")`, `APIRouter()` |
| Gin | `r.GET("/path", handler)`, `r.Group("/api")` |
| Spring | `@GetMapping("/path")`, `@RestController` |
| Django | `path("/api/", views.api)`, `urlpatterns` |

**GraphQL 模式**：

| 方式 | 识别标志 |
|------|---------|
| SDL-first | `.graphql` 文件, `typeDefs` |
| Code-first | `@ObjectType()`, `@Field()`, `GraphQLObjectType` |
| Resolver | `@Resolver()`, `@Query()`, `@Mutation()` |

</detection_patterns>

<output_format>

```json
{
  "api_type": "REST|GraphQL|gRPC|Mixed",
  "spec_file": "openapi.yaml|null",
  "base_url": "/api/v1",
  "endpoints": [
    {
      "method": "GET",
      "path": "/users/{id}",
      "handler": "GetUser",
      "file": "handlers/user.go:25",
      "parameters": [...],
      "responses": {...},
      "auth": "JWT",
      "middleware": ["auth"]
    }
  ],
  "schemas": {...},
  "auth": {
    "type": "JWT|OAuth|API Key",
    "config": "配置路径"
  },
  "versioning": "URL path|Header|None",
  "summary": "API 架构总结"
}
```

</output_format>

<tools_guide>

**规范文件搜索**：
- `glob("**/openapi.{yaml,yml,json}")` + `glob("**/swagger.{yaml,yml,json}")`
- `glob("**/*.graphql")` + `glob("**/*.gql")`
- `glob("**/*.proto")`

**路由搜索**：
- Express/Koa: `grep("app\\.(get|post|put|delete|patch)|router\\.(get|post)")`
- NestJS: `grep("@Get|@Post|@Put|@Delete|@Controller")`
- FastAPI: `grep("@app\\.(get|post)|@router\\.(get|post)|APIRouter")`
- Gin: `grep("\\.(GET|POST|PUT|DELETE)\\(|Group\\(")`
- Spring: `grep("@GetMapping|@PostMapping|@RequestMapping")`

**认证搜索**：
- `grep("JWT|Bearer|Authorization|authenticate|passport")`
- `grep("@UseGuards|@Authorized|login_required|middleware")`

**符号级分析**：
- `serena:find_symbol` → 查找处理函数
- `serena:get_symbols_overview` → 获取参数类型
- `serena:find_referencing_symbols` → 追踪中间件引用

</tools_guide>

<guidelines>

先搜索规范文件，再补充代码路由。规范文件是权威来源，代码中可能有未文档化的端点。

GraphQL 项目需要分析 schema 和 resolver 两个维度。schema 定义了 API 契约，resolver 实现了业务逻辑。

注意 API 版本管理。多版本 API 可能在不同路径或使用不同的 header 来区分。

</guidelines>
