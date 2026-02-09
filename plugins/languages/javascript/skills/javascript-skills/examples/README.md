# JavaScript 代码示例

本目录包含符合规范的 JavaScript 代码示例，用于学习和参考。

## 目录结构

```
examples/
├── error-handling-examples.js    # 错误处理代码示例
├── async-examples.js              # 异步编程代码示例
├── react-examples.jsx             # React 组件代码示例
├── good-bad-comparisons.js       # 代码对比示例（Good vs Bad）
└── README.md                      # 本文件
```

## 代码示例

### 错误处理示例

`error-handling-examples.js` 展示了完整的错误处理模式：

- 基本 try-catch 错误处理
- 自定义错误类（ValidationError、ApiError、NotFoundError）
- API 请求错误处理
- 表单验证错误处理
- Promise.allSettled 处理多个异步操作
- 带重试的请求
- 超时控制（AbortController）
- 错误边界组件

### 异步编程示例

`async-examples.js` 展示了现代异步编程模式：

- async/await 基本用法
- Promise.allSettled 处理多个异步操作
- 并发控制（Promise Pool）
- 超时控制（AbortController 和 Promise.race）
- 异步迭代器和生成器
- 异步防抖和节流
- 避免阻塞事件循环
- 异步队列

### React 组件示例

`react-examples.jsx` 展示了 React 18+ 组件开发：

- 函数组件 + Hooks
- 自定义 Hook（useUser）
- useReducer 复杂状态管理
- useMemo 和 useCallback 性能优化
- 表单处理（受控组件）
- 错误边界组件
- React.memo 组件优化
- Context API 状态管理

### 代码对比示例

`good-bad-comparisons.js` 展示了符合规范和不符合规范的代码对比：

- 命名规范对比
- 变量声明对比
- 异步编程对比
- 函数定义对比
- 对象和数组操作对比
- 条件语句对比
- 模块导出对比
- 错误处理对比
- 字符串处理对比
- 数组方法对比
- 代码组织对比

## 使用方法

### 在浏览器中运行

将示例文件复制到 HTML 中使用：

```html
<!DOCTYPE html>
<html>
<head>
  <title>JavaScript 示例</title>
</head>
<body>
  <h1>检查浏览器控制台</h1>
  <script src="error-handling-examples.js"></script>
  <script src="async-examples.js"></script>
</body>
</html>
```

### 在 Node.js 中运行

```bash
# 运行错误处理示例
node error-handling-examples.js

# 运行异步编程示例
node async-examples.js

# 运行代码对比示例
node good-bad-comparisons.js
```

### 在开发环境中使用

```bash
# 使用 pnpm 运行
pnpm node examples/error-handling-examples.js
```

## 学习路径

1. **基础规范** - 从 `good-bad-comparisons.js` 开始，了解基本规范
2. **错误处理** - 学习 `error-handling-examples.js` 中的错误处理模式
3. **异步编程** - 学习 `async-examples.js` 中的异步编程模式
4. **React 开发** - 学习 `react-examples.jsx` 中的 React 组件模式

## 相关文档

- [SKILL.md](../SKILL.md) - 核心规范入口
- [错误处理规范](../coding-standards/error-handling.md) - 错误处理详细规范
- [异步编程规范](../specialized/async-programming.md) - 异步编程详细规范
- [React 开发规范](../specialized/react-development.md) - React 开发详细规范
