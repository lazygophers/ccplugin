# TypeScript 测试规范

## 核心原则

### ✅ 必须遵守

1. **使用 Vitest** - 统一测试框架
2. **测试覆盖率 > 80%** - 核心代码覆盖率要求
3. **AAA 模式** - Arrange（准备）、Act（执行）、Assert（断言）
4. **测试隔离** - 测试之间相互独立
5. **描述性命名** - 测试名称清晰描述测试内容
6. **Mock 外部依赖** - 不测试外部服务

### ❌ 禁止行为

- 测试依赖执行顺序
- 在测试中使用 sleep 等待
- 忽略测试失败
- 测试实现细节而非行为
- 过度 Mock

## Vitest 配置

### 基础配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  test: {
    // 全局配置
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],

    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.tsx',
      ],
      // 覆盖率阈值
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },

    // 包配置
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', 'build'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 测试设置

```typescript
// src/test/setup.ts
import { vi } from 'vitest';
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;
```

## 测试结构

### AAA 模式

```typescript
// ✅ 正确 - AAA 模式
describe('UserService', () => {
  it('should return user when valid ID is provided', async () => {
    // Arrange（准备）
    const userId = '123';
    const expectedUser = { id: userId, name: 'John' };
    mockUserRepository.findById.mockResolvedValue(expectedUser);

    // Act（执行）
    const result = await userService.getUserById(userId);

    // Assert（断言）
    expect(result).toEqual(expectedUser);
    expect(mockUserRepository.findById).toHaveBeenCalledWith(userId);
  });

  // ❌ 错误 - 没有 AAA 结构
  it('test user', async () => {
    const user = await userService.getUserById('123');
    expect(user).toBeDefined();
  });
});
```

### 描述性测试命名

```typescript
// ✅ 正确 - 清晰的测试名称
describe('UserService', () => {
  it('should return user when valid ID is provided', async () => { });
  it('should throw NotFoundError when user does not exist', async () => { });
  it('should throw ValidationError when ID format is invalid', async () => { });
});

// ✅ 正确 - 使用 describe 分组
describe('getUserById', () => {
  describe('when user exists', () => {
    it('should return user', async () => { });
  });

  describe('when user does not exist', () => {
    it('should throw NotFoundError', async () => { });
  });

  describe('when ID format is invalid', () => {
    it('should throw ValidationError', async () => { });
  });
});

// ❌ 错误 - 不清晰的测试名称
describe('UserService', () => {
  it('test1', async () => { });
  it('test2', async () => { });
  it('works', async () => { });
});
```

## 单元测试

### 纯函数测试

```typescript
// ✅ 正确 - 测试纯函数
import { describe, it, expect } from 'vitest';
import { calculateTotal, formatPrice } from './utils';

describe('calculateTotal', () => {
  it('should return sum of all item prices', () => {
    const items = [
      { price: 10, quantity: 2 },
      { price: 5, quantity: 1 },
    ];
    const result = calculateTotal(items);
    expect(result).toBe(25);
  });

  it('should return 0 for empty array', () => {
    const result = calculateTotal([]);
    expect(result).toBe(0);
  });
});

describe('formatPrice', () => {
  it('should format price with currency symbol', () => {
    const result = formatPrice(1234.56);
    expect(result).toBe('$1,234.56');
  });

  it('should handle zero price', () => {
    const result = formatPrice(0);
    expect(result).toBe('$0.00');
  });
});
```

### Hook 测试

```typescript
// ✅ 正确 - 测试自定义 Hook
import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useUser } from './useUser';

describe('useUser', () => {
  it('should return user data on successful fetch', async () => {
    const mockUser = { id: '123', name: 'John' };
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockUser),
      } as Response),
    );

    const { result } = renderHook(() => useUser('123'));

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  it('should return error on failed fetch', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 404,
      } as Response),
    );

    const { result } = renderHook(() => useUser('123'));

    await waitFor(() => {
      expect(result.current.user).toBeNull();
      expect(result.current.error).toBeInstanceOf(Error);
      expect(result.current.loading).toBe(false);
    });
  });
});
```

### 组件测试

```typescript
// ✅ 正确 - 测试 React 组件
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('should render children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('should call onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));

    await waitFor(() => {
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('should not call onClick when disabled', () => {
    const handleClick = vi.fn();
    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>,
    );

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });
});
```

## 集成测试

### API 集成测试

```typescript
// ✅ 正确 - API 集成测试（使用 MSW）
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { getUser } from './api';

const server = setupServer(
  http.get('/api/users/:id', ({ params }) => {
    const { id } = params;
    if (id === '123') {
      return HttpResponse.json({ id: '123', name: 'John' });
    }
    return HttpResponse.json({ error: 'Not found' }, { status: 404 });
  }),
);

beforeAll(() => server.listen());
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

describe('getUser API', () => {
  it('should return user when user exists', async () => {
    const user = await getUser('123');
    expect(user).toEqual({ id: '123', name: 'John' });
  });

  it('should throw error when user does not exist', async () => {
    await expect(getUser('999')).rejects.toThrow('Not found');
  });
});
```

## Mock 使用

### 函数 Mock

```typescript
// ✅ 正确 - Mock 函数
import { describe, it, expect, vi, afterEach } from 'vitest';
import { processData } from './utils';

afterEach(() => {
  vi.clearAllMocks();
});

describe('processData', () => {
  it('should call callback with processed data', () => {
    const callback = vi.fn();
    processData([1, 2, 3], callback);

    expect(callback).toHaveBeenCalledTimes(3);
    expect(callback).toHaveBeenNthCalledWith(1, 2); // 1 * 2
    expect(callback).toHaveBeenNthCalledWith(2, 4); // 2 * 2
    expect(callback).toHaveBeenNthCalledWith(3, 6); // 3 * 2
  });

  it('should use mock implementation', () => {
    const callback = vi.fn((x) => x * 10);
    processData([1, 2, 3], callback);

    expect(callback).toHaveBeenLastCalledWith(30);
  });
});
```

### 模块 Mock

```typescript
// ✅ 正确 - Mock 模块
import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useUser } from './useUser';

// Mock API 模块
vi.mock('@/lib/api', () => ({
  fetchUser: vi.fn(),
}));

import { fetchUser } from '@/lib/api';

describe('useUser', () => {
  it('should fetch user', async () => {
    const mockUser = { id: '123', name: 'John' };
    vi.mocked(fetchUser).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useUser('123'));

    // 等待状态更新
    await expect(result.current.user).resolves.toEqual(mockUser);
    expect(fetchUser).toHaveBeenCalledWith('123');
  });
});
```

## 异步测试

### Promise 测试

```typescript
// ✅ 正确 - 测试 Promise
import { describe, it, expect } from 'vitest';
import { fetchUser } from './api';

describe('fetchUser', () => {
  it('should resolve with user data', async () => {
    const user = await fetchUser('123');
    expect(user).toEqual({ id: '123', name: 'John' });
  });

  it('should reject with error when user not found', async () => {
    await expect(fetchUser('999')).rejects.toThrow('User not found');
  });

  it('should use resolves matcher', async () => {
    await expect(fetchUser('123')).resolves.toEqual({
      id: '123',
      name: 'John',
    });
  });

  it('should use rejects matcher', async () => {
    await expect(fetchUser('999')).rejects.toThrow('User not found');
  });
});
```

## 参数化测试

```typescript
// ✅ 正确 - 参数化测试
import { describe, it, expect } from 'vitest';
import { validateEmail } from './validators';

describe('validateEmail', () => {
  it.each([
    ['test@example.com', true],
    ['user.name@domain.co.uk', true],
    ['invalid', false],
    ['', false],
    ['@example.com', false],
    ['test@', false],
  ])('should validate "%s" as %s', (email, expected) => {
    expect(validateEmail(email)).toBe(expected);
  });

  // 或使用 describe.each
  describe.each([
    { input: 'test@example.com', expected: true },
    { input: 'invalid', expected: false },
    { input: '', expected: false },
  ])('validateEmail', ({ input, expected }) => {
    it(`should return ${expected} for "${input}"`, () => {
      expect(validateEmail(input)).toBe(expected);
    });
  });
});
```

## 检查清单

提交代码前，确保：

- [ ] 新功能有对应的单元测试
- [ ] 测试覆盖率 > 80%
- [ ] 使用 AAA 模式编写测试
- [ ] 测试名称清晰描述测试内容
- [ ] 外部依赖已 Mock
- [ ] 异步测试正确处理 Promise
- [ ] 没有使用 sleep 等待
- [ ] `pnpm test` 全部通过
