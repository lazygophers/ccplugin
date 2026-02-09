# TypeScript 命名规范

强调**清晰、一致、符合 TypeScript 生态**。

## 核心原则

### ✅ 必须遵守

1. **类型 PascalCase** - User, UserProfile, ApiResponse
2. **接口 PascalCase** - 无 I 前缀（避免 C# 风格）
3. **变量/函数 camelCase** - getUser, userName, isActive
4. **常量 UPPER_SNAKE_CASE** - MAX_RETRIES, API_BASE_URL
5. **类型参数有意义** - TEntity, TId（而非简单的 T）
6. **布尔值 is/has 前缀** - isActive, hasPermission
7. **私有成员 _ 前缀** - _internalMethod, _privateVar

### ❌ 禁止行为

- 混合命名风格（getUser、GetUser、get_user）
- 使用 I 前缀的接口（IUser、IRepository）
- 过度缩写（usr 代替 user，但 config 可以）
- 单字符类型参数（除简单场景）
- 使用相似名称（user 和 users 容易混淆）

## 类型命名

### 基本规则

```typescript
// ✅ 正确 - PascalCase
type User = {
  id: string;
  name: string;
};

type UserRole = 'admin' | 'user' | 'guest';

type ApiResponse<T> = {
  data: T;
  status: number;
};

// ❌ 错误 - 其他风格
type user = { };           // 应该是 User
type userRole = string;    // 应该是 UserRole
type API_Response = { };   // 应该是 ApiResponse
```

### 接口命名

```typescript
// ✅ 正确 - PascalCase，无 I 前缀
interface User {
  id: string;
  name: string;
}

interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
}

interface EventHandler<T> {
  (event: T): void;
}

// ❌ 错误 - C# 风格的 I 前缀
interface IUser { }              // 不要这样做
interface IUserRepository { }    // 不要这样做

// ✅ 接口扩展使用相同的类型名称
interface User {
  id: string;
  name: string;
}

interface User extends Person {
  email: string;
}

// ✅ 类型别名 vs 接口
// 使用类型别名：联合类型、映射类型、条件类型
type Status = 'pending' | 'success' | 'error';
type PartialUser = Partial<User>;

// 使用接口：对象形状、可扩展、需要 declaration merging
interface User {
  id: string;
}
interface User {
  name: string;  // declaration merging
}
```

### 泛型命名

```typescript
// ✅ 正确 - 有意义的类型参数
interface Repository<Entity, Id> {
  findById(id: Id): Promise<Entity | null>;
  save(entity: Entity): Promise<void>;
  delete(id: Id): Promise<void>;
}

interface Mapper<Input, Output> {
  map(input: Input): Output;
}

type Result<Value, ErrorType = Error> =
  | { ok: true; value: Value }
  | { ok: false; error: ErrorType };

// ✅ 简单场景可以使用单字母
type Maybe<T> = T | null;
type Either<L, R> = Left<L> | Right<R>;

// ❌ 避免 - 无意义的单字母
interface Repo<T, K> { }  // 应该使用有意义名称
```

### 枚举命名

```typescript
// ✅ 正确 - PascalCase 枚举，PascalCase 成员
enum UserRole {
  Admin = 'admin',
  User = 'user',
  Guest = 'guest',
}

enum HttpStatus {
  Ok = 200,
  NotFound = 404,
  InternalServerError = 500,
}

// ✅ 使用枚举
if (user.role === UserRole.Admin) {
  // ...
}

// ❌ 避免 - 数字枚举（除非必要）
enum Color {
  Red,    // 0
  Green,  // 1
  Blue,   // 2
}

// ✅ 推荐 - 使用 const assertion 替代数字枚举
const Color = {
  Red: 'red',
  Green: 'green',
  Blue: 'blue',
} as const;

type Color = typeof Color[keyof typeof Color];
```

## 变量和函数命名

### 基本规则

```typescript
// ✅ 正确 - camelCase
const userName = 'John';
const isActive = true;
const maxRetries = 3;

function getUserById(id: string): Promise<User> { }
function calculateTotal(items: Item[]): number { }
function isValidEmail(email: string): boolean { }

// ❌ 错误 - 其他风格
const user_name = 'John';        // 应该是 userName
const IsActive = true;           // 应该是 isActive
const MAXRETRIES = 3;            // 应该是 maxRetries（局部常量）

function GetUserById() { }       // 应该是 getUserById
function Calculate_Total() { }   // 应该是 calculateTotal
```

### 布尔函数命名

```typescript
// ✅ 正确 - is/has/can/should 前缀
function isActive(user: User): boolean { }
function hasPermission(user: User, permission: string): boolean { }
function canEdit(user: User, resource: Resource): boolean { }
function shouldRetry(error: Error): boolean { }
function isValidEmail(email: string): boolean { }

// ❌ 避免 - 不清晰的布尔函数
function active(user: User): boolean { }      // 应该是 isActive
function checkPermission(): boolean { }       // 应该是 hasPermission
function edit(): boolean { }                  // 应该是 canEdit
function valid(): boolean { }                 // 应该是 isValid
```

### 转换函数命名

```typescript
// ✅ 正确 - to/from 前缀
function toDto(user: User): UserDTO { }
function fromDto(dto: UserDTO): User { }
function toJson(value: unknown): string { }
function fromJson(json: string): unknown { }

// ✅ 正确 - parse 前缀表示解析
function parseJson(data: string): unknown { }
function parseUrl(url: string): URL { }
function parseJwt(token: string): JwtPayload { }

// ✅ 正确 - format 前缀表示格式化
function formatDate(date: Date): string { }
function formatCurrency(amount: number): string { }
```

### 事件处理函数命名

```typescript
// ✅ 正确 - handle 前缀
function handleClick(event: MouseEvent): void { }
function handleSubmit(event: FormEvent): void { }
function handleChange(value: string): void { }

// ✅ 正确 - on 前缀（用于回调 prop）
interface ButtonProps {
  onClick: (event: MouseEvent) => void;
  onSubmit: (data: FormData) => void;
}

// ❌ 避免 - 不清晰的事件处理命名
function click() { }           // 应该是 handleClick
function submit() { }          // 应该是 handleSubmit
```

## 常量命名

### 全局常量

```typescript
// ✅ 正确 - UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT = 5000;
const API_BASE_URL = 'https://api.example.com';
const CACHE_TTL_SECONDS = 3600;

// ✅ 正确 - 分组相关常量
const Config = {
  MAX_RETRIES: 3,
  DEFAULT_TIMEOUT: 5000,
  API_BASE_URL: 'https://api.example.com',
} as const;

// ✅ 正确 - 使用枚举
const LogLevel = {
  Debug: 'debug',
  Info: 'info',
  Warn: 'warn',
  Error: 'error',
} as const;

// ❌ 错误 - 其他风格
const maxRetries = 3;         // 全局常量应该用 UPPER_SNAKE_CASE
const MaxRetries = 3;         // 混合大小写
const MAXRETRIES = 3;         // 应该有下划线
```

### 局部常量

```typescript
// ✅ 局部常量可以用 camelCase
function processItems(items: Item[]) {
  const maxItems = 100;
  const defaultStatus = 'pending';

  // ...
}

// ✅ 如果是"真正的"常量，也可以用 UPPER_SNAKE_CASE
function calculateCircleArea(radius: number) {
  const PI = 3.14159;
  return PI * radius * radius;
}
```

## React 命名

### 组件命名

```typescript
// ✅ 正确 - PascalCase
function UserProfile() {
  return <div>User Profile</div>;
}

const Button: React.FC<ButtonProps> = ({ children }) => {
  return <button>{children}</button>;
};

// ✅ HOC 命名
function withAuth<P extends object>(
  Component: React.ComponentType<P>,
): React.ComponentType<P & AuthProps> {
  return function WithAuth(props: P & AuthProps) {
    // ...
  };
}

// ❌ 错误 - 组件不用 PascalCase
function userProfile() { }     // 应该是 UserProfile
const button = () => { };      // 应该是 Button
```

### Hook 命名

```typescript
// ✅ 正确 - use 前缀
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  // ...
  return user;
}

function useLocalStorage<T>(key: string, initialValue: T) {
  // ...
}

function useToggle(initialValue: boolean = false) {
  // ...
}

// ❌ 错误 - 不使用 use 前缀
function getUser() { }         // 应该是 useUser
function localStorage() { }    // 应该是 useLocalStorage
function toggle() { }          // 应该是 useToggle
```

### Context 命名

```typescript
// ✅ 正确 - Context 用 PascalCase，创建函数用 create 前缀
const UserContext = createContext<User | null>(null);

function createUserContext() {
  return createContext<UserContextValue>(null);
}

// ✅ Provider 组件命名
function UserProvider({ children }: { children: React.ReactNode }) {
  // ...
  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

// ✅ 自定义 Hook 命名
function useUserContext() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUserContext must be used within UserProvider');
  }
  return context;
}
```

## 私有成员命名

```typescript
// ✅ 正确 - 单下划线前缀表示私有
class UserService {
  private _client: HttpClient;

  constructor(client: HttpClient) {
    this._client = client;
  }

  private _validateInput(data: unknown): data is UserInput {
    // ...
  }

  public async getUser(id: string): Promise<User> {
    this._validateInput({ id });
    // ...
  }
}

// ✅ 正确 - 模块级私有函数
function _internalHelper(): void {
  // 模块内部使用
}

function publicApi(): void {
  _internalHelper();
}

// ❌ 避免 - 双下划线（名称修饰）
class BadExample {
  private __private: string;  // 不要这样做
}
```

## 特殊约定

### 回调命名

```typescript
// ✅ 正确 - on 前缀表示回调
interface EventEmitter {
  on(event: string, callback: (...args: unknown[]) => void): void;
  off(event: string, callback: (...args: unknown[]) => void): void;
  emit(event: string, ...args: unknown[]): void;
}

// ✅ Props 中的回调
interface ButtonProps {
  onClick?: (event: MouseEvent) => void;
  onSubmit?: (data: FormData) => void;
  onCancel?: () => void;
}
```

### 断言函数命名

```typescript
// ✅ 正确 - asserts 关键字
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== 'string') {
    throw new TypeError('value is not a string');
  }
}

function assertDefined<T>(value: T | null | undefined): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error('value is null or undefined');
  }
}

// 使用
function processValue(value: unknown) {
  assertIsString(value);
  // 这里 value 的类型是 string
  console.log(value.toUpperCase());
}
```

## 检查清单

提交代码前，确保：

- [ ] 类型使用 PascalCase
- [ ] 接口使用 PascalCase，无 I 前缀
- [ ] 函数使用 camelCase
- [ ] 布尔函数使用 is/has/can/should 前缀
- [ ] 常量使用 UPPER_SNAKE_CASE
- [ ] 组件使用 PascalCase
- [ ] Hook 使用 use 前缀
- [ ] 私有成员使用单下划线前缀
- [ ] 类型参数有意义（非简单场景）
- [ ] 没有使用数字枚举（使用 const assertion）
