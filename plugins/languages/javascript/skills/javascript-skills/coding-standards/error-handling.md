# JavaScript 错误处理规范

## 基本原则

### try-catch

```javascript
// ✅ 推荐：始终包裹可能的错误
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;  // 重新抛出，让调用者处理
  }
}

// ❌ 避免：不处理错误
async function fetchData(url) {
  const response = await fetch(url);
  return await response.json();
}

// ❌ 避免：静默忽略错误
async function fetchData(url) {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    // 静默忽略
  }
}
```

### Promise 错误处理

```javascript
// ✅ 推荐：使用 catch
async function fetchData(url) {
  return fetch(url)
    .then(response => response.json())
    .catch(error => {
      console.error('Fetch error:', error);
      throw error;
    });
}

// ✅ 推荐：async/await 使用 try-catch
async function fetchData(url) {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

// ❌ 避免：不处理 Promise 错误
fetch(url).then(response => response.json());
```

## 自定义错误类

### Error 继承

```javascript
// ✅ 推荐：自定义错误类
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

class AuthenticationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

class NetworkError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.name = 'NetworkError';
    this.statusCode = statusCode;
  }
}
```

### 使用自定义错误

```javascript
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('Invalid email format', 'email');
  }
}

async function login(username, password) {
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (response.status === 401) {
      throw new AuthenticationError('Invalid credentials');
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ValidationError) {
      // 处理验证错误
      return { error: error.message, field: error.field };
    }
    if (error instanceof AuthenticationError) {
      // 处理认证错误
      return { error: error.message };
    }
    // 处理其他错误
    throw error;
  }
}
```

## 错误边界

### React Error Boundary

```javascript
// ✅ 推荐：错误边界组件
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// 使用
function App() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

### hooks 中的错误处理

```javascript
// ✅ 推荐：useAsync 模式
function useAsync(asyncFn) {
  const [state, setState] = useState({ status: 'idle', data: null, error: null });

  const execute = async () => {
    setState({ status: 'pending', data: null, error: null });
    try {
      const data = await asyncFn();
      setState({ status: 'success', data, error: null });
      return data;
    } catch (error) {
      setState({ status: 'error', data: null, error });
      throw error;
    }
  };

  return { ...state, execute };
}
```

## 异步错误处理

### Promise.allSettled

```javascript
// ✅ 推荐：使用 allSettled 处理多个异步操作
async function fetchAllData() {
  const results = await Promise.allSettled([
    fetchUsers(),
    fetchPosts(),
    fetchComments(),
  ]);

  const data = results.map((result, index) => {
    if (result.status === 'fulfilled') {
      return { status: 'success', data: result.value, index };
    }
    return { status: 'error', error: result.reason, index };
  });

  return data;
}

// ❌ 避免：使用 all（一个失败全部失败）
const results = await Promise.all([
  fetchUsers(),
  fetchPosts(),  // 如果这个失败，全部失败
]);
```

### 错误传播

```javascript
// ✅ 推荐：统一错误格式
async function handleApiRequest(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new NetworkError(
        `Request failed with status ${response.status}`,
        response.status
      );
    }
    return await response.json();
  } catch (error) {
    if (error instanceof NetworkError) {
      throw error;
    }
    // 包装未知错误
    throw new NetworkError(error.message, 0);
  }
}

// ✅ 推荐：调用者处理
async function loadPageData() {
  try {
    const users = await handleApiRequest('/api/users');
    const posts = await handleApiRequest('/api/posts');
    return { users, posts };
  } catch (error) {
    if (error.statusCode === 401) {
      // 处理未认证
      redirectToLogin();
      return;
    }
    // 处理其他错误
    showErrorNotification(error.message);
  }
}
```

## 前端错误处理

### API 错误

```javascript
// ✅ 推荐：统一的 API 错误处理
class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        data.message || 'Request failed',
        response.status,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message, 0, null);
  }
}
```

### 表单验证错误

```javascript
// ✅ 推荐：表单验证错误处理
class FormValidationError extends Error {
  constructor(errors) {
    super('Validation failed');
    this.name = 'FormValidationError';
    this.errors = errors;  // { field: message }
  }
}

function validateForm(formData) {
  const errors = {};

  if (!formData.email) {
    errors.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = 'Invalid email format';
  }

  if (!formData.password) {
    errors.password = 'Password is required';
  } else if (formData.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }

  if (Object.keys(errors).length > 0) {
    throw new FormValidationError(errors);
  }

  return formData;
}
```

## 错误日志

### 控制台输出

```javascript
// ✅ 推荐：清晰错误日志
try {
  await riskyOperation();
} catch (error) {
  console.error('Operation failed:', {
    message: error.message,
    stack: error.stack,
    name: error.name,
  });
}

// ❌ 避免：模糊错误
try {
  await riskyOperation();
} catch (error) {
  console.error('Error:', error);  // 信息不足
}
```

### 上报错误

```javascript
// ✅ 推荐：错误上报
function reportError(error, context = {}) {
  console.error('Error reported:', {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    userAgent: navigator.userAgent,
    ...context,
  });

  // 可选：发送到错误跟踪服务
  // if (window.Sentry) {
  //   Sentry.captureException(error);
  // }
}
```

## 快速检查清单

- [ ] 所有异步操作有错误处理
- [ ] 使用 try-catch 包裹可能出错的代码
- [ ] Promise 链有 catch 处理
- [ ] 自定义错误类型继承 Error
- [ ] 错误边界包裹可能出错的组件
- [ ] 错误信息清晰
- [ ] 错误日志完整
- [ ] 错误正确传播给调用者
- [ ] 生产环境不泄露敏感信息

## 常见反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| 静默忽略错误 | 难以调试 | 记录或处理错误 |
| 过于宽泛的 catch | 隐藏真正问题 | 捕获具体错误 |
| 不重新抛出错误 | 调用者不知情 | 适当传播错误 |
| 错误消息泄露敏感信息 | 安全风险 | 过滤敏感数据 |
| 不区分错误类型 | 无法针对性处理 | 使用自定义错误类 |
