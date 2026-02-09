# JavaScript 命名规范

## 核心约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量 | camelCase | `userName`, `isActive` |
| 函数 | camelCase | `getUserData`, `fetchPosts` |
| 类/构造函数 | PascalCase | `UserManager`, `HttpClient` |
| 常量 | UPPER_SNAKE_CASE | `MAX_TIMEOUT`, `API_KEY` |
| 布尔值 | is/has/can 前缀 | `isActive`, `hasChildren` |
| 文件名 | kebab-case | `user-service.js`, `login-form.jsx` |
| 私有属性 | # 或 _ 前缀 | `#privateField`, `_internal` |

## 变量命名

### 基本变量

```javascript
// ✅ 推荐
const userName = 'John';
const isActive = true;
const hasChildren = false;
const canEdit = true;
const userCount = 100;
const MAX_RETRIES = 3;

// ❌ 避免
const user_name = 'John';      // 不用 snake_case
const active = true;           // 布尔值缺少 is/has 前缀
const count = 100;             // 命名不清晰
const max_retries = 3;         // 常量不用 UPPER_SNAKE_CASE
```

### 数组/集合

```javascript
// ✅ 推荐：使用复数形式
const users = ['John', 'Jane'];
const items = [{ id: 1 }, { id: 2 }];
const productList = [];

// ❌ 避免
const userList = ['John'];    // 不用 List 后缀
const itemArray = [];         // 不用 Array 后缀
```

### 临时变量

```javascript
// ✅ 推荐：清晰表达用途
for (let i = 0; i < 10; i++) { }
for (let index = 0; index < items.length; index++) { }
const [first, ...rest] = array;
const result = await fetchData();

// ❌ 避免
const arr = [];              // 不清晰
const data = await get();     // 不清晰
```

## 函数命名

### 动词 + 名词模式

```javascript
// ✅ 推荐
function getUserData(id) { }
function fetchPosts(userId) { }
function validateEmail(email) { }
function handleSubmit(event) { }
function calculateTotal(price, quantity) { }
function formatDate(date) { }

// ❌ 避免
function user(id) { }                    // 缺少动词
function data() { }                       // 不清晰
function submit(event) { }               // 缺少 handle
```

### 布尔函数

```javascript
// ✅ 推荐：is/has/can + 形容词/过去分词
function isValid(email) { }
function isEmpty(array) { }
function hasPermission(user) { }
function canAccess(resource) { }
function exists(path) { }
function isLoading() { }

// ❌ 避免
function valid(email) { }
function empty(array) { }
function permission(user) { }
```

### 异步函数

```javascript
// ✅ 推荐：使用 async，命名清晰
async function fetchUserData(userId) { }
async function getProducts() { }
async function saveToDatabase(data) { }
async function loadConfig() { }

// ❌ 避免
async function user(id) { }
async function get() { }
```

## 类命名

### PascalCase

```javascript
// ✅ 推荐
class UserManager { }
class HttpClient { }
class DataFetcher { }
class ErrorBoundary { }
class EventEmitter { }

// ❌ 避免
class userManager { }
class http_client { }
```

### 方法命名

```javascript
class UserManager {
  // ✅ 推荐
  async getUser(id) { }
  async createUser(data) { }
  updateUser(id, data) { }
  deleteUser(id) { }
  isAdmin(user) { }
  hasPermission(user, action) { }

  // ❌ 避免
  user(id) { }
  create(data) { }
  admin(user) { }
}
```

## 常量命名

### UPPER_SNAKE_CASE

```javascript
// ✅ 推荐
const MAX_TIMEOUT = 5000;
const API_BASE_URL = 'https://api.example.com';
const HTTP_STATUS_OK = 200;
const DEFAULT_PAGE_SIZE = 20;

// ❌ 避免
const maxTimeout = 5000;
const API_BASE_URL = 'https://api.example.com';  // 不一致
const defaultPageSize = 20;
```

### 配置常量

```javascript
// ✅ 推荐：清晰表达用途
const CONFIG = {
  API_TIMEOUT: 30000,
  MAX_RETRY_COUNT: 3,
  PAGE_SIZE: 20,
};

const COLORS = {
  PRIMARY: '#007bff',
  SECONDARY: '#6c757d',
};

// ❌ 避免
const config = { timeout: 30000 };              // 不清晰
const colors = { p: '#007bff' };               // 缩写不清晰
```

## 文件命名

### kebab-case

```
// ✅ 推荐
user-service.js
login-form.jsx
auth-hook.js
api-client.ts
utils-helper.js

// ❌ 避免
userService.js         // camelCase
UserService.js         // PascalCase
user_service.py        // snake_case (Python 风格)
```

### 组件文件

```
// ✅ 推荐：PascalCase
Button.jsx
UserCard.jsx
LoginForm.jsx
ModalDialog.jsx

// ❌ 避免
button.jsx
user-card.jsx
loginForm.jsx
```

## 私有成员

### # 前缀（ES2022）

```javascript
class Counter {
  #count = 0;
  #increment() {
    this.#count++;
  }
}

// ✅ 推荐：使用真正的私有字段
```

### _ 前缀（约定俗成）

```javascript
class User {
  _internalId = '123';    // 约定：内部使用，但仍可访问

  _privateMethod() { }   // 约定：私有方法
}

// ⚠️ 注意：这只是约定，不是真正的私有
```

## 枚举/类型命名

### PascalCase

```typescript
// TypeScript 推荐
enum UserRole {
  Admin = 'admin',
  User = 'user',
  Guest = 'guest',
}

type UserStatus = 'active' | 'inactive' | 'pending';

interface User {
  id: string;
  name: string;
  role: UserRole;
  status: UserStatus;
}

// ✅ 推荐
```

## 常见反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| `data`, `info` | 过于笼统 | 具体命名 |
| `temp`, `tmp` | 含义不明 | 表达真实用途 |
| `list` 后缀 | 冗余 | 使用复数 |
| 缩写过短 | 难以理解 | 使用完整单词 |
| 单字母 | 难以搜索 | 使用描述性名称（循环除外） |

## 快速检查清单

- [ ] 变量使用 camelCase
- [ ] 函数使用动词 + 名词
- [ ] 类使用 PascalCase
- [ ] 常量使用 UPPER_SNAKE_CASE
- [ ] 布尔值使用 is/has/can 前缀
- [ ] 文件名使用 kebab-case
- [ ] 组件使用 PascalCase
- [ ] 避免过于笼统的命名（data、info、temp）
