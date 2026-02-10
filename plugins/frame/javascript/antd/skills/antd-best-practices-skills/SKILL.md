---
name: antd-best-practices-skills
description: Ant Design 最佳实践完整指南 - 架构模式、代码规范、设计模式、项目组织
---

# antd-best-practices: Ant Design 最佳实践完整指南

## 概述

Ant Design 最佳实践模块提供企业级应用开发的标准和规范，涵盖项目架构、组件设计、代码规范、状态管理、性能优化、安全实践、可维护性等多个维度，帮助团队构建高质量、可维护的 Ant Design 应用。

### 为什么需要最佳实践

- **代码一致性** - 统一的代码风格和架构模式，降低团队协作成本
- **可维护性** - 清晰的项目结构和模块划分，便于长期维护和迭代
- **性能优化** - 避免常见的性能陷阱，提升用户体验
- **安全性** - 防范常见的安全风险，保护用户数据
- **可扩展性** - 灵活的架构设计，支持业务快速扩展

### 代码质量标准

- **TypeScript 优先** - 完整的类型定义，减少运行时错误
- **组件化思维** - 高内聚、低耦合的组件设计
- **性能意识** - 避免不必要的渲染，优化用户体验
- **可测试性** - 编写可测试的代码，提高代码质量
- **文档完善** - 清晰的注释和文档，便于团队协作

---

## 核心特性

- **标准项目架构** - 经过验证的目录结构和模块划分方案
- **组件设计模式** - 容器组件与展示组件分离、HOC、自定义 Hooks
- **代码规范** - 命名规范、文件组织、导入顺序
- **状态管理策略** - 本地状态 vs 全局状态的决策指南
- **样式管理** - CSS-in-JS、主题定制、响应式设计
- **错误处理** - 错误边界、异常捕获、用户提示
- **测试策略** - 单元测试、集成测试、E2E 测试
- **性能优化** - 渲染优化、代码分割、懒加载
- **安全实践** - XSS 防护、CSRF 防护、数据验证
- **可维护性** - 代码复用、模块化、文档化

---

## 项目架构

### 标准目录结构

推荐使用功能模块化的目录结构，按业务功能组织代码：

```
src/
├── assets/                    # 静态资源
│   ├── images/               # 图片资源
│   ├── icons/                # 图标资源
│   └── fonts/                # 字体资源
│
├── components/               # 通用组件（跨业务复用）
│   ├── ui/                   # 基础 UI 组件（Button, Input 等封装）
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts
│   │   └── Input/
│   ├── business/             # 业务组件（特定业务场景）
│   │   ├── UserCard/
│   │   ├── ProductList/
│   │   └── OrderTable/
│   └── layout/               # 布局组件
│       ├── PageHeader/
│       ├── ContentContainer/
│       └── Footer/
│
├── pages/                    # 页面组件（路由页面）
│   ├── home/
│   │   ├── index.tsx
│   │   ├── components/       # 页面私有组件
│   │   ├── hooks/            # 页面私有 hooks
│   │   ├── services/         # 页面私有 API
│   │   └── types.ts          # 页面类型定义
│   ├── user/
│   │   ├── index.tsx
│   │   └── detail.tsx
│   └── _app.tsx              # 应用根组件
│
├── hooks/                    # 全局自定义 Hooks
│   ├── useRequest.ts         # 请求 Hook
│   ├── useTable.ts           # 表格 Hook
│   ├── useForm.ts            # 表单 Hook
│   └── useAuth.ts            # 认证 Hook
│
├── services/                 # API 服务层
│   ├── api.ts                # API 基础配置
│   ├── user.ts               # 用户相关 API
│   ├── product.ts            # 产品相关 API
│   └── types.ts              # API 类型定义
│
├── stores/                   # 状态管理
│   ├── userStore.ts          # 用户状态
│   ├── appStore.ts           # 应用状态
│   └── index.ts              # Store 统一导出
│
├── utils/                    # 工具函数
│   ├── request.ts            # 请求封装
│   ├── format.ts             # 格式化函数
│   ├── validate.ts           # 验证函数
│   └── storage.ts            # 本地存储封装
│
├── constants/                # 常量定义
│   ├── config.ts             # 配置常量
│   ├── enum.ts               # 枚举定义
│   └── routes.ts             # 路由配置
│
├── types/                    # 全局类型定义
│   ├── user.ts               # 用户类型
│   ├── common.ts             # 通用类型
│   └── index.ts              # 类型统一导出
│
├── styles/                   # 全局样式
│   ├── global.css            # 全局 CSS
│   ├── variables.css         # CSS 变量
│   └── themes/               # 主题样式
│
├── App.tsx                   # 应用根组件
├── main.tsx                  # 应用入口
└── vite-env.d.ts            # Vite 类型声明
```

### 组件组织原则

#### 1. 单一职责原则

每个组件只负责一个功能点：

```tsx
// ✅ 好的做法：组件职责单一
function UserAvatar({ userId, size }: { userId: string; size: number }) {
  const { user } = useUser(userId);

  return <Avatar src={user?.avatar} size={size} />;
}

function UserInfo({ userId }: { userId: string }) {
  const { user } = useUser(userId);

  return (
    <div>
      <UserAvatar userId={userId} size={64} />
      <Typography.Text>{user?.name}</Typography.Text>
    </div>
  );
}

// ❌ 不好的做法：组件职责过多
function UserComponent({ userId }: { userId: string }) {
  const { user } = useUser(userId);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 一个组件做了太多事情：头像、信息、模态框
  return (
    <div>
      <Avatar src={user?.avatar} size={64} />
      <Typography.Text>{user?.name}</Typography.Text>
      <Modal open={isModalOpen} onOk={() => setIsModalOpen(false)}>
        {/* ... */}
      </Modal>
    </div>
  );
}
```

#### 2. 组件层次结构

保持组件层次的扁平化，避免过深的嵌套：

```tsx
// ✅ 好的做法：层次扁平
function UserPage() {
  return (
    <PageLayout>
      <UserHeader />
      <UserContent />
      <UserFooter />
    </PageLayout>
  );
}

// ❌ 不好的做法：嵌套过深
function UserPage() {
  return (
    <div>
      <div>
        <div>
          <div>
            <div>
              <UserHeader />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### 3. 组件复用策略

- **通用 UI 组件**：放在 `components/ui/`，跨项目复用
- **业务组件**：放在 `components/business/`，项目内复用
- **页面私有组件**：放在 `pages/[page]/components/`，不复用

```tsx
// components/ui/Button/index.tsx - 通用 UI 组件
export function Button({ children, variant, ...props }: ButtonProps) {
  return <AntButton type={variant} {...props}>{children}</AntButton>;
}

// components/business/UserCard/index.tsx - 业务组件
export function UserCard({ userId }: { userId: string }) {
  const { user } = useUser(userId);

  return (
    <Card>
      <UserAvatar userId={userId} />
      <Typography.Text>{user?.name}</Typography.Text>
    </Card>
  );
}

// pages/user/components/UserDetail/index.tsx - 页面私有组件
function UserDetail({ userId }: { userId: string }) {
  // 仅在 user 页面使用
  return <div>...</div>;
}
```

### 模块划分方案

#### 1. 按功能模块划分

适合中大型项目，按业务领域划分：

```
src/
├── modules/
│   ├── user/                 # 用户模块
│   │   ├── components/       # 用户相关组件
│   │   ├── services/         # 用户相关 API
│   │   ├── types.ts          # 用户类型定义
│   │   ├── index.tsx         # 用户模块入口
│   │   └── routes.ts         # 用户路由配置
│   ├── product/              # 产品模块
│   └── order/                # 订单模块
```

#### 2. 按技术层次划分

适合小型项目，按技术职责划分：

```
src/
├── components/               # 所有组件
├── services/                 # 所有 API
├── hooks/                    # 所有 Hooks
├── utils/                    # 所有工具函数
└── types/                    # 所有类型定义
```

#### 3. 混合划分（推荐）

结合功能模块和技术层次：

```
src/
├── components/               # 跨模块复用的组件
│   ├── ui/
│   └── business/
├── modules/                  # 业务模块
│   ├── user/
│   │   ├── components/       # 模块私有组件
│   │   ├── services/
│   │   └── hooks/
│   └── product/
├── shared/                   # 共享资源
│   ├── hooks/                # 全局 Hooks
│   ├── utils/                # 全局工具函数
│   └── types/                # 全局类型定义
```

---

## 组件设计模式

### 容器组件 vs 展示组件

将组件分为容器组件（Container）和展示组件（Presentational）：

#### 展示组件（Presentational Components）

- **关注点**：UI 展示，如何渲染
- **数据来源**：通过 props 接收
- **无状态**：或仅有本地 UI 状态
- **可复用**：不包含业务逻辑

```tsx
// components/business/UserCard/UserCard.tsx
interface UserCardProps {
  name: string;
  email: string;
  avatar?: string;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function UserCard({ name, email, avatar, onEdit, onDelete }: UserCardProps) {
  return (
    <Card
      cover={avatar && <Card.Cover src={avatar} />}
      actions={[
        onEdit && <Button key="edit" onClick={onEdit}>Edit</Button>,
        onDelete && <Button key="delete" danger onClick={onDelete}>Delete</Button>,
      ].filter(Boolean)}
    >
      <Card.Meta
        title={name}
        description={email}
      />
    </Card>
  );
}
```

#### 容器组件（Container Components）

- **关注点**：业务逻辑，如何工作
- **数据来源**：从 API、Store 获取
- **有状态**：管理业务状态
- **不复用**：特定业务场景

```tsx
// pages/user/components/UserCardContainer.tsx
import { UserCard } from '@/components/business/UserCard';
import { useUser } from '@/hooks/useUser';
import { useDeleteUser } from '@/hooks/useDeleteUser';

export function UserCardContainer({ userId }: { userId: string }) {
  const { user, loading } = useUser(userId);
  const deleteUser = useDeleteUser();

  const handleEdit = () => {
    // 导航到编辑页面
    navigate(`/user/${userId}/edit`);
  };

  const handleDelete = async () => {
    await deleteUser(userId);
  };

  if (loading) {
    return <Skeleton active />;
  }

  return (
    <UserCard
      name={user?.name || ''}
      email={user?.email || ''}
      avatar={user?.avatar}
      onEdit={handleEdit}
      onDelete={handleDelete}
    />
  );
}
```

### 高阶组件（HOC）

用于复用组件逻辑：

#### 基础 HOC 模式

```tsx
// hooks/withAuth.tsx
import { ComponentType } from 'react';
import { Redirect } from 'react-router-dom';

interface WithAuthProps {
  isAuthenticated: boolean;
}

export function withAuth<P extends object>(
  WrappedComponent: ComponentType<P>
): ComponentType<P & WithAuthProps> {
  return (props) => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    if (!isAuthenticated) {
      return <Redirect to="/login" />;
    }

    return <WrappedComponent {...props} />;
  };
}

// 使用
const ProtectedPage = withAuth(function Dashboard() {
  return <div>Dashboard</div>;
});
```

#### 组合多个 HOC

```tsx
// hooks/withLoading.tsx
import { ComponentType } from 'react';
import { Spin } from 'antd';

interface WithLoadingProps<T> {
  data?: T;
  loading?: boolean;
}

export function withLoading<T, P extends WithLoadingProps<T>>(
  WrappedComponent: ComponentType<P>
): ComponentType<Omit<P, 'loading'>> {
  return (props) => {
    const { loading, data, ...rest } = props as P;

    if (loading) {
      return <Spin size="large" />;
    }

    if (!data) {
      return <Empty description="No data" />;
    }

    return <WrappedComponent {...(rest as P)} data={data} />;
  };
}

// 组合使用
const EnhancedUserCard = withAuth(withLoading(UserCard));
```

### 自定义 Hooks 封装

将可复用逻辑封装为自定义 Hooks：

#### useRequest Hook

封装数据请求逻辑：

```tsx
// hooks/useRequest.ts
import { useState, useEffect } from 'react';
import { App } from 'antd';

interface UseRequestOptions<T> {
  manual?: boolean;          // 是否手动触发
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useRequest<T>(
  requestFn: () => Promise<T>,
  options: UseRequestOptions<T> = {}
) {
  const { message } = App.useApp();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await requestFn();
      setData(result);

      options.onSuccess?.(result);
    } catch (err) {
      const error = err as Error;
      setError(error);
      message.error(error.message);

      options.onError?.(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!options.manual) {
      execute();
    }
  }, []);

  return {
    data,
    loading,
    error,
    execute,
  };
}

// 使用
function UserList() {
  const { data: users, loading, execute } = useRequest(
    () => userService.getUsers(),
    {
      onSuccess: (data) => {
        console.log('Users loaded:', data);
      },
    }
  );

  return (
    <Table
      loading={loading}
      dataSource={users}
      columns={columns}
    />
  );
}
```

#### useTable Hook

封装表格逻辑：

```tsx
// hooks/useTable.ts
import { useState, useCallback } from 'react';
import type { TableProps } from 'antd';

interface UseTableOptions<T> {
  fetchFn: (params: any) => Promise<{ data: T[]; total: number }>;
  defaultPageSize?: number;
}

export function useTable<T extends Record<string, any>>({
  fetchFn,
  defaultPageSize = 10,
}: UseTableOptions<T>) {
  const [dataSource, setDataSource] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: defaultPageSize,
    total: 0,
  });

  const fetchData = useCallback(
    async (params: any = {}) => {
      try {
        setLoading(true);

        const { data, total } = await fetchFn({
          page: pagination.current,
          pageSize: pagination.pageSize,
          ...params,
        });

        setDataSource(data);
        setPagination((prev) => ({ ...prev, total }));
      } catch (error) {
        message.error('Failed to fetch data');
      } finally {
        setLoading(false);
      }
    },
    [fetchFn, pagination.current, pagination.pageSize]
  );

  const handleChange: TableProps<T>['onChange'] = (newPagination) => {
    setPagination({
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || defaultPageSize,
      total: pagination.total,
    });
  };

  useEffect(() => {
    fetchData();
  }, [pagination.current, pagination.pageSize]);

  return {
    dataSource,
    loading,
    pagination,
    onChange: handleChange,
    refresh: fetchData,
  };
}

// 使用
function UserTable() {
  const { dataSource, loading, pagination, onChange, refresh } = useTable({
    fetchFn: userService.getUsers,
    defaultPageSize: 20,
  });

  return (
    <Table
      loading={loading}
      dataSource={dataSource}
      columns={columns}
      pagination={pagination}
      onChange={onChange}
    />
  );
}
```

#### useForm Hook

封装表单逻辑：

```tsx
// hooks/useForm.ts
import { Form } from 'antd';
import { App } from 'antd';

interface UseFormOptions<T> {
  onSubmit: (values: T) => Promise<void>;
  onSuccess?: (values: T) => void;
  initialValues?: Partial<T>;
}

export function useForm<T extends Record<string, any>>({
  onSubmit,
  onSuccess,
  initialValues,
}: UseFormOptions<T>) {
  const [form] = Form.useForm<T>();
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: T) => {
    try {
      setLoading(true);
      await onSubmit(values);

      message.success('提交成功');
      onSuccess?.(values);

      form.resetFields();
    } catch (error) {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  return {
    form,
    loading,
    submit: handleSubmit,
  };
}

// 使用
function UserForm() {
  const { form, loading, submit } = useForm({
    onSubmit: async (values) => {
      await userService.createUser(values);
    },
    initialValues: {
      name: '',
      email: '',
    },
  });

  return (
    <Form form={form} onFinish={submit} layout="vertical">
      <Form.Item name="name" label="Name" rules={[{ required: true }]}>
        <Input />
      </Form.Item>

      <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
        <Input />
      </Form.Item>

      <Button type="primary" htmlType="submit" loading={loading}>
        Submit
      </Button>
    </Form>
  );
}
```

---

## 代码规范

### 命名规范

#### 文件命名

- **组件文件**：PascalCase（大驼峰）
  - `UserCard.tsx`
  - `DataTable.tsx`
  - `FormModal.tsx`

- **工具文件**：camelCase（小驼峰）
  - `formatUtils.ts`
  - `request.ts`
  - `validate.ts`

- **Hooks 文件**：`use` 前缀 + camelCase
  - `useRequest.ts`
  - `useTable.ts`
  - `useAuth.ts`

- **类型文件**：`types.ts` 或 `*.types.ts`
  - `user.types.ts`
  - `api.types.ts`

- **常量文件**：`constants.ts` 或 `*.constants.ts`
  - `config.constants.ts`
  - `routes.constants.ts`

#### 变量命名

```tsx
// ✅ 好的做法
const userName = 'John';              // camelCase
const isActive = true;                // Boolean: is/has 前缀
const userCount = 10;                 // Number: count/length/size
const maxItems = 100;                 // Number: max/min 前缀
const userLists: User[][] = [];       // Array: 复数形式

// ❌ 不好的做法
const user_name = 'John';             // 避免下划线命名
const active = true;                  // Boolean 缺少前缀
const data = [];                      // 命名不清晰
```

#### 组件命名

```tsx
// ✅ 好的做法
function UserCard() {}                // PascalCase
function UserProfilePage() {}         // 页面组件：Page 后缀
function UserListContainer() {}       // 容器组件：Container 后缀
function useUserList() {}             // Hook: use 前缀

// ❌ 不好的做法
function userCard() {}                // 组件应使用 PascalCase
function User() {}                    // 命名太宽泛
function getData() {}                 // 函数不是组件
```

#### 类型命名

```tsx
// ✅ 好的做法
interface User {}                     // interface: PascalCase
type UserRole = 'admin' | 'user';     // type: PascalCase
interface UserProps {}                // Props: Props 后缀
interface UserState {}                // State: State 后缀
type UserList = User[];               // Array/List/List: 复数形式

// ❌ 不好的做法
interface user {}                     // interface 应使用 PascalCase
type userRole = 'admin' | 'user';     // type 应使用 PascalCase
interface Props {}                    // 命名不清晰
```

#### 常量命名

```tsx
// ✅ 好的做法
const API_BASE_URL = 'https://api.example.com';   // UPPER_CASE
const MAX_RETRY_COUNT = 3;                        // UPPER_CASE
const DEFAULT_PAGE_SIZE = 20;                     // UPPER_CASE

// 枚举常量：使用对象
const UserRole = {
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest',
} as const;

// ❌ 不好的做法
const apiUrl = 'https://api.example.com';         // 常量应使用 UPPER_CASE
const maxRetry = 3;                               // 常量应使用 UPPER_CASE
```

### 文件组织

#### 组件文件结构

每个组件应包含以下文件（按需）：

```
UserCard/
├── index.ts                # 导出入口
├── UserCard.tsx            # 组件实现
├── UserCard.test.tsx       # 单元测试
├── UserCard.types.ts       # 类型定义（可选）
├── UserCard.styles.ts      # 样式（可选）
└── README.md               # 组件文档（可选）
```

#### index.ts 导出

统一使用 `index.ts` 导出，简化导入路径：

```tsx
// components/ui/Button/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button';

// 使用
import { Button, ButtonProps } from '@/components/ui/Button';
```

#### 组件导入顺序

```tsx
// 1. React 相关
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

// 2. 第三方库
import { Button, Form, Input } from 'antd';
import { debounce } from 'lodash';

// 3. 组件内部模块
import { UserCard } from './components/UserCard';
import { useUserList } from './hooks/useUserList';
import { UserService } from './services/user';

// 4. 类型导入
import type { User } from './types/user';
import type { ButtonProps } from 'antd';

// 5. 样式导入
import './UserPage.styles.css';
import styles from './UserPage.module.css';
```

### 导入规范

#### 路径别名

配置路径别名，避免相对路径地狱：

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/utils/*": ["src/utils/*"],
      "@/types/*": ["src/types/*"]
    }
  }
}

// vite.config.ts
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

使用路径别名：

```tsx
// ✅ 好的做法：使用路径别名
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { formatDate } from '@/utils/format';

// ❌ 不好的做法：使用相对路径
import { Button } from '../../../components/ui/Button';
import { useAuth } from '../../hooks/useAuth';
import { formatDate } from '../../../utils/format';
```

#### 按需导入

```tsx
// ✅ 好的做法：按需导入
import { Button, Input, Form } from 'antd';

// ❌ 不好的做法：导入整个库
import antd from 'antd';
```

---

## 状态管理

### 本地状态 vs 全局状态

根据状态的使用范围选择合适的状态管理方式：

#### 使用本地状态（useState）

适用于：
- 仅在单个组件内使用的状态
- UI 相关状态（loading, open, visible 等）

```tsx
function UserForm() {
  // ✅ 本地 UI 状态
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  // ✅ 表单数据（不需要跨组件共享）
  const [formValues, setFormValues] = useState({
    name: '',
    email: '',
  });

  return <Form>...</Form>;
}
```

#### 使用 Context（useContext）

适用于：
- 跨多个组件共享，但不需要复杂逻辑的状态
- 主题、语言、用户信息等全局配置

```tsx
// contexts/AuthContext.tsx
interface AuthContextValue {
  user: User | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (credentials: Credentials) => {
    const user = await authService.login(credentials);
    setUser(user);
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

#### 使用状态管理库（Zustand/Jotai/Recoil）

适用于：
- 跨多个页面/模块共享的复杂状态
- 需要状态持久化
- 需要时间旅行调试

```tsx
// stores/userStore.ts (Zustand)
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserStore {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  clearUser: () => void;
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      clearUser: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: 'user-storage',
    }
  )
);

// 使用
function UserProfile() {
  const { user, clearUser } = useUserStore();

  return (
    <div>
      <h1>{user?.name}</h1>
      <Button onClick={clearUser}>Logout</Button>
    </div>
  );
}
```

### 表单状态管理

#### 使用 Form.useForm

```tsx
function UserForm() {
  const [form] = Form.useForm<UserFormValues>();

  const handleSubmit = async (values: UserFormValues) => {
    await userService.createUser(values);
    form.resetFields();
  };

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      initialValues={{
        name: '',
        email: '',
        role: 'user',
      }}
    >
      <Form.Item name="name" label="Name" rules={[{ required: true }]}>
        <Input />
      </Form.Item>

      <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
        <Input />
      </Form.Item>

      <Button type="primary" htmlType="submit">
        Submit
      </Button>
    </Form>
  );
}
```

#### 动态表单

```tsx
function DynamicForm() {
  const [form] = Form.useForm();
  const [fields, setFields] = useState<FormField[]>([]);

  const addField = () => {
    setFields([...fields, { name: `field_${fields.length}`, label: `Field ${fields.length}` }]);
  };

  return (
    <Form form={form}>
      {fields.map((field) => (
        <Form.Item key={field.name} name={field.name} label={field.label}>
          <Input />
        </Form.Item>
      ))}

      <Button onClick={addField}>Add Field</Button>
    </Form>
  );
}
```

### 列表数据管理

#### 使用自定义 Hook

```tsx
// hooks/useList.ts
interface UseListOptions<T> {
  fetchFn: () => Promise<T[]>;
  deleteFn?: (id: string) => Promise<void>;
}

export function useList<T extends { id: string }>({ fetchFn, deleteFn }: UseListOptions<T>) {
  const [dataSource, setDataSource] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchFn();
      setDataSource(data);
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  const handleDelete = useCallback(
    async (id: string) => {
      if (!deleteFn) return;

      try {
        await deleteFn(id);
        setDataSource(dataSource.filter((item) => item.id !== id));
        message.success('删除成功');
      } catch (error) {
        message.error('删除失败');
      }
    },
    [dataSource, deleteFn]
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    dataSource,
    loading,
    refresh: fetchData,
    delete: handleDelete,
  };
}

// 使用
function UserList() {
  const { dataSource, loading, refresh, delete: handleDelete } = useList({
    fetchFn: userService.getUsers,
    deleteFn: userService.deleteUser,
  });

  return (
    <Table
      loading={loading}
      dataSource={dataSource}
      columns={columns}
      actions={{
        delete: handleDelete,
      }}
    />
  );
}
```

---

## 样式管理

### CSS-in-JS（推荐）

Ant Design 5.x 内置 CSS-in-JS，推荐使用样式对象：

```tsx
import { Button } from 'antd';
import { theme } from 'antd';

function StyledComponent() {
  const { token } = theme.useToken();

  return (
    <Button
      type="primary"
      style={{
        backgroundColor: token.colorPrimary,
        borderColor: token.colorPrimary,
        borderRadius: token.borderRadius,
        padding: `${token.paddingSM}px ${token.padding}px`,
      }}
    >
      Styled Button
    </Button>
  );
}
```

### 主题定制

#### 全局主题配置

```tsx
// App.tsx
import { ConfigProvider, theme } from 'antd';

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
          fontSize: 14,
        },
        components: {
          Button: {
            fontWeight: 500,
          },
          Input: {
            controlHeight: 40,
          },
        },
      }}
    >
      <YourApp />
    </ConfigProvider>
  );
}
```

#### 组件级主题

```tsx
import { ConfigProvider } from 'antd';

function SpecialSection() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#52c41a',
        },
      }}
    >
      <Button type="primary">Green Button</Button>
    </ConfigProvider>
  );
}
```

### 响应式设计

#### 使用 Grid 系统

```tsx
import { Row, Col } from 'antd';

function ResponsiveLayout() {
  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={8} lg={6} xl={4}>
        <Card>Content 1</Card>
      </Col>
      <Col xs={24} sm={12} md={8} lg={6} xl={4}>
        <Card>Content 2</Card>
      </Col>
    </Row>
  );
}
```

#### 使用媒体查询

```tsx
import { useBreakpoint } from 'antd';

function ResponsiveComponent() {
  const screens = useBreakpoint();

  return (
    <div>
      {screens.xs && <div>Mobile view</div>}
      {screens.md && <div>Tablet view</div>}
      {screens.lg && <div>Desktop view</div>}
    </div>
  );
}
```

---

## 错误处理

### 错误边界（Error Boundary）

```tsx
// components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Result
          status="error"
          title="Something went wrong"
          subTitle={this.state.error?.message}
          extra={
            <Button type="primary" onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          }
        />
      );
    }

    return this.props.children;
  }
}

// 使用
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

### 异常捕获

```tsx
// hooks/useRequest.ts (增强版)
import { App } from 'antd';

export function useRequest<T>(requestFn: () => Promise<T>) {
  const { message } = App.useApp();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await requestFn();
      setData(result);

      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);

      // 根据错误类型显示不同的提示
      if (error.name === 'NetworkError') {
        message.error('网络错误，请检查您的网络连接');
      } else if (error.name === 'ValidationError') {
        message.error(error.message);
      } else {
        message.error('发生未知错误，请稍后重试');
      }

      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, execute };
}
```

### 用户提示

```tsx
// 统一的错误提示
function showError(error: Error) {
  const { message } = App.useApp();

  const errorMessages: Record<string, string> = {
    NetworkError: '网络错误，请检查您的网络连接',
    ValidationError: error.message,
    UnauthorizedError: '您没有权限执行此操作',
    NotFoundError: '请求的资源不存在',
  };

  const displayMessage = errorMessages[error.name] || '发生未知错误，请稍后重试';

  message.error(displayMessage);
}
```

---

## 测试策略

### 单元测试

使用 Vitest + React Testing Library：

```tsx
// UserCard.test.tsx
import { render, screen } from '@testing-library/react';
import { UserCard } from './UserCard';

describe('UserCard', () => {
  const defaultProps = {
    name: 'John Doe',
    email: 'john@example.com',
  };

  it('should render user name and email', () => {
    render(<UserCard {...defaultProps} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('should call onEdit when Edit button is clicked', () => {
    const onEdit = vi.fn();
    render(<UserCard {...defaultProps} onEdit={onEdit} />);

    const editButton = screen.getByText('Edit');
    editButton.click();

    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it('should call onDelete when Delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<UserCard {...defaultProps} onDelete={onDelete} />);

    const deleteButton = screen.getByText('Delete');
    deleteButton.click();

    expect(onDelete).toHaveBeenCalledTimes(1);
  });
});
```

### 集成测试

```tsx
// UserForm.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserForm } from './UserForm';

describe('UserForm Integration', () => {
  it('should submit form successfully', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<UserForm onSubmit={onSubmit} />);

    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    await userEvent.type(nameInput, 'John Doe');
    await userEvent.type(emailInput, 'john@example.com');
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john@example.com',
      });
    });
  });
});
```

### E2E 测试

使用 Playwright：

```typescript
// e2e/user.spec.ts
import { test, expect } from '@playwright/test';

test('user flow', async ({ page }) => {
  await page.goto('http://localhost:3000/users');

  // 创建用户
  await page.click('button:has-text("Add User")');
  await page.fill('input[name="name"]', 'John Doe');
  await page.fill('input[name="email"]', 'john@example.com');
  await page.click('button:has-text("Submit")');

  // 验证用户创建成功
  await expect(page.locator('text=John Doe')).toBeVisible();
  await expect(page.locator('text=john@example.com')).toBeVisible();

  // 删除用户
  await page.click('button:has-text("Delete")');
  await page.click('button:has-text("Confirm")');

  // 验证用户删除成功
  await expect(page.locator('text=John Doe')).not.toBeVisible();
});
```

---

## 性能最佳实践

### 避免不必要的渲染

```tsx
// ✅ 使用 React.memo
export const UserCard = React.memo(function UserCard({ user }: { user: User }) {
  return <Card>{user.name}</Card>;
});

// ✅ 使用 useMemo
function ExpensiveComponent({ data }: { data: DataType }) {
  const processedData = useMemo(() => {
    return data.map(process);
  }, [data]);

  return <div>{/* ... */}</div>;
}

// ✅ 使用 useCallback
function ParentComponent() {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <ChildComponent onClick={handleClick} />;
}
```

### 代码分割

```tsx
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';

// 路由级别代码分割
const UserList = lazy(() => import('./pages/user/List'));
const UserDetail = lazy(() => import('./pages/user/Detail'));

function App() {
  return (
    <Suspense fallback={<Spin size="large" />}>
      <Routes>
        <Route path="/users" element={<UserList />} />
        <Route path="/users/:id" element={<UserDetail />} />
      </Routes>
    </Suspense>
  );
}
```

### 虚拟滚动

```tsx
import { List } from 'antd';

function VirtualizedList({ dataSource }: { dataSource: ItemType[] }) {
  return (
    <List
      dataSource={dataSource}
      renderItem={(item) => (
        <List.Item key={item.id}>
          <List.Item.Meta title={item.title} description={item.description} />
        </List.Item>
      )}
      pagination={{
        pageSize: 20,
      }}
    />
  );
}
```

---

## 安全最佳实践

### XSS 防护

```tsx
// ❌ 危险：直接渲染 HTML
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ 安全：使用 DOMPurify 清理
import DOMPurify from 'dompurify';

function SafeHTML({ content }: { content: string }) {
  const cleanHTML = DOMPurify.sanitize(content);
  return <div dangerouslySetInnerHTML={{ __html: cleanHTML }} />;
}
```

### CSRF 防护

```tsx
// 请求时携带 CSRF Token
import { getCSRFToken } from '@/utils/csrf';

async function secureRequest(url: string, options: RequestInit) {
  const csrfToken = getCSRFToken();

  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'X-CSRF-Token': csrfToken,
    },
  });
}
```

### 数据验证

```tsx
// 前端验证（不能替代后端验证）
const userSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  age: z.number().min(18).max(120),
});

function UserForm() {
  const handleSubmit = (values: unknown) => {
    const result = userSchema.safeParse(values);

    if (!result.success) {
      // 显示验证错误
      return;
    }

    // 提交数据
    userService.createUser(result.data);
  };
}
```

---

## 可维护性最佳实践

### DRY 原则（Don't Repeat Yourself）

```tsx
// ❌ 重复代码
function UserList() {
  return (
    <div>
      <Card style={{ marginBottom: 16, padding: 24 }}>
        <UserCard />
      </Card>
      <Card style={{ marginBottom: 16, padding: 24 }}>
        <UserCard />
      </Card>
    </div>
  );
}

// ✅ 提取复用
const cardStyle = { marginBottom: 16, padding: 24 };

function UserList() {
  return (
    <div>
      {[1, 2].map((i) => (
        <Card key={i} style={cardStyle}>
          <UserCard />
        </Card>
      ))}
    </div>
  );
}
```

### 文档化

```tsx
/**
 * 用户卡片组件
 *
 * @description 显示用户基本信息，支持编辑和删除操作
 *
 * @example
 * ```tsx
 * <UserCard
 *   name="John Doe"
 *   email="john@example.com"
 *   onEdit={() => console.log('edit')}
 *   onDelete={() => console.log('delete')}
 * />
 * ```
 */
export function UserCard({ name, email, onEdit, onDelete }: UserCardProps) {
  // ...
}
```

---

## 最佳实践对比

### 组件定义

```tsx
// ✅ 好的做法：使用函数组件 + Hooks
function UserCard({ user }: { user: User }) {
  return <Card>{user.name}</Card>;
}

// ❌ 不好的做法：使用类组件（除非必要）
class UserCard extends Component<{ user: User }> {
  render() {
    return <Card>{this.props.user.name}</Card>;
  }
}
```

### 状态更新

```tsx
// ✅ 好的做法：使用函数式更新
setCount((prev) => prev + 1);

// ❌ 不好的做法：直接使用当前值
setCount(count + 1);
```

### 依赖管理

```tsx
// ✅ 好的做法：正确声明依赖
useEffect(() => {
  fetchData(userId);
}, [userId]);

// ❌ 不好的做法：缺少依赖
useEffect(() => {
  fetchData(userId);
}, []); // eslint-disable-line react-hooks/exhaustive-deps
```

---

## 常见问题

### Q: 何时使用 useState，何时使用 useReducer?

**A**:
- **useState**：简单的独立状态（如 loading, visible）
- **useReducer**：复杂的状态逻辑，多个子值或下一个状态依赖于前一个状态

```tsx
// 简单状态：使用 useState
const [loading, setLoading] = useState(false);

// 复杂状态：使用 useReducer
const [state, dispatch] = useReducer(formReducer, initialState);
```

### Q: 如何避免组件过度渲染?

**A**:
1. 使用 `React.memo` 包装组件
2. 使用 `useMemo` 缓存计算结果
3. 使用 `useCallback` 缓存回调函数
4. 避免在 render 中创建新对象/数组

### Q: 何时使用自定义 Hook?

**A**: 当需要在多个组件间复用状态逻辑时，将其提取为自定义 Hook。

---

## 参考资源

- [Ant Design 官方文档](https://ant.design/)
- [React 官方文档](https://react.dev/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [React Testing Library](https://testing-library.com/react)

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
