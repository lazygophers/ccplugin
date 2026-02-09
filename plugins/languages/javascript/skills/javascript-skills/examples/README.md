# JavaScript 代码示例

本目录包含符合规范和不符合规范的代码示例（good/bad），用于学习和参考。

## 目录结构

```
examples/
├── good/
│   ├── naming-conventions.js
│   ├── async-await.js
│   ├── components/
│   │   └── UserCard.jsx
│   └── error-handling.js
│
├── bad/
│   ├── naming-conventions.js
│   ├── async-await.js
│   ├── components/
│   │   └── UserCard.jsx
│   └── error-handling.js
│
└── README.md
```

## 命名规范示例

### Good

```javascript
// good/naming-conventions.js

// 变量使用 camelCase
const userName = 'John';
const isActive = true;
const hasChildren = false;
const userList = [];

// 函数使用动词 + 名词
function getUserData(userId) {
  return fetch(`/api/users/${userId}`);
}

async function fetchUserPosts(userId) {
  const response = await fetch(`/api/users/${userId}/posts`);
  return response.json();
}

// 常量使用 UPPER_SNAKE_CASE
const MAX_TIMEOUT = 5000;
const API_BASE_URL = 'https://api.example.com';

// 类使用 PascalCase
class UserManager {
  async getUser(id) {
    return fetch(`/api/users/${id}`).then(r => r.json());
  }
}
```

### Bad

```javascript
// bad/naming-conventions.js

// 变量使用 snake_case
const user_name = 'John';
const user_list = [];

// 布尔值缺少 is/has 前缀
const active = true;
const children = false;

// 函数命名不清晰
function user(id) {
  return fetch(`/api/users/${id}`).then(r => r.json());
}

function data() {
  return fetch('/api/data').then(r => r.json());
}

// 常量不使用 UPPER_SNAKE_CASE
const max_timeout = 5000;
const apiBaseUrl = 'https://api.example.com';

// 类不使用 PascalCase
class user_manager {
  get_user(id) {
    return fetch(`/api/users/${id}`).then(r => r.json());
  }
}
```

## 异步编程示例

### Good

```javascript
// good/async-await.js

// 清晰的 async/await
async function fetchUserData(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}

// Promise.allSettled 处理多个请求
async function fetchAllData() {
  const results = await Promise.allSettled([
    fetchUsers(),
    fetchPosts(),
    fetchComments(),
  ]);

  return results.map(result => {
    if (result.status === 'fulfilled') {
      return { status: 'success', data: result.value };
    }
    return { status: 'error', error: result.reason };
  });
}

// 异步函数返回 Promise
async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Bad

```javascript
// bad/async-await.js

// 不处理错误
async function fetchUserData(userId) {
  const response = await fetch(`/api/users/${userId}`);
  return response.json();
}

// 回调地狱
function fetchUserData(userId, callback) {
  fetch(`/api/users/${userId}`, (error, response) => {
    if (error) {
      callback(error);
      return;
    }
    response.json((error, data) => {
      if (error) {
        callback(error);
        return;
      }
      callback(null, data);
    });
  });
}

// 不使用 async/await
function fetchUserData(userId) {
  return fetch(`/api/users/${userId}`)
    .then(response => response.json())
    .then(data => {
      console.log(data);
      return data;
    });
}

// Promise.all 一个失败全部失败
async function fetchAllData() {
  const results = await Promise.all([
    fetchUsers(),    // 如果这个失败，全部失败
    fetchPosts(),
    fetchComments(),
  ]);
  return results;
}
```

## 组件示例

### Good

```jsx
// good/components/UserCard.jsx

import { useState, useEffect } from 'react';

// 命名：PascalCase
export function UserCard({ userId, onEdit }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadUser() {
      try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch user');
        }
        const data = await response.json();
        setUser(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, [userId]);

  if (loading) {
    return <div className="user-card loading">Loading...</div>;
  }

  if (error) {
    return <div className="user-card error">{error}</div>;
  }

  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <button onClick={() => onEdit(userId)}>Edit</button>
    </div>
  );
}
```

### Bad

```jsx
// bad/components/UserCard.jsx

import { useState, useEffect } from 'react';

// 命名：camelCase（非组件）
function user_card({ user_id, on_edit }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 不处理错误
    fetch(`/api/users/${user_id}`)
      .then(response => response.json())
      .then(data => setUser(data));
  }, []);

  return (
    <div className="user_card">
      <h3>{user?.name}</h3>
      <p>{user?.email}</p>
      <button onClick={() => on_edit(user_id)}>edit</button>
    </div>
  );
}

// 无状态组件使用变量命名
function card(props) {
  return <div>{props.user.name}</div>;
}
```

## 错误处理示例

### Good

```javascript
// good/error-handling.js

// 自定义错误类
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// 验证函数
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('Invalid email format', 'email');
  }
}

// API 调用
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new ApiError(
        `Request failed: ${response.statusText}`,
        response.status
      );
    }
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message, 0);
  }
}

// 使用错误边界
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
```

### Bad

```javascript
// bad/error-handling.js

// 不使用自定义错误
function validateEmail(email) {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new Error('Invalid email');  // 太笼统
  }
}

// 静默忽略错误
async function fetchData(url) {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    // 静默忽略
  }
}

// 不处理错误
async function fetchData(url) {
  const response = await fetch(url);
  return await response.json();
}

// 不传播错误
async function fetchData(url) {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    console.error(error);
  }
}

// 错误消息泄露敏感信息
function handleLogin(username, password) {
  if (password === 'secret123') {  // 安全问题！
    return { success: true };
  }
  throw new Error(`Wrong password for user: ${username}`);
}
```

## ESM 模块示例

### Good

```javascript
// good/modules.js

// 具名导出（推荐）
export const API_BASE_URL = 'https://api.example.com';
export async function fetchUser(id) {
  const response = await fetch(`${API_BASE_URL}/users/${id}`);
  return response.json();
}
export function formatDate(date) {
  return new Date(date).toLocaleDateString();
}

// 默认导出仅用于主要功能
export default class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async get(path) {
    const response = await fetch(`${this.baseUrl}${path}`);
    return response.json();
  }
}

// type-only 导入（TypeScript）
import type { User } from './types.js';
```

### Bad

```javascript
// bad/modules.js

// 混合导出
export const API_BASE_URL = 'https://api.example.com';
export default {
  fetchUser(id) { },
  formatDate(date) { },
};

// 默认导出过于复杂
export default {
  getUser(id) { },
  createUser(data) { },
  updateUser(id, data) { },
  deleteUser(id) { },
};

// 没有明确导出
module.exports = {
  a() { },
  b() { },
  c() { },
};
```

## 快速参考

| 场景 | Good | Bad |
|------|------|-----|
| 变量命名 | `userName` | `user_name` |
| 常量命名 | `MAX_TIMEOUT` | `max_timeout` |
| 函数命名 | `getUserData` | `user(id)` |
| 错误处理 | `try-catch` | 不处理 |
| 异步 | `async/await` | 回调 |
| 组件命名 | `UserCard` | `user_card` |
| 模块导出 | 具名导出 | 默认导出混合 |
