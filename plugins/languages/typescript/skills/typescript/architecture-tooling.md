# TypeScript 架构设计和工具链

## 架构设计规范

### 分层架构

```
Presentation Layer (React Components)
    ↓
Application Layer (Hooks, Services)
    ↓
Domain Layer (Business Logic, Types)
    ↓
Infrastructure Layer (API, Database)
```

**关键特性**：

- 依赖方向从上到下，下层不依赖上层
- 每层有明确的职责
- 通过类型定义实现层间通信

### 领域驱动设计（DDD）

```typescript
// ✅ 领域模型 - 纯业务逻辑，不依赖框架
type UserId = string & { readonly __brand: unique symbol };
type Email = string & { readonly __brand: unique symbol };

class User {
  private constructor(
    public readonly id: UserId,
    public readonly email: Email,
    public readonly name: string,
  ) {}

  static create(email: Email, name: string): User {
    return new User(
      crypto.randomUUID() as UserId,
      email,
      name,
    );
  }

  changeName(newName: string): User {
    return new User(this.id, this.email, newName);
  }
}

// ✅ Repository 接口 - 定义数据访问契约
interface IUserRepository {
  save(user: User): Promise<void>;
  findById(id: UserId): Promise<User | null>;
  findByEmail(email: Email): Promise<User | null>;
}
```

## 项目结构

### Monorepo 结构（推荐）

```
workspace/
├── apps/
│   ├── web/                    # Next.js 前端应用
│   │   ├── src/
│   │   │   ├── app/           # App Router
│   │   │   ├── components/    # 共享组件
│   │   │   ├── lib/           # 工具函数
│   │   │   └── styles/        # 样式文件
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── api/                    # NestJS/Express 后端应用
│       ├── src/
│       │   ├── modules/       # 功能模块
│       │   ├── common/        # 公共代码
│       │   └── main.ts
│       └── package.json
│
├── packages/
│   ├── shared/                 # 共享类型定义
│   │   ├── src/
│   │   │   ├── types/         # 类型定义
│   │   │   ├── domain/        # 领域模型
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
├── package.json
├── pnpm-lock.yaml
└── turbo.json                  # Turborepo 配置
```

### 单一应用结构

```
project/
├── src/
│   ├── app/                    # 应用入口
│   │   ├── routes/            # 路由定义
│   │   └── store/             # 状态管理
│   │
│   ├── components/             # UI 组件
│   │   ├── ui/                # 基础 UI 组件
│   │   ├── forms/             # 表单组件
│   │   └── layouts/           # 布局组件
│   │
│   ├── features/               # 功能模块
│   │   ├── auth/              # 认证功能
│   │   │   ├── api/           # API 调用
│   │   │   ├── components/    # 特定组件
│   │   │   ├── hooks/         # 自定义 Hooks
│   │   │   ├── types/         # 类型定义
│   │   │   └── index.ts
│   │   └── users/             # 用户功能
│   │
│   ├── lib/                    # 工具函数
│   │   ├── api/               # API 客户端
│   │   ├── utils/             # 通用工具
│   │   └── validators/        # 验证器
│   │
│   ├── hooks/                  # 自定义 Hooks
│   ├── types/                  # 全局类型定义
│   └── styles/                 # 样式文件
│
├── public/                     # 静态资源
├── tests/                      # 测试文件
├── package.json
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
└── eslint.config.js
```

## 依赖管理

### pnpm Workspace

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### 依赖安装规范

```bash
# ✅ 安装生产依赖
pnpm add package-name

# ✅ 安装开发依赖
pnpm add -D package-name

# ✅ 安装到特定包
pnpm --filter web add react

# ✅ 安装到根目录
pnpm add -w package-name

# ❌ 避免 - 使用 npm 或 yarn
npm install package-name
yarn add package-name
```

### 依赖版本管理

```json
// package.json - 使用精确版本或范围
{
  "dependencies": {
    // ✅ 推荐 - 使用精确版本
    "react": "18.3.1",
    "typescript": "5.9.2",

    // ✅ 或使用 ~ (补丁版本更新)
    "zod": "~3.23.8",  // 允许 3.23.x

    // ⚠️ 谨慎使用 ^ (次版本更新)
    "next": "^15.0.0"  // 允许 15.x.x
  },
  "devDependencies": {
    "vite": "6.0.0",
    "vitest": "3.0.0"
  }
}
```

## 工具链配置

### TypeScript 配置

```json
// tsconfig.json - 基础配置
{
  "compilerOptions": {
    // 语言与环境
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",

    // 模块解析
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,

    // 类型检查
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,

    // 互操作约束
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,

    // 完成性
    "skipLibCheck": true,

    // 路径映射
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/types/*": ["./src/types/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "build"]
}
```

### Monorepo TypeScript 配置

```json
// tsconfig.json - 根配置
{
  "files": [],
  "references": [
    { "path": "./apps/web" },
    { "path": "./apps/api" },
    { "path": "./packages/shared" },
    { "path": "./packages/ui" }
  ]
}

// apps/web/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "references": [
    { "path": "../../packages/shared" },
    { "path": "../../packages/ui" }
  ],
  "include": ["src"]
}
```

### Vite 配置

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/lib': path.resolve(__dirname, './src/lib'),
      '@/types': path.resolve(__dirname, './src/types'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
});
```

### Vitest 配置

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### ESLint 配置

```javascript
// eslint.config.js
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import jsxA11yPlugin from 'eslint-plugin-jsx-a11y';

export default [
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
      'jsx-a11y': jsxA11yPlugin,
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      }],
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
];
```

### Prettier 配置

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

## 开发工作流

### 初始化项目

```bash
# 使用 pnpm 创建项目
pnpm create vite my-app --template react-ts

# 或使用 Next.js
pnpm create next-app my-app --typescript --eslint

# 进入目录
cd my-app

# 安装依赖
pnpm install
```

### 开发命令

```bash
# 开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 预览生产版本
pnpm preview

# 运行测试
pnpm test

# 运行测试（UI 模式）
pnpm test:ui

# 运行类型检查
pnpm typecheck

# 运行 ESLint
pnpm lint

# 自动修复 ESLint 问题
pnpm lint:fix

# 格式化代码
pnpm format
```

### Git Hooks（Husky + lint-staged）

```bash
# 安装 Husky
pnpm add -D husky lint-staged

# 初始化
pnpm exec husky init

# 配置 pre-commit hook
echo "pnpm lint-staged" > .husky/pre-commit

# 配置 lint-staged
```

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md}": [
      "prettier --write"
    ]
  }
}
```

## 检查清单

初始化项目前，确保：

- [ ] 使用 pnpm 作为包管理器
- [ ] tsconfig.json 启用了 strict 模式
- [ ] 配置了路径映射（@ 别名）
- [ ] 使用 Vite 作为构建工具
- [ ] 使用 Vitest 作为测试框架
- [ ] 配置了 ESLint 和 Prettier
- [ ] 配置了 Husky 和 lint-staged
- [ ] 设置了测试覆盖率阈值
- [ ] 配置了代码分割

提交代码前，确保：

- [ ] `pnpm typecheck` 通过
- [ ] `pnpm lint` 通过
- [ ] `pnpm test` 通过，覆盖率达标
- [ ] `pnpm build` 成功
- [ ] 代码格式符合 Prettier 规范
