# TypeScript 开发实践规范

## 强制规范（必须遵守）

### 工具库使用

```typescript
// ✅ 必须 - 使用 Zod 进行运行时验证
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  email: z.string().email(),
});

type User = z.infer<typeof UserSchema>;

function parseUser(data: unknown): User {
  return UserSchema.parse(data);
}

// ❌ 禁止 - 不验证直接使用类型断言
function badParse(data: unknown): User {
  return data as User;  // 运行时不安全
}
```

### 包管理（pnpm）

```bash
# ✅ 必须 - 使用 pnpm
pnpm install
pnpm add package-name
pnpm add -D package-name
pnpm run build

# ❌ 禁止 - 使用 npm 或 yarn
npm install
yarn add
```

## 错误处理

### 基本原则（强制）

```typescript
// ❌ 禁止 - 单行 if
if (err) return err;
if (error) throw error;

// ✅ 必须 - 多行处理，记录日志
try {
  const data = await fetchData();
  return data;
} catch (error) {
  console.error('error:', error);
  throw error;
}

// ✅ 使用 Result 类型处理可能失败的操作
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function safeFetch(url: string): Promise<Response> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return { ok: true, value: response };
  } catch (error) {
    console.error('error:', error);
    return { ok: false, error: error as Error };
  }
}
```

### 错误类型判断

```typescript
// ✅ 使用 instanceof 判断错误类型
try {
  await operation();
} catch (error) {
  if (error instanceof TypeError) {
    console.error('Type error:', error);
  } else if (error instanceof Error) {
    console.error('General error:', error);
  } else {
    // unknown 类型需要特殊处理
    console.error('Unknown error:', error);
  }
}

// ❌ 避免 - 使用类型断言绕过检查
try {
  await operation();
} catch (error: unknown) {
  throw (error as Error);  // 不安全的断言
}
```

## 命名规范

### 核心约定

```typescript
// ✅ 类型使用 PascalCase
type User = { id: string; name: string };
type UserRole = 'admin' | 'user' | 'guest';
interface ApiResponse<T> {
  data: T;
  status: number;
}

// ✅ 接口使用 PascalCase（无 I 前缀）
interface User {
  id: string;
  name: string;
}

// ❌ 避免 - C# 风格的 I 前缀
interface IUser { }  // 不要这样做
interface IUserRepository { }

// ✅ 类型参数使用有意义的名称
interface Repository<Entity, Id> {
  findById(id: Id): Promise<Entity | null>;
  save(entity: Entity): Promise<void>;
}

// ❌ 避免 - 单字母类型参数（除简单场景）
interface Repository<T, K> { }  // 不清晰
```

### 变量和函数命名

```typescript
// ✅ 函数使用 camelCase，动词开头
function getUserById(id: string): Promise<User | null> { }
function calculateTotal(items: Item[]): number { }
function isValidEmail(email: string): boolean { }

// ✅ 布尔返回值使用 is/has/can 前缀
function isActive(user: User): boolean { }
function hasPermission(user: User, permission: string): boolean { }
function canEdit(user: User, resource: Resource): boolean { }

// ✅ 常量使用 UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT = 5000;
const API_BASE_URL = 'https://api.example.com';

// ✅ 枚举使用 PascalCase
enum UserRole {
  Admin = 'admin',
  User = 'user',
  Guest = 'guest',
}

// ❌ 避免 - 混合命名风格
function GetUser() { }  // 应该是 getUser
const Max_Retries = 3;  // 应该是 MAX_RETRIES
```

### React 组件命名

```typescript
// ✅ 组件使用 PascalCase
function UserProfile() {
  return <div>User Profile</div>;
}

const Button: React.FC<ButtonProps> = ({ children, onClick }) => {
  return <button onClick={onClick}>{children}</button>;
};

// ✅ 自定义 Hook 使用 use 前缀
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  // ...
  return user;
}

function useLocalStorage<T>(key: string, initialValue: T) {
  // ...
}

// ❌ 避免 - 组件不使用 PascalCase
function userProfile() { }  // 应该是 UserProfile
const button = () => { };  // 应该是 Button
```

## 类型安全

### Strict 模式配置

```json
// tsconfig.json - 必须启用的选项
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

### 类型守卫

```typescript
// ✅ 定义类型守卫
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value
  );
}

// 使用类型守卫
function processValue(value: unknown) {
  if (isString(value)) {
    // 这里 value 的类型是 string
    console.log(value.toUpperCase());
  } else if (isUser(value)) {
    // 这里 value 的类型是 User
    console.log(value.name);
  }
}
```

### 避免类型断言

```typescript
// ❌ 避免 - 类型断言
function badExample(data: unknown): User {
  return data as User;  // 运行时不验证
}

// ✅ 推荐 - 类型守卫或 Zod 验证
function goodExample(data: unknown): User | null {
  if (isUser(data)) {
    return data;
  }
  return null;
}

// ✅ 或使用 Zod
function zodExample(data: unknown): User {
  return UserSchema.parse(data);
}
```

### Discriminated Union

```typescript
// ✅ 使用 Discriminated Union 处理不同状态
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function renderState<T>(state: AsyncState<T>) {
  switch (state.status) {
    case 'idle':
      return 'Ready to load';
    case 'loading':
      return 'Loading...';
    case 'success':
      return `Data: ${state.data}`;  // TypeScript 知道这里有 data
    case 'error':
      return `Error: ${state.error.message}`;  // TypeScript 知道这里有 error
  }
}
```

## 性能优化

### 避免不必要的重新渲染

```typescript
// ✅ 使用 React.memo 避免不必要的重新渲染
const ExpensiveComponent = React.memo(({ data }: { data: Data[] }) => {
  return <div>{data.map(...)}</div>;
});

// ✅ 使用 useCallback 稳定函数引用
const handleClick = useCallback(() => {
  doSomething(dependency);
}, [dependency]);

// ✅ 使用 useMemo 缓存计算结果
const filteredData = useMemo(() => {
  return data.filter(item => item.active);
}, [data]);
```

### 懒加载

```typescript
// ✅ 使用动态导入进行代码分割
const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  );
}
```

### 避免内存泄漏

```typescript
// ✅ 正确 - 清理副作用
useEffect(() => {
  const subscription = subscribe();
  return () => {
    subscription.unsubscribe();  // 清理
  };
}, []);

// ✅ 正确 - 清理定时器
useEffect(() => {
  const timer = setInterval(() => {
    console.log('Tick');
  }, 1000);
  return () => {
    clearInterval(timer);  // 清理
  };
}, []);
```

## 检查清单

提交代码前，确保：

- [ ] 使用 pnpm 作为包管理器
- [ ] tsconfig.json 启用了 strict 模式
- [ ] 使用 Zod 进行运行时类型验证
- [ ] 没有使用 `any` 类型（使用 `unknown` 代替）
- [ ] 错误处理使用多行格式，记录了日志
- [ ] 类型使用 PascalCase
- [ ] 函数使用 camelCase
- [ ] 常量使用 UPPER_SNAKE_CASE
- [ ] 没有使用 `I` 前缀的接口
- [ ] 没有使用 `@ts-ignore` 绕过类型检查
- [ ] 使用类型守卫而非类型断言
- [ ] React 组件使用 PascalCase
- [ ] 自定义 Hook 使用 use 前缀
