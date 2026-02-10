---
name: antd-testing-skills
description: Ant Design 测试完整指南 - Jest、React Testing Library、组件测试、E2E测试
---

# antd-testing: Ant Design 测试完整指南

Ant Design 组件测试模块，提供基于 Jest、React Testing Library、Cypress、Playwright 的完整测试方案，涵盖单元测试、集成测试、E2E 测试的最佳实践。

---

## 概述

### 测试重要性

Ant Design 组件测试是确保 UI 质量、可维护性和用户体验的关键手段。完善的测试体系可以帮助：

- **防止回归**: 捕捉代码修改导致的功能破坏
- **文档作用**: 测试即文档，展示组件预期行为
- **重构信心**: 安全地重构代码而不破坏功能
- **提高质量**: 早期发现 bug，降低修复成本

### 测试策略

Ant Design 组件测试采用**测试金字塔**策略：

```
         /\
        /  \      E2E Tests (10%)
       /----\     关键用户流程
      /------\
     /        \   Integration Tests (30%)
    /----------\  组件交互测试
   /            \
  /--------------\ Unit Tests (60%)
 /                \ 组件单元测试
```

- **单元测试 (60%)**: 测试单个组件的行为和状态
- **集成测试 (30%)**: 测试多个组件的交互和数据流
- **E2E 测试 (10%)**: 测试完整的用户流程

### 测试工具栈

| 工具 | 用途 | 版本要求 |
|------|------|---------|
| **Jest** | 测试运行器、断言库 | >= 29.0 |
| **React Testing Library** | 组件渲染、交互测试 | >= 14.0 |
| **@testing-library/user-event** | 用户交互模拟 | >= 14.0 |
| **Cypress** | E2E 测试框架 | >= 13.0 |
| **Playwright** | E2E 测试框架 | >= 1.40 |
| **msw (Mock Service Worker)** | API Mock | >= 2.0 |
| **@faker-js/faker** | 测试数据生成 | >= 8.0 |

---

## 核心特性

- **完整测试覆盖**: 单元测试、集成测试、E2E 测试
- **Ant Design 组件适配**: 针对 antd 组件的专用测试工具
- **快照测试**: 组件 UI 快照和回归检测
- **Mock 方案**: API、组件、Hook 的完整 Mock 策略
- **异步测试**: Promise、Timer、异步组件的测试方法
- **性能测试**: 组件渲染性能测试
- **可访问性测试**: ARIA、键盘导航测试
- **覆盖率配置**: Jest 覆盖率报告和阈值配置

---

## 测试环境配置

### Jest 配置

#### 基础配置

**jest.config.js**:
```javascript
module.exports = {
  // 测试环境
  testEnvironment: 'jsdom',

  // 测试文件匹配
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],

  // 模块路径映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },

  // 转换配置
  transform: {
    '^.+\\.(ts|tsx|js|jsx)$': ['@swc/jest', {
      jsc: {
        transform: {
          react: {
            runtime: 'automatic',
          },
        },
      },
    }],
  },

  // Setup 文件
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],

  // 覆盖率配置
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
    '!src/main.tsx',
  ],

  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },

  // 模块文件扩展名
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
};
```

#### Setup 文件

**src/setupTests.ts**:
```typescript
import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { TextEncoder, TextDecoder } from 'util';

// React Testing Library 配置
configure({
  asyncUtilTimeout: 5000, // 异步工具超时时间
});

// Polyfill for TextEncoder/TextDecoder
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
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

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;
```

### React Testing Library 配置

#### 自定义 Render 函数

**src/test-utils.tsx**:
```typescript
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// Ant Design 全局配置
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ConfigProvider locale={zhCN}>
      {children}
    </ConfigProvider>
  );
};

// 自定义 render 函数
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// 重新导出所有测试工具
export * from '@testing-library/react';
export { customRender as render };
```

### 测试脚本配置

**package.json**:
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2",
    "test:debug": "node --inspect-brk node_modules/.bin/jest --runInBand"
  }
}
```

### TypeScript 类型定义

**src/global.d.ts**:
```typescript
// Jest 类型扩展
declare namespace jest {
  interface Matchers<R> {
    toHaveStyle(css: object): R;
    toBeDisabled(): R;
    toBeEmpty(): R;
  }
}

// Mock 文件类型声明
declare module '*.svg' {
  const content: React.FC<React.SVGProps<SVGSVGElement>>;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.css' {
  const classes: { [key: string]: string };
  export default classes;
}
```

---

## 组件测试

### Button 组件测试

#### 基础测试

```typescript
import { render, screen, fireEvent } from '@/test-utils';
import { Button } from 'antd';

describe('Button Component', () => {
  it('should render button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('should call onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should not call onClick when button is disabled', () => {
    const handleClick = jest.fn();
    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>
    );

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('should apply primary type styles', () => {
    render(<Button type="primary">Primary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('ant-btn-primary');
  });

  it('should show loading spinner', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('ant-btn-loading');
    expect(button).toBeDisabled();
  });

  it('should render icon', () => {
    const { container } = render(
      <Button icon={<span data-testid="icon">Icon</span>}>
        With Icon
      </Button>
    );
    expect(container.querySelector('[data-testid="icon"]')).toBeInTheDocument();
  });
});
```

### Input 组件测试

```typescript
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Input } from 'antd';

describe('Input Component', () => {
  it('should render input field', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('should update value on user input', async () => {
    const user = userEvent.setup();
    render(<Input />);

    const input = screen.getByRole('textbox');
    await user.type(input, 'Hello World');

    expect(input).toHaveValue('Hello World');
  });

  it('should call onChange when value changes', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<Input onChange={handleChange} />);

    const input = screen.getByRole('textbox');
    await user.type(input, 'test');

    expect(handleChange).toHaveBeenCalled();
  });

  it('should render password input', () => {
    render(<Input.Password />);
    const input = screen.getByPlaceholderText('input password');
    expect(input).toHaveAttribute('type', 'password');
  });

  it('should toggle password visibility', async () => {
    const user = userEvent.setup();
    render(<Input.Password />);

    const input = screen.getByPlaceholderText('input password');
    const toggleButton = screen.getByRole('button');

    // 初始状态：password
    expect(input).toHaveAttribute('type', 'password');

    // 点击切换按钮
    await user.click(toggleButton);
    expect(input).toHaveAttribute('type', 'text');

    // 再次点击
    await user.click(toggleButton);
    expect(input).toHaveAttribute('type', 'password');
  });

  it('should render search input with button', () => {
    const onSearch = jest.fn();
    render(<Input.Search placeholder="Search..." onSearch={onSearch} />);

    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should call onSearch when search button clicked', async () => {
    const user = userEvent.setup();
    const onSearch = jest.fn();
    render(<Input.Search onSearch={onSearch} />);

    const searchButton = screen.getByRole('button');
    await user.click(searchButton);

    expect(onSearch).toHaveBeenCalledWith('');
  });
});
```

### Select 组件测试

```typescript
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Select } from 'antd';

const options = [
  { label: 'Apple', value: 'apple' },
  { label: 'Banana', value: 'banana' },
  { label: 'Orange', value: 'orange' },
];

describe('Select Component', () => {
  it('should render select component', () => {
    render(<Select options={options} placeholder="Select fruit" />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('should open dropdown on click', async () => {
    const user = userEvent.setup();
    render(<Select options={options} open />);

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });
  });

  it('should select option', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(
      <Select options={options} onChange={handleChange} placeholder="Select" />
    );

    const select = screen.getByRole('combobox');
    await user.click(select);

    const option = await screen.findByText('Apple');
    await user.click(option);

    expect(handleChange).toHaveBeenCalledWith('apple', expect.any(Object));
  });

  it('should support search', async () => {
    const user = userEvent.setup();
    render(<Select options={options} showSearch placeholder="Search" />);

    const select = screen.getByRole('combobox');
    await user.click(select);

    const input = screen.getByRole('combobox');
    await user.type(input, 'App');

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });
  });

  it('should support multiple selection', async () => {
    const user = userEvent.setup();
    render(<Select mode="multiple" options={options} placeholder="Select" />);

    const select = screen.getByRole('combobox');
    await user.click(select);

    await user.click(await screen.findByText('Apple'));
    await user.click(await screen.findByText('Banana'));

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('Banana')).toBeInTheDocument();
  });
});
```

### DatePicker 组件测试

```typescript
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { DatePicker } from 'antd';
import dayjs from 'dayjs';

describe('DatePicker Component', () => {
  it('should render date picker', () => {
    render(<DatePicker />);
    expect(screen.getByPlaceholderText('Select date')).toBeInTheDocument();
  });

  it('should select date', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<DatePicker onChange={handleChange} />);

    const input = screen.getByPlaceholderText('Select date');
    await user.click(input);

    // 选择当前日期
    const today = new Date().getDate();
    const todayButton = await screen.findByText(String(today));
    await user.click(todayButton);

    expect(handleChange).toHaveBeenCalled();
  });

  it('should work with controlled value', () => {
    const date = dayjs('2024-01-15');
    const { rerender } = render(<DatePicker value={date} />);

    const input = screen.getByDisplayValue('2024-01-15');
    expect(input).toBeInTheDocument();

    // 更新 value
    const newDate = dayjs('2024-01-20');
    rerender(<DatePicker value={newDate} />);

    expect(screen.getByDisplayValue('2024-01-20')).toBeInTheDocument();
  });

  it('should disable dates before minDate', () => {
    const minDate = dayjs('2024-01-10');
    render(<DatePicker minDate={minDate} />);

    const input = screen.getByPlaceholderText('Select date');
    // 点击打开日历
    // 验证 1月9日被禁用
  });

  it('should format display value', () => {
    const date = dayjs('2024-01-15');
    render(<DatePicker value={date} format="DD/MM/YYYY" />);

    expect(screen.getByDisplayValue('15/01/2024')).toBeInTheDocument();
  });
});
```

---

## 交互测试

### 用户交互模拟

#### Form 表单提交测试

```typescript
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Form, Input, Button } from 'antd';

describe('Form Interaction', () => {
  it('should submit form with valid data', async () => {
    const user = userEvent.setup();
    const handleSubmit = jest.fn();

    render(
      <Form onFinish={handleSubmit} layout="vertical">
        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Email is required' },
            { type: 'email', message: 'Invalid email' },
          ]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="Password"
          name="password"
          rules={[{ required: true, message: 'Password is required' }]}
        >
          <Input.Password />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit
          </Button>
        </Form.Item>
      </Form>
    );

    // 填写表单
    await user.type(
      screen.getByPlaceholderText('Email'),
      'user@example.com'
    );
    await user.type(
      screen.getByPlaceholderText('input password'),
      'password123'
    );

    // 提交表单
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith(
        {
          email: 'user@example.com',
          password: 'password123',
        },
        expect.any(Object)
      );
    });
  });

  it('should show validation errors', async () => {
    const user = userEvent.setup();
    const handleSubmit = jest.fn();

    render(
      <Form onFinish={handleSubmit}>
        <Form.Item
          label="Email"
          name="email"
          rules={[{ required: true, message: 'Email is required' }]}
        >
          <Input />
        </Form.Item>

        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form>
    );

    // 直接提交空表单
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(handleSubmit).not.toHaveBeenCalled();
    });
  });

  it('should validate email format', async () => {
    const user = userEvent.setup();

    render(
      <Form>
        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true },
            { type: 'email', message: 'Invalid email format' },
          ]}
        >
          <Input />
        </Form.Item>

        <Button type="primary" htmlType="submit">
          Submit
        </Button>
      </Form>
    );

    // 输入无效邮箱
    await user.type(
      screen.getByRole('textbox'),
      'invalid-email'
    );

    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    });
  });
});
```

### Modal 组件测试

```typescript
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Modal, Button } from 'antd';

describe('Modal Component', () => {
  it('should render modal when open', () => {
    render(
      <Modal open title="Test Modal" onCancel={jest.fn()} onOk={jest.fn()}>
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('should not render modal when closed', () => {
    render(
      <Modal open={false} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
  });

  it('should call onOk when OK button clicked', async () => {
    const user = userEvent.setup();
    const handleOk = jest.fn();

    render(
      <Modal open title="Test Modal" onOk={handleOk} onCancel={jest.fn()}>
        <p>Modal content</p>
      </Modal>
    );

    await user.click(screen.getByRole('button', { name: /OK/i }));
    expect(handleOk).toHaveBeenCalled();
  });

  it('should call onCancel when Cancel button clicked', async () => {
    const user = userEvent.setup();
    const handleCancel = jest.fn();

    render(
      <Modal open title="Test Modal" onOk={jest.fn()} onCancel={handleCancel}>
        <p>Modal content</p>
      </Modal>
    );

    await user.click(screen.getByRole('button', { name: /Cancel/i }));
    expect(handleCancel).toHaveBeenCalled();
  });

  it('should close on ESC key press', async () => {
    const user = userEvent.setup();
    const handleCancel = jest.fn();

    render(
      <Modal
        open
        title="Test Modal"
        onOk={jest.fn()}
        onCancel={handleCancel}
      >
        <p>Modal content</p>
      </Modal>
    );

    await user.keyboard('{Escape}');
    expect(handleCancel).toHaveBeenCalled();
  });

  it('should support controlled open state', () => {
    const { rerender } = render(
      <Modal open={false} title="Test Modal">
        <p>Content</p>
      </Modal>
    );

    expect(screen.queryByText('Content')).not.toBeInTheDocument();

    rerender(
      <Modal open={true} title="Test Modal">
        <p>Content</p>
      </Modal>
    );

    expect(screen.getByText('Content')).toBeInTheDocument();
  });
});
```

### Table 交互测试

```typescript
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Table } from 'antd';

describe('Table Interaction', () => {
  const dataSource = [
    { key: '1', name: 'John Brown', age: 32, address: 'New York' },
    { key: '2', name: 'Jim Green', age: 42, address: 'London' },
    { key: '3', name: 'Joe Black', age: 28, address: 'Paris' },
  ];

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Age', dataIndex: 'age', key: 'age' },
    { title: 'Address', dataIndex: 'address', key: 'address' },
  ];

  it('should render table with data', () => {
    render(<Table dataSource={dataSource} columns={columns} />);

    expect(screen.getByText('John Brown')).toBeInTheDocument();
    expect(screen.getByText('Jim Green')).toBeInTheDocument();
    expect(screen.getByText('Joe Black')).toBeInTheDocument();
  });

  it('should select row', async () => {
    const user = userEvent.setup();

    render(
      <Table
        dataSource={dataSource}
        columns={columns}
        rowSelection={{
          type: 'checkbox',
          onChange: jest.fn(),
        }}
      />
    );

    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]); // 第一行数据复选框

    expect(checkboxes[1]).toBeChecked();
  });

  it('should sort column when clicking header', async () => {
    const user = userEvent.setup();
    render(
      <Table
        dataSource={dataSource}
        columns={[
          { title: 'Name', dataIndex: 'name', sorter: true },
          { title: 'Age', dataIndex: 'age' },
        ]}
      />
    );

    const nameHeader = screen.getByText('Name');
    await user.click(nameHeader);

    await waitFor(() => {
      // 验证排序图标出现
      const sortIcon = screen.getByLabelText(/sort/i);
      expect(sortIcon).toBeInTheDocument();
    });
  });

  it('should filter data', async () => {
    const user = userEvent.setup();
    render(
      <Table
        dataSource={dataSource}
        columns={[
          {
            title: 'Name',
            dataIndex: 'name',
            filters: [
              { text: 'John', value: 'John' },
              { text: 'Jim', value: 'Jim' },
            ],
            onFilter: (value, record) =>
              record.name.includes(value as string),
          },
        ]}
      />
    );

    // 点击筛选图标
    const filterIcon = screen.getByRole('img', { name: /filter/i });
    await user.click(filterIcon);

    // 选择筛选条件
    const johnFilter = await screen.findByText('John');
    await user.click(johnFilter);

    await waitFor(() => {
      expect(screen.getByText('John Brown')).toBeInTheDocument();
      expect(screen.queryByText('Jim Green')).not.toBeInTheDocument();
    });
  });
});
```

---

## 快照测试

### 基础快照测试

```typescript
import { render } from '@/test-utils';
import { Button, Card } from 'antd';

describe('Snapshot Tests', () => {
  it('should match button snapshot', () => {
    const { container } = render(<Button type="primary">Primary Button</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('should match card snapshot', () => {
    const { container } = render(
      <Card title="Card Title">
        <p>Card content</p>
      </Card>
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('should match form snapshot', () => {
    const { container } = render(
      <Form>
        <Form.Item label="Name" name="name">
          <Input />
        </Form.Item>
        <Form.Item>
          <Button type="primary">Submit</Button>
        </Form.Item>
      </Form>
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
```

### 内联样式快照

```typescript
import { render } from '@/test-utils';
import { Button } from 'antd';

describe('Inline Snapshot Tests', () => {
  it('should match inline snapshot', () => {
    const { container } = render(
      <Button type="primary" style={{ margin: 10 }}>
        Styled Button
      </Button>
    );

    expect(container.firstChild).toMatchInlineSnapshot(`
      <button
        class="ant-btn ant-btn-primary css-dev-only-do-not-override-1xg9z9n"
        style="margin: 10px;"
        type="button"
      >
        <span>Styled Button</span>
      </button>
    `);
  });

  it('should match multiple inline snapshots', () => {
    const types = ['primary', 'default', 'dashed'] as const;

    types.forEach((type) => {
      const { container } = render(<Button type={type}>{type} Button</Button>);
      expect(container.firstChild).toMatchInlineSnapshot(`
        <button
          class="ant-btn ant-btn-${type} css-dev-only-do-not-override-1xg9z9n"
          type="button"
        >
          <span>${type} Button</span>
        </button>
      `);
    });
  });
});
```

### 快照更新策略

```bash
# 更新快照
npm test -- -u

# 检查快照但不更新
npm test -- --ci

# 查看快照差异
npm test -- --verbose
```

---

## Mock 和 Stub

### API Mock with MSW

#### MSW 配置

**src/mocks/handlers.ts**:
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

export const handlers = [
  // Mock 用户登录
  rest.post('/api/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          token: 'mock-token-123',
          user: {
            id: 1,
            name: 'Test User',
            email: 'test@example.com',
          },
        },
      })
    );
  }),

  // Mock 用户数据
  rest.get('/api/users', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: [
          { id: 1, name: 'User 1', email: 'user1@example.com' },
          { id: 2, name: 'User 2', email: 'user2@example.com' },
        ],
      })
    );
  }),

  // Mock 错误响应
  rest.get('/api/error', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        success: false,
        message: 'Internal Server Error',
      })
    );
  }),
];

export const server = setupServer(...handlers);
```

**src/mocks/setupTests.ts**:
```typescript
import { server } from './handlers';

beforeAll(() => {
  // 启动 MSW 服务器
  server.listen();
});

afterEach(() => {
  // 每个测试后重置 handlers
  server.resetHandlers();
});

afterAll(() => {
  // 关闭 MSW 服务器
  server.close();
});
```

#### MSW 使用示例

```typescript
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { Login } from './Login';

describe('Login with MSW', () => {
  it('should login successfully', async () => {
    const user = userEvent.setup();
    render(<Login />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');

    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText(/welcome test user/i)).toBeInTheDocument();
    });
  });

  it('should show error message on login failure', async () => {
    const user = userEvent.setup();

    // 覆盖默认 handler，返回错误
    server.use(
      rest.post('/api/login', (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({
            success: false,
            message: 'Invalid credentials',
          })
        );
      })
    );

    render(<Login />);

    await user.type(screen.getByLabelText(/email/i), 'wrong@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');

    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});
```

### 组件 Mock

```typescript
import { render, screen } from '@/test-utils';
import { UserProfile } from './UserProfile';

// Mock 子组件
jest.mock('./UserAvatar', () => ({
  UserAvatar: ({ src }: { src: string }) => (
    <img src={src} alt="User Avatar" data-testid="user-avatar" />
  ),
}));

// Mock API 模块
jest.mock('@/api/users', () => ({
  getUser: jest.fn(() => Promise.resolve({ id: 1, name: 'Test User' })),
}));

describe('Component Mocking', () => {
  it('should use mocked component', () => {
    render(<UserProfile userId={1} />);

    expect(screen.getByTestId('user-avatar')).toBeInTheDocument();
  });

  it('should use mocked API', async () => {
    render(<UserProfile userId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });
});
```

### Hook 测试

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useUser } from './useUser';

describe('useUser Hook', () => {
  it('should fetch user data', async () => {
    // Mock fetch
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ id: 1, name: 'Test User' }),
      })
    ) as jest.Mock;

    const { result } = renderHook(() => useUser(1));

    await waitFor(() => {
      expect(result.current.user).toEqual({ id: 1, name: 'Test User' });
    });
  });

  it('should handle loading state', () => {
    const { result } = renderHook(() => useUser(1));

    expect(result.current.loading).toBe(true);
  });

  it('should handle error state', async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error('API Error'))) as jest.Mock;

    const { result } = renderHook(() => useUser(1));

    await waitFor(() => {
      expect(result.current.error).toEqual(new Error('API Error'));
    });
  });
});
```

---

## 测试最佳实践

### AAA 模式 (Arrange-Act-Assert)

```typescript
describe('AAA Pattern', () => {
  it('should calculate total price', () => {
    // Arrange - 准备测试数据和环境
    const price = 100;
    const quantity = 2;
    const taxRate = 0.1;

    // Act - 执行被测试的操作
    const total = (price * quantity) * (1 + taxRate);

    // Assert - 验证结果
    expect(total).toBe(220);
  });
});
```

### 避免测试实现细节

**❌ 不好的实践** - 测试实现细节：
```typescript
it('should set state to true when button clicked', () => {
  const component = new ButtonComponent();
  component.handleClick();
  expect(component.state.isActive).toBe(true);
});
```

**✅ 好的实践** - 测试用户行为：
```typescript
it('should activate button when clicked', async () => {
  const user = userEvent.setup();
  render(<ButtonActivator />);

  await user.click(screen.getByRole('button'));

  expect(screen.getByRole('button')).toHaveClass('active');
});
```

### 测试用户行为

**❌ 不好的实践**：
```typescript
it('should call onChange prop', () => {
  const handleChange = jest.fn();
  render(<Select onChange={handleChange} />);

  // 直接调用 prop
  handleChange('value');

  expect(handleChange).toHaveBeenCalledWith('value');
});
```

**✅ 好的实践**：
```typescript
it('should select option when user clicks', async () => {
  const user = userEvent.setup();
  const handleChange = jest.fn();

  render(<Select onChange={handleChange} options={[{ value: '1', label: 'One' }]} />);

  // 模拟真实用户操作
  await user.click(screen.getByRole('combobox'));
  await user.click(await screen.findByText('One'));

  expect(handleChange).toHaveBeenCalledWith('1');
});
```

### 选择器最佳实践

**优先级顺序**：
1. **最优先**: `getByRole()` - 可访问性
2. **其次**: `getByLabelText()` - 表单关联
3. **然后**: `getByPlaceholderText()` - 输入框
4. **之后**: `getByText()` - 文本内容
5. **最后**: `getByTestId()` - 仅用于无语义元素

```typescript
// ✅ 最好的选择器
screen.getByRole('button', { name: /submit/i })

// ✅ 好的选择器
screen.getByLabelText('Email')
screen.getByPlaceholderText('Enter email')
screen.getByText('Submit')

// ⚠️ 最后的选择
screen.getByTestId('submit-button')
```

---

## E2E 测试

### Cypress 配置

**cypress.config.ts**:
```typescript
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: false,
    video: false,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
  },
});
```

### Cypress 测试示例

**cypress/e2e/login.cy.ts**:
```typescript
describe('Login Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('should login successfully with valid credentials', () => {
    cy.get('input[name="email"]').type('user@example.com');
    cy.get('input[name="password"]').type('password123');

    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.contains('Welcome, User').should('be.visible');
  });

  it('should show error with invalid credentials', () => {
    cy.get('input[name="email"]').type('wrong@example.com');
    cy.get('input[name="password"]').type('wrongpassword');

    cy.get('button[type="submit"]').click();

    cy.contains('Invalid credentials').should('be.visible');
    cy.url().should('include', '/login');
  });

  it('should validate email format', () => {
    cy.get('input[name="email"]').type('invalid-email');
    cy.get('input[name="password"]').type('password123');

    cy.get('button[type="submit"]').click();

    cy.contains('Invalid email format').should('be.visible');
  });
});
```

### Playwright 配置

**playwright.config.ts**:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
});
```

### Playwright 测试示例

**e2e/login.spec.ts**:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should login successfully', async ({ page }) => {
    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('text=Welcome, User')).toBeVisible();
  });

  test('should show validation errors', async ({ page }) => {
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Email is required')).toBeVisible();
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('should handle API errors', async ({ page }) => {
    // Mock API 响应
    await page.route('**/api/login', route => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({ message: 'Invalid credentials' }),
      });
    });

    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});
```

---

## 覆盖率

### 覆盖率配置

**jest.config.js**:
```javascript
module.exports = {
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
  ],

  coverageThreshold: {
    global: {
      statements: 70,
      branches: 70,
      functions: 70,
      lines: 70,
    },
  },

  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
  ],
};
```

### 覆盖率报告

```bash
# 生成覆盖率报告
npm run test:coverage

# 输出示例：
# ---------------------|---------|----------|---------|---------|-------------------
# File                 | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
# ---------------------|---------|----------|---------|---------|-------------------
# All files            |   85.23 |    78.45  |   88.12 |   85.45 |
#  src                 |   85.23 |    78.45  |   88.12 |   85.45 |
#   components         |   92.15 |    85.32  |   95.12 |   92.34 |
#    Button.tsx        |   95.00 |    90.00  |  100.00 |   95.00 | 45
#    Form.tsx          |   88.50 |    82.15  |   92.11 |   88.50 | 23-24,56
# ---------------------|---------|----------|---------|---------|-------------------
```

---

## 最佳实践

### 1. 测试文件组织

**✅ 推荐**:
```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   └── Form/
│       ├── Form.tsx
│       ├── Form.test.tsx
│       └── index.ts
```

**❌ 避免**:
```
tests/
├── Button.test.tsx
└── Form.test.tsx
```

### 2. 测试命名规范

**✅ 推荐** - 描述性命名：
```typescript
describe('Button Component', () => {
  it('should render primary button with correct styles', () => {});
  it('should call onClick handler when clicked', () => {});
  it('should be disabled when loading prop is true', () => {});
});
```

**❌ 避免** - 模糊命名：
```typescript
it('should work', () => {});
it('test button', () => {});
```

### 3. 异步测试

**✅ 推荐** - 使用 async/await：
```typescript
it('should fetch data', async () => {
  render(<UserProfile userId={1} />);

  await waitFor(() => {
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });
});
```

**❌ 避免** - 使用假计时器：
```typescript
it('should fetch data', () => {
  jest.useFakeTimers();
  render(<UserProfile userId={1} />);

  jest.runAllTimers();

  expect(screen.getByText('Test User')).toBeInTheDocument();
});
```

### 4. 隔离测试

**✅ 推荐** - 独立的测试：
```typescript
describe('Form Component', () => {
  beforeEach(() => {
    // 每个测试前重置
    jest.clearAllMocks();
  });

  it('should validate required fields', () => {
    // 独立的测试逻辑
  });

  it('should submit valid form', () => {
    // 独立的测试逻辑，不依赖上一个测试
  });
});
```

**❌ 避免** - 依赖性测试：
```typescript
it('should validate form', () => {
  // 依赖上一个测试的状态
});
```

### 5. 测试数据管理

**✅ 推荐** - 使用工厂函数：
```typescript
const createMockUser = (overrides = {}) => ({
  id: 1,
  name: 'Test User',
  email: 'test@example.com',
  ...overrides,
});

it('should display user info', () => {
  const user = createMockUser({ name: 'Custom Name' });
  render(<UserProfile user={user} />);

  expect(screen.getByText('Custom Name')).toBeInTheDocument();
});
```

**❌ 避免** - 重复的数据定义：
```typescript
it('should display user info', () => {
  const user = { id: 1, name: 'Test User', email: 'test@example.com', age: 30, ... };
  render(<UserProfile user={user} />);
});
```

---

## 常见问题

### Q: 如何测试 Portal 组件（Modal、Dropdown）？

A: React Testing Library 自动处理 Portal，只需测试内容是否出现在 DOM 中：

```typescript
it('should render modal content', () => {
  render(
    <Modal open>
      <p>Modal Content</p>
    </Modal>
  );

  expect(screen.getByText('Modal Content')).toBeInTheDocument();
});
```

### Q: 如何测试 Ant Design 样式？

A: 使用 `toHaveClass` 或 `toHaveStyle`：

```typescript
it('should apply primary class', () => {
  render(<Button type="primary">Primary</Button>);

  expect(screen.getByRole('button')).toHaveClass('ant-btn-primary');
});

it('should apply custom style', () => {
  render(<Button style={{ margin: 10 }}>Button</Button>);

  expect(screen.getByRole('button')).toHaveStyle({ margin: '10px' });
});
```

### Q: 如何测试异步验证？

A: 使用 `waitFor` 等待异步操作完成：

```typescript
it('should validate email asynchronously', async () => {
  const validateEmail = async (email: string) => {
    await new Promise(resolve => setTimeout(resolve, 100));
    return email.includes('@');
  };

  render(<Input onValidate={validateEmail} />);

  await userEvent.type(screen.getByRole('textbox'), 'test@example.com');

  await waitFor(() => {
    expect(screen.getByText('Valid email')).toBeInTheDocument();
  });
});
```

### Q: 如何测试定时器？

A: 使用 Jest 的 fake timers：

```typescript
describe('Timer Tests', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should call callback after delay', () => {
    const callback = jest.fn();
    setTimeout(callback, 1000);

    jest.advanceTimersByTime(1000);

    expect(callback).toHaveBeenCalledTimes(1);
  });
});
```

### Q: 如何测试组件的 console.error？

A: Mock console 并验证调用：

```typescript
it('should log error when props are invalid', () => {
  const consoleError = jest.spyOn(console, 'error').mockImplementation();

  render(<Button type="invalid" as="invalid-prop" />);

  expect(consoleError).toHaveBeenCalled();

  consoleError.mockRestore();
});
```

### Q: 如何测试可访问性？

A: 使用 jest-axe 或 React Testing Library 的 `toHaveAccessibleName`：

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('should have no accessibility violations', async () => {
  const { container } = render(<Button>Click me</Button>);
  const results = await axe(container);

  expect(results).toHaveNoViolations();
});
```

---

## 参考资源

### 官方文档
- [Jest 官方文档](https://jestjs.io/)
- [React Testing Library 官方文档](https://testing-library.com/docs/react-testing-library/intro/)
- [Ant Design 测试指南](https://ant.design/docs/react/testing-cn)
- [Cypress 官方文档](https://docs.cypress.io/)
- [Playwright 官方文档](https://playwright.dev/)

### 推荐文章
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Mock Service Worker Guide](https://mswjs.io/docs)
- [Accessibility Testing](https://www.deque.com/axe/)

---

## 版本要求

- **Jest**: >= 29.0
- **React Testing Library**: >= 14.0
- **Ant Design**: >= 5.0.0
- **Cypress**: >= 13.0 (可选)
- **Playwright**: >= 1.40 (可选)
- **msw**: >= 2.0 (可选)

---

**最后更新**: 2026-02-10
**维护者**: lazygophers
