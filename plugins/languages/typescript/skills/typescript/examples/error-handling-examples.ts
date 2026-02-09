// TypeScript 错误处理示例

// Result 类型定义
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function isOk<T, E>(result: Result<T, E>): result is { ok: true; value: T } {
  return result.ok;
}

// ========== 正确示例 ==========

// 示例 1: 使用 Result 类型处理可能失败的操作
async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const response = await fetch(`/api/users/${id}`);

    if (!response.ok) {
      if (response.status === 404) {
        return {
          ok: false,
          error: new Error(`User not found: ${id}`),
        };
      }
      return {
        ok: false,
        error: new Error(`HTTP ${response.status}: ${response.statusText}`),
      };
    }

    const data = await response.json();
    const user = UserSchema.parse(data);

    return { ok: true, value: user };
  } catch (error) {
    console.error('error:', error);
    return { ok: false, error: error as Error };
  }
}

// 示例 2: 使用 Result 的代码
async function displayUser(id: string) {
  const result = await fetchUser(id);

  if (isOk(result)) {
    // TypeScript 知道这里 result.value 存在
    console.log(`User: ${result.value.name}`);
  } else {
    // TypeScript 知道这里 result.error 存在
    console.error(`Error: ${result.error.message}`);
    // 可以尝试从缓存加载
    const cached = loadFromCache(id);
    if (cached) {
      console.log(`Cached user: ${cached.name}`);
    }
  }
}

// 示例 3: 链式 Result 操作
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

  unwrapOr(defaultValue: T): T {
    return this.ok ? (this.value as T) : defaultValue;
  }
}

// 使用链式操作
const result = await fetchUser('123')
  .map(user => user.profile)
  .flatMap(profile => validateProfile(profile))
  .map(valid => formatProfile(valid));

if (isOk(result)) {
  console.log(result.value);
}

// 示例 4: 自定义错误类
class AppError extends Error {
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

class NotFoundError extends AppError {
  constructor(resource: string, identifier: string) {
    super(
      `${resource} with identifier '${identifier}' not found`,
      'NOT_FOUND',
      404,
    );
  }
}

class ValidationError extends AppError {
  constructor(message: string, public readonly field?: string) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}

// 示例 5: 类型守卫
function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}

function isNotFoundError(error: unknown): error is NotFoundError {
  return error instanceof NotFoundError;
}

function handleError(error: unknown) {
  if (isNotFoundError(error)) {
    console.error('Not found:', error.message);
    return { status: 404, message: error.message };
  }

  if (isAppError(error)) {
    console.error('App error:', error.code, error.message);
    return { status: error.statusCode, message: error.message };
  }

  console.error('Unknown error:', error);
  return { status: 500, message: 'Internal server error' };
}

// ========== 错误示例 ==========

// ❌ 错误 1: 单行错误处理
function badFetch(id: string) {
  try {
    return fetch(`/api/users/${id}`);
  } catch (err) {
    if (err) return err;  // 禁止：单行 if
  }
}

// ❌ 错误 2: 不处理错误
async function badFetch2(id: string) {
  const response = await fetch(`/api/users/${id}`);
  return response.json();  // 没有检查 response.ok
}

// ❌ 错误 3: 使用 any 作为错误类型
function badHandle(error: any) {  // 禁止：any 类型
  console.error(error.message);  // 可能不存在
}

// ❌ 错误 4: 类型断言绕过检查
function badParse(data: unknown): User {
  return data as User;  // 运行时不验证
}

// ❌ 错误 5: 静默失败
async function badFetch3(id: string) {
  try {
    return await fetch(`/api/users/${id}`);
  } catch (error) {
    // 静默失败，不记录日志
  }
}
