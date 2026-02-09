// TypeScript 代码对比示例（正确 vs 错误）

// ========== 类型定义 ==========

// ✅ 正确: 使用有意义的类型参数
interface Repository<Entity, Id> {
  findById(id: Id): Promise<Entity | null>;
  save(entity: Entity): Promise<void>;
}

// ❌ 错误: 使用单字母类型参数
interface Repo<T, K> { }

// ✅ 正确: 使用 Discriminated Union
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function handle<T>(result: Result<T>) {
  if (result.ok) {
    console.log(result.value);
  } else {
    console.error(result.error);
  }
}

// ❌ 错误: 简单 Union 无法区分类型
type ResultBad<T> = T | Error;

function handleBad<T>(result: ResultBad<T>) {
  // 无法安全地访问 value 或 error
}

// ========== 命名规范 ==========

// ✅ 正确: 类型使用 PascalCase
type UserDTO = { id: string; name: string };
type UserRole = 'admin' | 'user' | 'guest';

// ✅ 正确: 接口使用 PascalCase（无 I 前缀）
interface ApiResponse<T> {
  data: T;
  status: number;
}

// ❌ 错误: 使用 I 前缀
interface IUserDTO { }  // C# 风格，在 TypeScript 中不推荐

// ❌ 错误: 类型使用 camelCase
type userDTO = { };

// ✅ 正确: 函数使用 camelCase
function getUserById(id: string): Promise<User> { }
function calculateTotal(items: Item[]): number { }
function isValidEmail(email: string): boolean { }

// ❌ 错误: 函数使用 PascalCase
function GetUserById() { }  // 应该是 camelCase

// ✅ 正确: 布尔函数使用 is/has 前缀
function isActive(user: User): boolean { }
function hasPermission(user: User, perm: string): boolean { }
function canEdit(user: User, resource: Resource): boolean { }

// ❌ 错误: 不清晰的布尔函数
function active(user: User): boolean { }  // 应该是 isActive

// ========== 错误处理 ==========

// ✅ 正确: 多行错误处理
async function fetchData(id: string) {
  try {
    const response = await fetch(`/api/data/${id}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('error:', error);
    throw error;
  }
}

// ❌ 错误: 单行错误处理
async function fetchDataBad(id: string) {
  try {
    return await fetch(`/api/data/${id}`);
  } catch (err) {
    if (err) return err;  // 禁止单行 if
  }
}

// ✅ 正确: 使用 Result 类型
async function safeFetch(id: string): Promise<Result<Data>> {
  try {
    const data = await fetchData(id);
    return { ok: true, value: data };
  } catch (error) {
    console.error('error:', error);
    return { ok: false, error: error as Error };
  }
}

// ========== 类型安全 ==========

// ✅ 正确: 使用类型守卫
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function processValue(value: unknown) {
  if (isString(value)) {
    // TypeScript 知道这里 value 是 string
    return value.toUpperCase();
  }
  return String(value);
}

// ❌ 错误: 使用类型断言
function processValueBad(value: unknown) {
  return (value as string).toUpperCase();  // 运行时不安全
}

// ✅ 正确: 使用 Zod 运行时验证
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  email: z.string().email(),
});

function parseUser(data: unknown): User {
  return UserSchema.parse(data);
}

// ❌ 错误: 不验证直接使用
function parseUserBad(data: unknown): User {
  return data as User;  // 运行时不验证
}

// ========== React Hooks ==========

// ✅ 正确: useEffect 依赖数组完整
useEffect(() => {
  const subscription = subscribe(userId);
  return () => subscription.unsubscribe();
}, [userId]);

// ❌ 错误: 缺少依赖
useEffect(() => {
  subscribe(userId);  // userId 应该在依赖数组中
}, []);  // 缺少 userId

// ✅ 正确: useCallback 缓存回调
const handleClick = useCallback(() => {
  console.log('Clicked', userId);
}, [userId]);

// ❌ 错误: 不使用 useCallback（每次渲染都创建新函数）
function Component() {
  return <Child onClick={() => console.log('Clicked')} />;
}

// ========== 异步处理 ==========

// ✅ 正确: 并发处理
async function fetchAllData(userId: string) {
  const [user, posts, comments] = await Promise.all([
    fetchUser(userId),
    fetchPosts(userId),
    fetchComments(userId),
  ]);
  return { user, posts, comments };
}

// ❌ 错误: 串行等待（可以并行时）
async function fetchAllDataBad(userId: string) {
  const user = await fetchUser(userId);
  const posts = await fetchPosts(userId);  // 不必要地等待
  const comments = await fetchComments(userId);  // 不必要地等待
  return { user, posts, comments };
}

// ✅ 正确: 处理 Promise.allSettled
async function fetchAllWithErrors() {
  const results = await Promise.allSettled([
    fetchUser('1'),
    fetchUser('2'),
    fetchUser('3'),
  ]);

  const successful = results
    .filter((r): r is PromiseFulfilledResult<User> => r.status === 'fulfilled')
    .map(r => r.value);

  const failed = results
    .filter((r): r is PromiseRejectedResult => r.status === 'rejected')
    .map(r => r.reason);

  return { successful, failed };
}

// ========== 常量定义 ==========

// ✅ 正确: 全局常量使用 UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT = 5000;
const API_BASE_URL = 'https://api.example.com';

// ❌ 错误: 全局常量使用其他格式
const maxRetries = 3;  // 应该是 UPPER_SNAKE_CASE
const MaxRetries = 3;  // 混合大小写

// ✅ 正确: 局部常量可以用 camelCase
function processData(items: Item[]) {
  const maxItems = 100;  // 局部常量可以用 camelCase
  // ...
}

// ========== 泛型使用 ==========

// ✅ 正确: 有意义的泛型参数
function identity<T>(value: T): T {
  return value;
}

function first<T>(items: T[]): T | undefined {
  return items[0];
}

// ❌ 错误: 过度使用泛型
function identityBad<T>(value: T): T {
  return value;  // 对于简单情况，不需要泛型
}

// ========== 条件类型 ==========

// ✅ 正确: 条件类型
type NonNullable<T> = T extends null | undefined ? never : T;

type Flatten<T> = T extends Array<infer U> ? U : T;

// 使用
type T1 = NonNullable<string | null>;  // string
type T2 = Flatten<number[]>;  // number

// ========== 映射类型 ==========

// ✅ 正确: 映射类型
type ReadonlyUser = Readonly<User>;
type PartialUser = Partial<User>;
type UserKeys = keyof User;

// ✅ 高级映射类型
type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// ========== 工具类型使用 ==========

// ✅ 正确: 使用内置工具类型
type UserUpdate = Partial<Omit<User, 'id'>>;
type UserWithTimestamps = User & { createdAt: Date; updatedAt: Date };

// 提取函数返回类型
type FetchUserReturn = Awaited<ReturnType<typeof fetchUser>>;

// ========== 类型推断 ==========

// ✅ 正确: 使用 infer 推断类型
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;

type ExtractReturnType<T extends (...args: any[]) => any> = T extends (...args: any[]) => infer R ? R : any;

// ========== 模板字面量类型 ==========

// ✅ 正确: 模板字面量
type EventName<T extends string> = `on${Capitalize<T>}`;

type ButtonEvents = EventName<'click'> | EventName<'hover'>;

// ========== 类型守卫 ==========

// ✅ 正确: 类型守卫
function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

const items: (string | undefined)[] = ['a', 'b', undefined, 'c'];
const definedItems = items.filter(isDefined);  // string[]

// ✅ 谓词类型守卫
function isUser(data: unknown): data is User {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'name' in data &&
    'email' in data
  );
}
