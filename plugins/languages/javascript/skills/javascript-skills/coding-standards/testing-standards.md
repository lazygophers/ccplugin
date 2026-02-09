# JavaScript 测试规范

## 测试框架

### Vitest 配置

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.config.js',
        '**/*.d.ts',
      ],
    },
  },
});
```

### Jest 配置

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: ['**/*.test.{js,jsx}'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/**/*.d.ts',
    '!src/**/index.js',
  ],
};
```

## 测试结构

### 目录组织

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.jsx
│   │   ├── Button.css
│   │   └── Button.test.jsx    # 组件测试
│   │
│   └── UserCard/
│       ├── UserCard.jsx
│       └── UserCard.test.jsx
│
├── hooks/
│   ├── useAuth/
│   │   ├── useAuth.js
│   │   └── useAuth.test.js    # Hook 测试
│   │
│   └── useLocalStorage/
│       ├── useLocalStorage.js
│       └── useLocalStorage.test.js
│
├── services/
│   ├── api/
│   │   ├── api.js
│   │   └── api.test.js        # 服务测试
│   │
│   └── user/
│       ├── user.js
│       └── user.test.js
│
└── test/
    ├── setup.js               # 测试配置
    └── mocks/                  # Mock 文件
```

## 测试配置

### setup.js

```javascript
// src/test/setup.js
import { cleanup } from '@testing-library/react';
import { beforeAll, afterAll, afterEach, vi } from 'vitest';

// 每个测试后清理
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.resetAllMocks();
});

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

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
  removeItem: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});
```

## 单元测试

### 函数测试

```javascript
// utils/calculateTotal.test.js
import { describe, it, expect } from 'vitest';
import { calculateTotal, formatCurrency } from '../calculateTotal';

describe('calculateTotal', () => {
  it('calculates total with tax', () => {
    const result = calculateTotal(100, 0.1);
    expect(result).toBe(110);
  });

  it('handles zero price', () => {
    const result = calculateTotal(0, 0.1);
    expect(result).toBe(0);
  });

  it('handles different tax rates', () => {
    expect(calculateTotal(100, 0.05)).toBe(105);
    expect(calculateTotal(100, 0.2)).toBe(120);
    expect(calculateTotal(100, 0)).toBe(100);
  });
});

describe('formatCurrency', () => {
  it('formats USD correctly', () => {
    expect(formatCurrency(100, 'USD')).toBe('$100.00');
  });

  it('formats EUR correctly', () => {
    expect(formatCurrency(100, 'EUR')).toBe('100.00 EUR');
  });

  it('handles zero', () => {
    expect(formatCurrency(0, 'USD')).toBe('$0.00');
  });
});
```

### 异步函数测试

```javascript
// services/api.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchUser, fetchUsers } from '../api';

describe('api service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchUser', () => {
    it('fetches user successfully', async () => {
      const mockUser = { id: 1, name: 'John' };
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockUser,
      });

      const result = await fetchUser(1);

      expect(fetch).toHaveBeenCalledWith('/api/users/1');
      expect(result).toEqual(mockUser);
    });

    it('throws error on failed request', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
      });

      await expect(fetchUser(999)).rejects.toThrow('User not found');
    });
  });

  describe('fetchUsers', () => {
    it('fetches all users', async () => {
      const mockUsers = [
        { id: 1, name: 'John' },
        { id: 2, name: 'Jane' },
      ];
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockUsers,
      });

      const result = await fetchUsers();

      expect(result).toEqual(mockUsers);
      expect(fetch).toHaveBeenCalledWith('/api/users');
    });
  });
});
```

## 组件测试

### React 组件测试

```javascript
// components/Button/Button.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button';

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('renders with variant classes', () => {
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn-primary');
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is set', () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);

    expect(screen.getByRole('button')).toBeDisabled();

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('shows loading state', () => {
    render(<Button loading>Submit</Button>);
    expect(screen.getByRole('button')).toHaveTextContent(/loading/i);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### 用户交互测试

```javascript
// components/Input/Input.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Input from '../Input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Username" />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
  });

  it('calls onChange when value changes', () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'new value' },
    });

    expect(handleChange).toHaveBeenCalledWith('new value');
  });

  it('shows error message when error prop is set', () => {
    render(<Input error="Required field" />);
    expect(screen.getByText('Required field')).toHaveClass('error-message');
  });

  it('is disabled when disabled prop is set', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });
});
```

## Hook 测试

### 自定义 Hook 测试

```javascript
// hooks/useCounter/useCounter.test.js
import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCounter } from '../useCounter';

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it('initializes with custom value', () => {
    const { result } = renderHook(() => useCounter(10));
    expect(result.current.count).toBe(10);
  });

  it('increments count', () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it('decrements count', () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.decrement();
    });

    expect(result.current.count).toBe(4);
  });

  it('resets count', () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.reset();
    });

    expect(result.current.count).toBe(0);
  });
});
```

### 异步 Hook 测试

```javascript
// hooks/useUser/useUser.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useUser } from '../useUser';

describe('useUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches user data', async () => {
    const mockUser = { id: 1, name: 'John' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });

    const { result } = renderHook(() => useUser(1));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
    });

    const { result } = renderHook(() => useUser(999));

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
      expect(result.current.loading).toBe(false);
    });
  });
});
```

## 集成测试

### API 集成测试

```javascript
// integration/api.integration.test.js
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';

describe('User API Integration', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  it('fetches user with mocked API', async () => {
    const mockUser = { id: 1, name: 'John' };

    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.json(mockUser);
      })
    );

    const user = await fetchUser(1);
    expect(user).toEqual(mockUser);
  });

  it('handles API error', async () => {
    server.use(
      http.get('/api/users/:id', () => {
        return HttpResponse.json({ error: 'Not found' }, { status: 404 });
      })
    );

    await expect(fetchUser(999)).rejects.toThrow();
  });
});
```

## Mock 和 Stub

### Mock 函数

```javascript
// 使用 vi.fn()
import { describe, it, expect, vi } from 'vitest';

describe('mock examples', () => {
  it('mocks a function', () => {
    const myFunc = vi.fn().mockReturnValue('mocked');

    const result = myFunc();

    expect(result).toBe('mocked');
    expect(myFunc).toHaveBeenCalledTimes(1);
    expect(myFunc).toHaveBeenCalledWith();
  });

  it('mocks with implementation', () => {
    const myFunc = vi.fn((x, y) => x + y);

    const result = myFunc(2, 3);

    expect(result).toBe(5);
  });

  it('mocks return values sequence', () => {
    const myFunc = vi.fn()
      .mockReturnValueOnce('first')
      .mockReturnValueOnce('second')
      .mockReturnValue('default');

    expect(myFunc()).toBe('first');
    expect(myFunc()).toBe('second');
    expect(myFunc()).toBe('default');
  });
});
```

### Mock 模块

```javascript
// utils/__mocks__/api.js
export const fetchUser = vi.fn().mockResolvedValue({
  id: 1,
  name: 'Mocked User',
});

// 测试中使用
vi.mock('../utils/api', () => ({
  fetchUser: vi.fn().mockResolvedValue({
    id: 1,
    name: 'Mocked User',
  }),
}));
```

## 测试覆盖率

### 目标

| 指标 | 最低要求 | 推荐 |
|------|---------|------|
| 语句覆盖 | 70% | 80% |
| 分支覆盖 | 60% | 75% |
| 函数覆盖 | 70% | 80% |
| 关键路径 | 100% | 100% |

### 运行测试

```bash
# 运行所有测试
pnpm run test

# 运行测试并生成覆盖率
pnpm run test:coverage

# 监听模式（开发时）
pnpm run test:watch

# 运行单个文件
pnpm run test Button.test.jsx

# 运行匹配的文件
pnpm run test --testNamePattern="increments"
```

## 测试最佳实践

### AAA 模式

```javascript
it('calculates total correctly', () => {
  // Arrange
  const price = 100;
  const tax = 0.1;
  const expected = 110;

  // Act
  const result = calculateTotal(price, tax);

  // Assert
  expect(result).toBe(expected);
});
```

### 测试替身（Test Doubles）

```javascript
// Mock - 模拟对象行为
const mockFetch = vi.fn().mockResolvedValue({ data: 'test' });

// Stub - 提供固定返回值
const stubFetch = vi.fn().mockReturnValue({ users: [] });

// Spy - 包装真实函数
const originalFetch = global.fetch;
global.fetch = vi.spyOn(global, 'fetch');

// Fake - 提供简化实现
const fakeDelay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
```

## 快速检查清单

- [ ] 所有函数有单元测试
- [ ] 关键组件有集成测试
- [ ] API 调用被正确 Mock
- [ ] 错误场景被测试
- [ ] 边缘情况被覆盖
- [ ] 测试描述清晰
- [ ] 测试独立运行
- [ ] 测试快速执行
- [ ] 覆盖率达标

## 常见反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| 测试实现细节 | 重构导致测试失败 | 测试行为，而非实现 |
| 过度 Mock | 集成测试缺失 | 使用真实依赖做集成测试 |
| 断言过多 | 难以调试 | 每个测试一个主要断言 |
| 测试不独立 | 互相影响 | 每个测试重置状态 |
| 忽略异步 | 竞态条件 | 使用 waitFor/async utilities |
