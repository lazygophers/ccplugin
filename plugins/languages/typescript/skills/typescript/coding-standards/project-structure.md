# TypeScript 项目结构规范

## 核心原则

### ✅ 必须遵守

1. **按功能组织** - 按业务功能而非文件类型组织
2. **层级清晰** - 明确的目录层级，避免过深嵌套
3. **命名一致** - 目录和文件命名保持一致
4. **索引文件** - 使用 index.ts 简化导入
5. **类型集中** - 类型定义放在专门的 types 目录

### ❌ 禁止行为

- 按文件类型组织（components、hooks、utils 分散各处）
- 过深的目录嵌套（超过 4 层）
- 不一致的命名风格
- 循环依赖

## 单一应用结构

### 推荐目录布局

```
project/
├── src/
│   ├── app/                    # 应用入口和路由
│   │   ├── routes/            # 路由配置
│   │   ├── store/             # 状态管理
│   │   └── config.ts          # 应用配置
│   │
│   ├── components/             # UI 组件
│   │   ├── ui/                # 基础 UI 组件（按钮、输入框等）
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── index.ts
│   │   ├── forms/             # 表单组件
│   │   ├── layouts/           # 布局组件
│   │   └── index.ts
│   │
│   ├── features/               # 功能模块
│   │   ├── auth/              # 认证功能
│   │   │   ├── api/           # API 调用
│   │   │   │   ├── queries.ts  # React Query hooks
│   │   │   │   └── mutations.ts
│   │   │   ├── components/    # 功能特定组件
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── index.ts
│   │   │   ├── hooks/         # 功能特定 hooks
│   │   │   │   ├── useAuth.ts
│   │   │   │   └── index.ts
│   │   │   ├── types/         # 功能特定类型
│   │   │   │   ├── types.ts
│   │   │   │   └── index.ts
│   │   │   ├── utils/         # 功能特定工具
│   │   │   │   └── validators.ts
│   │   │   └── index.ts       # 功能入口
│   │   │
│   │   └── users/             # 用户功能
│   │       ├── api/
│   │       ├── components/
│   │       ├── hooks/
│   │       ├── types/
│   │       ├── utils/
│   │       └── index.ts
│   │
│   ├── lib/                    # 工具函数（跨功能）
│   │   ├── api/               # API 客户端
│   │   │   ├── client.ts
│   │   │   └── index.ts
│   │   ├── utils/             # 通用工具函数
│   │   │   ├── date.ts
│   │   │   ├── string.ts
│   │   │   └── index.ts
│   │   ├── validators/        # 通用验证器
│   │   │   ├── zod.ts
│   │   │   └── index.ts
│   │   └── formatters/        # 格式化函数
│   │       └── index.ts
│   │
│   ├── hooks/                  # 全局 hooks（跨功能）
│   │   ├── useDebounce.ts
│   │   ├── useLocalStorage.ts
│   │   └── index.ts
│   │
│   ├── types/                  # 全局类型定义
│   │   ├── api.ts             # API 相关类型
│   │   ├── models.ts          # 数据模型
│   │   └── index.ts
│   │
│   ├── styles/                 # 样式文件
│   │   ├── globals.css
│   │   └── components.css
│   │
│   ├── App.tsx                 # 应用根组件
│   ├── main.tsx                # 应用入口
│   └── vite-env.d.ts           # Vite 环境类型
│
├── public/                     # 静态资源
├── tests/                      # 测试文件（镜像 src 结构）
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vitest.config.ts
```

### 索引文件使用

```typescript
// ✅ 正确 - 使用 index.ts 简化导入
// src/components/ui/index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Select } from './Select';

// 使用
import { Button, Input, Select } from '@/components/ui';

// ❌ 避免 - 深层相对路径导入
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

// ✅ 或使用路径别名
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
```

## 功能模块结构

### 标准功能模块

```
features/
└── auth/                       # 认证功能模块
    ├── api/                    # API 层
    │   ├── queries.ts          # 查询 hooks
    │   ├── mutations.ts        # 变更 hooks
    │   └── index.ts
    │
    ├── components/             # 组件
    │   ├── LoginForm.tsx
    │   ├── RegisterForm.tsx
    │   ├── ResetPasswordForm.tsx
    │   └── index.ts
    │
    ├── hooks/                  # 功能特定 hooks
    │   ├── useAuth.ts
    │   ├── useLogin.ts
    │   └── index.ts
    │
    ├── types/                  # 类型定义
    │   ├── types.ts            # 接口、类型定义
    │   ├── schemas.ts          # Zod schemas
    │   └── index.ts
    │
    ├── utils/                  # 工具函数
    │   ├── validators.ts
    │   └── index.ts
    │
    ├── constants.ts            # 常量
    └── index.ts                # 功能入口
```

### 功能入口示例

```typescript
// features/auth/index.ts
// 导出所有公开的 API

// Types
export type * from './types';

// Hooks
export { useAuth } from './hooks/useAuth';
export { useLogin } from './hooks/useLogin';

// Components
export { LoginForm } from './components/LoginForm';
export { RegisterForm } from './components/RegisterForm';

// 使用
import { LoginForm, useAuth } from '@/features/auth';
```

## Monorepo 结构

### Monorepo 布局

```
workspace/
├── apps/
│   ├── web/                    # Next.js 前端
│   │   ├── src/
│   │   │   ├── app/           # App Router
│   │   │   ├── components/
│   │   │   └── lib/
│   │   └── package.json
│   │
│   └── api/                    # NestJS/Express 后端
│       ├── src/
│       │   ├── modules/
│       │   └── main.ts
│       └── package.json
│
├── packages/
│   ├── shared/                 # 共享类型
│   │   ├── src/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   ├── ui/                     # 共享 UI 组件
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── utils/
│   │   └── package.json
│   │
│   └── eslint-config/          # 共享 ESLint 配置
│       └── index.js
│
├── pnpm-workspace.yaml
└── turbo.json
```

### 依赖规则

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

```json
// apps/web/package.json
{
  "name": "@workspace/web",
  "dependencies": {
    // ✅ 依赖共享包
    "@workspace/shared": "workspace:*",
    "@workspace/ui": "workspace:*"
  }
}
```

## 测试文件结构

### 测试目录

```
tests/
├── unit/                       # 单元测试
│   ├── components/
│   │   └── Button.test.tsx
│   ├── hooks/
│   │   └── useAuth.test.ts
│   └── utils/
│       └── date.test.ts
│
├── integration/                # 集成测试
│   └── api/
│       └── auth.test.ts
│
├── e2e/                        # 端到端测试
│   └── scenarios/
│       └── login.spec.ts
│
├── mocks/                      # Mock 数据
│   ├── handlers.ts
│   └── data.ts
│
└── setup.ts                    # 测试设置
```

### 同目录测试

```
src/
└── features/
    └── auth/
        ├── useAuth.ts
        ├── useAuth.test.ts     # 同目录测试文件
        └── index.ts
```

## 检查清单

创建新项目时，确保：

- [ ] 按功能组织代码
- [ ] 使用 features 目录
- [ ] 每个功能有独立的 api、components、hooks、types
- [ ] 使用 index.ts 简化导入
- [ ] 配置了路径别名（@/*）
- [ ] 测试文件与源文件位置一致
- [ ] 没有循环依赖
- [ ] 目录层级不超过 4 层
