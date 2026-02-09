# TypeScript 错误处理规范

## 核心原则

### ✅ 必须遵守

1. **多行处理** - 所有异常必须多行处理，记录日志
2. **统一日志格式** - 使用 `console.error('error:', error)` 统一格式
3. **明确错误类型** - 定义自定义错误类，使用类型守卫
4. **Result 类型** - 使用 Result 类型处理可能失败的操作
5. **不忽略错误** - 所有 catch 块必须处理或重新抛出错误
6. **异步错误处理** - 正确处理 Promise 和 async/await 错误

### ❌ 禁止行为

- 静默失败（空的 catch 块）
- 单行错误处理（`if (err) return err`）
- 使用 `any` 作为错误类型
- 忽略 Promise 拒绝
- 吞掉异常不记录

## Result 类型模式

### 基本 Result 类型

```typescript
// ✅ 定义 Result 类型
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

// ✅ 类型守卫
function isOk<T, E>(result: Result<T, E>): result is { ok: true; value: T } {
  return result.ok;
}

// ✅ 使用 Result 包装可能失败的操作
async function safeFetch(url: string): Promise<Response> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return { ok: true, value: response };
  } catch (error) {
    console.error('error:', error);
    return { ok: false, error: error as Error };
  }
}

// 使用示例
const result = await safeFetch('/api/users');

if (isOk(result)) {
  // TypeScript 知道这里 result.value 存在
  const data = await result.value.json();
} else {
  // TypeScript 知道这里 result.error 存在
  console.error('Failed to fetch:', result.error.message);
}
```

### 链式 Result 操作

```typescript
// ✅ 定义 map 和 flatMap
class Result<T, E = Error> {
  private constructor(
    private readonly value: T | E,
    private readonly ok: boolean,
  ) {}

  static ok<U>(value: U): Result<U, E> {
    return new Result(value, true);
  }

  static err<F>(error: F): Result<T, F> {
    return new Result(error, false);
  }

  map<U>(fn: (value: T) => U): Result<U, E> {
    return this.ok
      ? Result.ok(fn(this.value as T))
      : Result.err(this.value as E);
  }

  flatMap<U, F>(fn: (value: T) => Result<U, F>): Result<U, E | F> {
    return this.ok
      ? fn(this.value as T)
      : Result.err(this.value as E);
  }

  unwrap(): T {
    if (!this.ok) {
      throw this.value;
    }
    return this.value as T;
  }
}

// 使用示例
const result = await fetchUser('123')
  .map(user => user.profile)
  .flatMap(profile => validateProfile(profile))
  .map(valid => formatProfile(valid));
```

## 自定义错误类

### 错误层次结构

```typescript
// ✅ 基础错误类
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace?.(this, this.constructor);
  }
}

// ✅ 领域错误
export class ValidationError extends AppError {
  constructor(message: string, public readonly field?: string) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, identifier: string) {
    super(
      `${resource} with identifier '${identifier}' not found`,
      'NOT_FOUND',
      404,
    );
    this.resource = resource;
    this.identifier = identifier;
  }

  public readonly resource: string;
  public readonly identifier: string;
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super(message, 'CONFLICT', 409);
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication failed') {
    super(message, 'AUTHENTICATION_ERROR', 401);
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'Insufficient permissions') {
    super(message, 'AUTHORIZATION_ERROR', 403);
  }
}
```

### 类型守卫

```typescript
// ✅ 错误类型守卫
function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}

function isNotFoundError(error: unknown): error is NotFoundError {
  return error instanceof NotFoundError;
}

function isValidationError(error: unknown): error is ValidationError {
  return error instanceof ValidationError;
}

// 使用示例
try {
  await deleteUser(userId);
} catch (error) {
  if (isNotFoundError(error)) {
    return res.status(404).json({ error: error.message });
  }
  if (isValidationError(error)) {
    return res.status(400).json({ error: error.message, field: error.field });
  }
  if (isAppError(error)) {
    return res.status(error.statusCode).json({ error: error.message });
  }
  // 未知错误
  console.error('error:', error);
  return res.status(500).json({ error: 'Internal server error' });
}
```

## 错误处理模式

### 同步错误处理

```typescript
// ✅ 正确 - 多行处理，记录日志
function divide(a: number, b: number): number {
  if (b === 0) {
    const error = new ValidationError('Division by zero', 'b');
    console.error('error:', error);
    throw error;
  }
  return a / b;
}

// ✅ 使用 Result 类型
function safeDivide(a: number, b: number): Result<number> {
  if (b === 0) {
    return Result.err(new ValidationError('Division by zero', 'b'));
  }
  return Result.ok(a / b);
}

// ❌ 禁止 - 单行 if
function badDivide(a: number, b: number): number {
  if (b === 0) throw new Error('Division by zero');
  return a / b;
}
```

### 异步错误处理

```typescript
// ✅ 正确 - async/await 多行处理
async function getUser(id: string): Promise<User> {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      throw new NotFoundError('User', id);
    }
    const data = await response.json();
    return UserSchema.parse(data);
  } catch (error) {
    console.error('error:', error);
    throw error;
  }
}

// ✅ 使用 Result 类型
async function safeGetUser(id: string): Promise<Result<User>> {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      return Result.err(new NotFoundError('User', id));
    }
    const data = await response.json();
    const user = UserSchema.parse(data);
    return Result.ok(user);
  } catch (error) {
    console.error('error:', error);
    return Result.err(error as Error);
  }
}

// ❌ 禁止 - 忽略错误
async function badGetUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();  // 没有检查 response.ok
}
```

### Promise 错误处理

```typescript
// ✅ 正确 - Promise 链中处理错误
fetchUser(userId)
  .then(user => validateUser(user))
  .then(valid => saveUser(valid))
  .catch(error => {
    console.error('error:', error);
    // 处理错误
  });

// ✅ 使用 Promise.finally
let isLoading = true;

fetchData()
  .then(data => {
    // 处理数据
  })
  .catch(error => {
    console.error('error:', error);
  })
  .finally(() => {
    isLoading = false;
  });

// ❌ 禁止 - 没有catch的 Promise
fetchUser(userId).then(user => {
  // 如果这里抛出错误，会变成未捕获的 Promise 拒绝
  processUser(user);
});
```

### 并发错误处理

```typescript
// ✅ Promise.all - 任何一个失败都会立即拒绝
try {
  const [user, posts, comments] = await Promise.all([
    fetchUser(userId),
    fetchUserPosts(userId),
    fetchUserComments(userId),
  ]);
} catch (error) {
  console.error('error:', error);
  throw error;
}

// ✅ Promise.allSettled - 等待所有完成，无论成功或失败
const results = await Promise.allSettled([
  fetchUser(userId),
  fetchUserPosts(userId),
  fetchUserComments(userId),
]);

const successfulResults = results
  .filter((r): r is PromiseFulfilledResult<unknown> => r.status === 'fulfilled')
  .map(r => r.value);

const failedResults = results
  .filter((r): r is PromiseRejectedResult => r.status === 'rejected')
  .map(r => r.reason);

if (failedResults.length > 0) {
  console.error('Some requests failed:', failedResults);
}
```

## React 错误处理

### Error Boundary

```typescript
// ✅ 使用类组件实现 Error Boundary
interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('error:', error);
    console.error('errorInfo:', errorInfo);
    // 可以将错误日志发送到服务器
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}

// 使用
<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>
```

### 错误处理 Hook

```typescript
// ✅ 自定义错误处理 Hook
function useErrorHandler() {
  return useCallback((error: Error) => {
    console.error('error:', error);
    // 可以集成错误追踪服务
  }, []);
}

// ✅ 异步操作错误处理
function useAsync<T>(
  asyncFn: () => Promise<T>,
): { data: T | null; error: Error | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);

    asyncFn()
      .then(setData)
      .catch((err) => {
        console.error('error:', err);
        setError(err as Error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [asyncFn]);

  return { data, error, loading };
}
```

## 检查清单

提交代码前，确保：

- [ ] 所有错误都有明确的类型
- [ ] 错误处理使用多行格式
- [ ] 所有错误都记录了日志
- [ ] 没有空 catch 块（静默失败）
- [ ] 使用自定义错误类而非通用 Error
- [ ] Promise 都有 catch 处理
- [ ] async/await 都有 try-catch
- [ ] 错误类型使用类型守卫判断
- [ ] 没有使用 `any` 作为错误类型
