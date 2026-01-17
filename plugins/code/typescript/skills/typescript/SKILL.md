---
name: typescript
description: TypeScript 5.9+ 开发规范 - 包含类型系统、编码规范、项目结构、测试策略和最佳实践
---

# TypeScript 5.9+ 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 版本、命名约定、基本开发流程 | 快速入门 |
| [type-system.md](type-system.md) | 类型系统详解、泛型、Union、错误处理 | 类型设计 |
| [tooling-testing.md](tooling-testing.md) | 工具链、测试、项目结构、性能优化 | 开发配置 |

## 版本和环境

- **TypeScript**: 5.9+ (当前稳定版本)
- **Node.js**: 20+ LTS
- **包管理器**: pnpm (推荐) → Yarn Berry → npm
- **运行时**: Node.js 或 Deno
- **测试框架**: Vitest (推荐) 优于 Jest
- **代码风格**: ESLint + Prettier

## 命名约定

### 类型系统命名

```typescript
// ✅ 正确
type UserDTO = { id: string; name: string };
interface ApiResponse { data: unknown; status: number }
type Status = 'active' | 'inactive' | 'pending';
enum Role { Admin, User, Guest }

// ❌ 错误
type IUser = { };      // 禁止使用 I 前缀（C# 约定）
type user = { };       // 类型使用 PascalCase
interface userData { } // 接口使用 PascalCase
```

### 变量和函数命名

```typescript
// ✅ 正确
const userName: string = 'John';
function getUserById(id: string): Promise<User> { }
const isActive = true;
const MAX_RETRIES = 3;

// ❌ 错误
const user_name: string = 'John';     // 使用 camelCase
function Get_User_By_Id(id: string) { } // 函数使用 camelCase
const maxRetries = 3;                  // 常量使用 UPPER_SNAKE_CASE 或 camelCase
```

## 类型系统详解

参见 [type-system.md](type-system.md) 了解严格模式、泛型约束、Union 类型、常见类型模式和错误处理的详细内容。

## 编码规范

参见 [tooling-testing.md](tooling-testing.md) 了解代码风格、注释规范、导入规范和配置详情。

## 项目结构

参见 [tooling-testing.md](tooling-testing.md) 了解完整的项目结构、依赖管理和公开接口设计。

## 常见类型模式

参见 [type-system.md](type-system.md) 了解异步操作结果、可选属性、错误处理和其他常见类型模式。

## 测试规范

参见 [tooling-testing.md](tooling-testing.md) 了解 Vitest 配置、单元测试最佳实践和测试覆盖率目标。

## 工具链配置

参见 [tooling-testing.md](tooling-testing.md) 了解 tsconfig.json、包管理器、构建工具和性能优化配置。

## 常见反模式和最佳实践

参见 [type-system.md](type-system.md) 了解常见类型反模式和异步操作反模式的解决方案；参见 [tooling-testing.md](tooling-testing.md) 了解框架集成、性能优化和快速检查清单。
