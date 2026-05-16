---
name: core
description: |
  跨语言命名规范权威指南 — 覆盖变量/函数/类型/常量/包/文件/分支/API/DB 字段的命名风格、缩写规约、布尔前缀、动词搭配与防误读。
  Use when 重命名符号、新建模块/文件、代码审查命名问题、设计 API 字段、定义数据库列、起 git 分支或 PR 标题、对比 snake_case/camelCase/PascalCase 选型。
  Also triggers on "命名建议"、"重命名"、"这个名字好不好"、"how should I name"、"naming convention"、"rename"。
allowed-tools: Read, Grep, Glob
---

# 命名规范核心

命名是接口设计。命名错 → 后续所有引用、文档、测试都跟着错。改名成本远高于一次想清楚的成本。

## 适用范围

- 适用于所有编程语言通用规则；语言特定规则参考各语言插件（python / golang / typescript 等）
- 适用于代码符号 + 文件路径 + git 分支 + PR/commit + URL/API 字段 + DB 列

## 决策顺序（按优先级）

遇到命名问题，按以下顺序判断：

1. **语言社区强制规范** —— PEP 8 / Go Effective / Rust API Guidelines / Microsoft .NET / Google Style Guide 有明确规定时，无条件遵循
2. **项目已有约定** —— 现有代码模式优先于个人偏好（用 Grep 查相邻代码）
3. **本指南通用原则** —— 无社区/项目约定时回落到这里

## 核心原则

### 清晰性优先于简洁性

名称应让读者**无需阅读实现**即理解用途。

| 不好 | 好 | 原因 |
|------|-----|------|
| `d` / `data` / `obj` / `temp` | `userProfile` / `parsedConfig` | 泛化名无信息量 |
| `calc()` | `calculateTotalPrice()` | 缺主语+宾语 |
| `process(x)` | `validateAndPersist(order)` | "处理"是垃圾词 |
| `flag` | `isAuthenticated` | 单值 flag 无语义 |
| `mgr` / `hdlr` / `ctx` | `manager` / `handler` / `context` | 仅在极窄局部作用域允许缩写 |

### 一致性优先于个人审美

| 场景 | 规则 |
|------|------|
| 相同概念 | 全局统一一个词。`user` vs `account` vs `member` 选一个 |
| 相反操作对仗 | `start/stop` 不混 `begin/end`；`open/close`；`get/set`；`add/remove`；`create/destroy` |
| 时间字段 | 统一 `_at` 后缀（`created_at`/`updated_at`），存储用时间戳（int64 unix），不用字符串 |
| ID 字段 | 同项目内 `id`/`uid`/`userId` 选一种风格，不混用 |

### 避免歧义

- 单复数：集合用复数（`users []User`），单元素用单数（`user User`）
- 不用易混淆字符：`l`/`I`/`O`/`0`/`1` 单字母变量
- 不用否定布尔：`isNotReady` → 改 `isReady` 取反；`disableLogging` 在配置项可接受

## 大小写风格速查

| 风格 | 用途 | 示例 |
|------|------|------|
| `snake_case` | Python/Rust 变量函数；DB 列；URL 路径段 | `user_name`、`created_at` |
| `camelCase` | JS/TS/Java/C# 变量函数；JSON 字段（多数前端约定） | `userName`、`getUserById` |
| `PascalCase` | 类型/类/接口/枚举（几乎所有语言）；Go 导出符号 | `UserService`、`HttpClient` |
| `UPPER_SNAKE_CASE` | 常量 / 枚举值 / 环境变量 | `MAX_RETRY`、`DATABASE_URL` |
| `kebab-case` | 文件名（JS/TS 生态）、CLI flag、URL、CSS class | `user-profile.ts`、`--dry-run` |
| `lowercase` | Go 包名、Java 包名段 | `httputil`、`com.example.auth` |

## 缩写规约

广为人知的首字母缩写（acronym/initialism）按**所在风格的大小写规则**处理，**不要保持全大写**：

| 缩写 | snake_case | camelCase | PascalCase |
|------|------------|-----------|------------|
| ID | `user_id` | `userId` | `UserId`（Go/.NET 多数）/ `UserID`（Go 官方推荐 [Effective Go]） |
| URL | `api_url` | `apiUrl` | `ApiUrl` / `APIURL`（Go） |
| HTTP | `http_client` | `httpClient` | `HttpClient` / `HTTPClient`（Go） |
| JSON | `json_data` | `jsonData` | `JsonData` / `JSONData`（Go） |
| IO | `io_stream` | `ioStream` | `IoStream` / `IOStream`（Go） |

**关键**：Go 社区遵循 [Go Code Review Comments] 要求首字母缩写**整体大小写一致**（`URL`/`ID`/`HTTP`）；其他语言（Java/C#/TS）普遍**当作普通单词**首字母大写（`Url`/`Id`/`Http`）。**项目内统一一种**。

允许的缩写白名单（其余写完整单词）：`id` / `url` / `uri` / `http` / `json` / `xml` / `html` / `css` / `api` / `db` / `io` / `ip` / `tcp` / `udp` / `sql` / `uuid` / `os` / `fs`。

## 布尔命名

布尔变量/方法**必须**让人一眼看出 true/false 含义。前缀任选其一：

| 前缀 | 语义 | 示例 |
|------|------|------|
| `is` | 状态/属性 | `isReady`、`isAdmin`、`isValid` |
| `has` | 拥有/包含 | `hasChildren`、`hasPermission` |
| `can` | 能力/许可 | `canEdit`、`canRetry` |
| `should` | 推荐/期望 | `shouldRetry`、`shouldCache` |
| `will` | 未来动作 | `willExpire` |
| `did` | 过去事件（回调） | `didMount`、`didFinishLoading` |

**禁用**：单词布尔（`flag` / `status` / `enable`）。配置/常量例外：`ENABLE_DEBUG` 可接受。

## 函数命名（动词 + 宾语）

| 模式 | 用途 | 示例 |
|------|------|------|
| `get<Name>` | 同步读取，不可能失败 | `getUserName()` |
| `fetch<Name>` | 异步/IO 获取 | `fetchUser(id)` |
| `find<Name>` | 可能返回空 | `findUserByEmail()` |
| `list<Name>` | 返回集合 | `listActiveUsers()` |
| `create/update/delete<Name>` | CRUD 写操作 | `createOrder()` |
| `is/has/can<Cond>` | 谓词（返回 bool） | `isExpired()` |
| `to<Type>` | 类型转换 | `toJson()`、`toString()` |
| `parse<Format>` | 解析输入 | `parseQuery()` |
| `validate<Subject>` | 校验，抛错/返回错误 | `validateInput()` |
| `on<Event>` | 事件处理器 | `onSubmit()` |
| `handle<Event>` | 事件处理器（异步/复杂） | `handleRequest()` |

避免：`processX`、`doX`、`runX`、`executeX` — 这些动词无信息量，几乎总有更具体的替代词。

## 类/类型命名（名词或名词短语）

| 类别 | 后缀模式 | 示例 |
|------|----------|------|
| 服务 | `Service` | `UserService` |
| 仓储 | `Repository` / `Store` / `Dao` | `OrderRepository` |
| 工厂 | `Factory` / `Builder` | `ClientBuilder` |
| 异常 | `Error` / `Exception` | `NotFoundError` |
| 接口（语言相关） | Go 单方法 `-er`（`Reader`）；Java/C# `IXxx`；Python ABC 同类名 | `Reader`、`IUserRepo` |
| 配置 | `Config` / `Options` / `Settings` | `RetryOptions` |
| DTO/Model | 实体名本身 | `User`、`Order`（不加 `Model` 后缀，除非冲突） |

避免：`Manager` / `Helper` / `Util` / `Handler`（无明确职责 → 通常是"上帝类"前兆）。允许 `XxxHelper` 仅当确实是无状态纯函数集合。

## 文件命名

| 生态 | 风格 | 示例 |
|------|------|------|
| Python | `snake_case.py` | `user_service.py` |
| Go | `snake_case.go` 或 `lowercase.go` | `user_service.go` |
| Rust | `snake_case.rs` | `user_service.rs` |
| JS/TS（React/前端主流） | `kebab-case.ts` 或 `PascalCase.tsx`（组件） | `user-card.ts`、`UserCard.tsx` |
| Java/Kotlin | `PascalCase.java` 与类同名 | `UserService.java` |
| C/C++ | `snake_case.{c,cc,h}` 或 `PascalCase`（依项目） | `string_util.cc` |

测试文件后缀：`*_test.go`、`*.test.ts`、`test_*.py`、`*Test.java`。

## Git / PR / Commit 命名

```text
分支:  <type>/<scope>-<short-desc>          feature/auth-oauth-login
       <type> ∈ feature|fix|hotfix|chore|refactor|docs|test
Commit: <type>(<scope>): <subject>           feat(auth): add OAuth login flow
       <type> ∈ feat|fix|docs|style|refactor|perf|test|chore|build|ci
PR 标题: 同 commit 格式；正文用模板说明 why/what/how-to-test
```

参考 [Conventional Commits]。

## URL / API / DB 字段命名

| 层 | 规则 | 示例 |
|---|------|------|
| URL 路径 | kebab-case，复数名词，REST 谓词靠 HTTP method | `GET /api/v1/user-profiles/{id}` |
| 查询参数 | snake_case 或 camelCase（项目统一） | `?page_size=20&sort_by=created_at` |
| JSON 字段 | camelCase（前端主流）或 snake_case（Python/Ruby 后端） | `{"userId": 1, "createdAt": ...}` |
| DB 表/列 | snake_case，表用复数，列单数 | `users.first_name`、`orders.user_id` |
| 环境变量 | UPPER_SNAKE_CASE，前缀域名 | `STRIPE_API_KEY`、`DATABASE_URL` |

**端到端一致性**：DB 列 `user_id` → ORM 模型 `userId`（按语言） → JSON `userId` → URL `user_id` 或 `userId`。**项目层面定一次**，文档化在 `CONTRIBUTING.md`。

## 检查清单

每次写新名字过一遍：

- [ ] 不读实现能猜对用途？
- [ ] 符合语言社区规范？（PEP 8 / Effective Go / Rust API / .NET / Google Style）
- [ ] 与项目现有命名一致？（先 Grep 看周边）
- [ ] 缩写在白名单内或团队已知？
- [ ] 布尔有 `is/has/can/should/will/did` 前缀？
- [ ] 函数动词具体（非 `process/do/run/handle`）？
- [ ] 类无 `Manager/Helper/Util` 兜底后缀？
- [ ] 时间字段 `_at` 后缀 + 时间戳存储？
- [ ] 集合用复数，单元素用单数？

## 权威参考

| 资源 | 适用范围 | URL |
|------|---------|-----|
| PEP 8 | Python | https://peps.python.org/pep-0008/#naming-conventions |
| Effective Go | Go | https://go.dev/doc/effective_go#names |
| Go Code Review Comments | Go 缩写规约 | https://go.dev/wiki/CodeReviewComments#initialisms |
| Rust API Guidelines | Rust | https://rust-lang.github.io/api-guidelines/naming.html |
| Microsoft .NET Naming | C# / .NET | https://learn.microsoft.com/dotnet/standard/design-guidelines/naming-guidelines |
| Google Java Style | Java | https://google.github.io/styleguide/javaguide.html#s5-naming |
| Google TypeScript Style | TS | https://google.github.io/styleguide/tsguide.html#identifiers |
| Airbnb JavaScript Style | JS | https://github.com/airbnb/javascript#naming-conventions |
| Conventional Commits | Git commit | https://www.conventionalcommits.org/ |
