# TypeScript 文档规范

## 核心原则

### ✅ 必须遵守

1. **README 必需** - 每个项目都有 README.md
2. **API 文档** - 公开 API 有类型文档
3. **变更日志** - 维护 CHANGELOG.md
4. **代码示例** - 文档包含可运行的示例
5. **保持更新** - 代码变更时同步更新文档

### ❌ 禁止行为

- 过时的文档
- 没有示例的 API 文档
- 抽象的描述（缺少具体细节）

## README 规范

### 项目 README

```markdown
# 项目名称

简短描述项目（一句话说明项目功能）。

## 功能特性

- ✅ 支持用户认证和授权
- ✅ 实时数据同步
- ✅ 响应式设计

## 技术栈

- TypeScript 5.9+
- React 18+
- Vite 6+
- Vitest 3+

## 快速开始

### 前置要求

- Node.js 20+
- pnpm 9+

### 安装

\`\`\`bash
# 克隆仓库
git clone https://github.com/username/project.git
cd project

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
\`\`\`

## 项目结构

\`\`\`
src/
├── components/     # UI 组件
├── features/       # 功能模块
├── lib/            # 工具函数
├── hooks/          # 自定义 Hooks
└── types/          # 类型定义
\`\`\`

## 开发

\`\`\`bash
# 类型检查
pnpm typecheck

# 代码检查
pnpm lint

# 运行测试
pnpm test

# 构建生产版本
pnpm build
\`\`\`

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

## 许可证

MIT
```

### 组件 README

```markdown
# Button 组件

基础按钮组件，支持多种样式和状态。

## 功能特性

- 支持多种尺寸（small, medium, large）
- 支持多种变体（primary, secondary, ghost）
- 支持加载状态
- 支持禁用状态

## API

### ButtonProps

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| children | ReactNode | - | 按钮内容 |
| variant | 'primary' \| 'secondary' \| 'ghost' | 'primary' | 按钮变体 |
| size | 'small' \| 'medium' \| 'large' | 'medium' | 按钮尺寸 |
| disabled | boolean | false | 是否禁用 |
| loading | boolean | false | 是否加载中 |
| onClick | () => void | - | 点击回调 |

## 示例

### 基础用法

\`\`\`tsx
import { Button } from '@/components/ui/button';

function Example() {
  return <Button>Click me</Button>;
}
\`\`\`

### 不同变体

\`\`\`tsx
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="ghost">Ghost</Button>
\`\`\`

### 加载状态

\`\`\`tsx
<Button loading>Loading...</Button>
\`\`\`
```

## API 文档

### JSDoc 注释

```typescript
/**
 * 用户服务类。
 *
 * 提供用户的 CRUD 操作和业务逻辑处理。
 *
 * @example
 * ```ts
 * const service = new UserRepository(apiClient);
 * const user = await service.findById('123');
 * ```
 */
export class UserRepository {
  /**
   * 创建用户仓库实例。
   *
   * @param client - HTTP 客户端用于 API 调用
   * @param config - 可选配置
   */
  constructor(
    private readonly client: HttpClient,
    private readonly config?: RepositoryConfig,
  ) {}

  /**
   * 根据 ID 查找用户。
   *
   * @param id - 用户 ID（必须是有效的 UUID）
   * @returns 用户对象，如果不存在则返回 null
   * @throws {ValidationError} 如果 ID 格式无效
   * @throws {ApiError} 如果 API 调用失败
   *
   * @example
   * ```ts
   * const user = await repository.findById('123e4567-e89b-12d3-a456-426614174000');
   * if (user) {
   *   console.log(user.name);
   * }
   * ```
   */
  async findById(id: string): Promise<User | null> {
    // ...
  }

  /**
   * 创建新用户。
   *
   * @param data - 用户创建数据
   * @returns 创建的用户对象
   * @throws {ValidationError} 如果数据验证失败
   *
   * @example
   * ```ts
   * const user = await repository.create({
   *   name: 'John',
   *   email: 'john@example.com',
   * });
   * ```
   */
  async create(data: CreateUserInput): Promise<User> {
    // ...
  }
}
```

### 类型文档

```typescript
/**
 * 用户类型。
 *
 * @remarks
 * 包含用户的基本信息和状态。
 *
 * @example
 * ```ts
 * const user: User = {
 *   id: '123',
 *   name: 'John',
 *   email: 'john@example.com',
 *   status: 'active',
 * };
 * ```
 */
export type User = {
  /** 用户唯一标识符（UUID 格式） */
  id: string;

  /** 用户名称（2-50 字符） */
  name: string;

  /** 用户邮箱地址 */
  email: string;

  /**
   * 用户状态。
   *
   * - `active`: 活跃用户，可以正常使用系统
   * - `inactive`: 非活跃用户，不能登录
   * - `suspended`: 已暂停用户，违反了使用条款
   */
  status: UserStatus;
};
```

## 变更日志

### CHANGELOG 格式

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 新增用户认证功能
- 添加深色模式支持

### Changed
- 重构状态管理逻辑
- 更新依赖到最新版本

### Fixed
- 修复按钮点击没有响应的问题
- 修复移动端显示问题

### Removed
- 移除旧的 API 客户端

## [1.2.0] - 2025-01-15

### Added
- 新增批量导入功能
- 添加数据导出功能

### Fixed
- 修复登录重定向问题
```

## 代码示例

### 示例目录结构

```
examples/
├── basic-usage/
│   ├── index.ts
│   └── README.md
├── advanced/
│   ├── index.ts
│   └── README.md
└── integration/
    ├── index.ts
    └── README.md
```

### 可运行示例

```markdown
## 示例

### 基础用法

\`\`\`ts title="examples/basic-usage/index.ts"
import { Button } from '@workspace/ui';

function Example() {
  return (
    <Button onClick={() => console.log('clicked')}>
      Click me
    </Button>
  );
}
\`\`\`

### 高级用法

\`\`\`ts title="examples/advanced/index.ts"
import { Button } from '@workspace/ui';
import { useAuth } from '@/hooks/useAuth';

function AdvancedExample() {
  const { user, logout } = useAuth();

  return (
    <Button
      variant="secondary"
      disabled={!user}
      onClick={logout}
    >
      Logout
    </Button>
  );
}
\`\`\`
```

## 检查清单

发布新版本前，确保：

- [ ] README.md 包含项目概述和快速开始
- [ ] 公开 API 有 JSDoc 文档
- [ ] 复杂功能有使用示例
- [ ] CHANGELOG.md 记录了变更
- [ ] 文档与代码保持同步
