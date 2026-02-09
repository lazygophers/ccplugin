# JavaScript 注释规范

## 核心原则

### 必须遵守

1. **导出必须有注释** - 所有导出的函数、类、常量必须有 JSDoc 注释
2. **说明意图** - 注释说明"是什么"和"为什么"，而不是"怎么做"
3. **简洁清晰** - 注释简洁明了，避免冗余
4. **保持更新** - 代码变更时同步更新注释
5. **避免误导** - 不准确或过时的注释比没有注释更糟糕

### 禁止行为

- 注释显而易见的代码
- 注释与代码不一致
- 使用 HTML 风格的注释 `<!-- -->`
- 注释包含作者、日期等版本控制信息
- 过度注释

## JSDoc 注释

### 函数注释

```javascript
// ✅ 正确 - 完整的 JSDoc 注释
/**
 * 获取用户信息
 * @param {number} userId - 用户 ID
 * @param {Object} options - 配置选项
 * @param {boolean} options.includePosts - 是否包含用户帖子
 * @param {boolean} options.includeFriends - 是否包含好友列表
 * @returns {Promise<User>} 用户信息对象
 * @throws {NotFoundError} 用户不存在时抛出
 * @example
 * const user = await fetchUser(123, { includePosts: true });
 */
async function fetchUser(userId, options = {}) {
  const { includePosts = false, includeFriends = false } = options;
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) {
    throw new NotFoundError(`User ${userId} not found`);
  }
  return response.json();
}

// ❌ 错误 - 缺少 JSDoc 注释
async function fetchUser(userId, options = {}) {
  const response = await fetch(`/api/users/${userId}`);
  return response.json();
}

// ❌ 错误 - 注释过于简单
/**
 * 获取用户
 */
async function fetchUser(userId, options = {}) {
  // ...
}
```

### 类注释

```javascript
// ✅ 正确 - 完整的类注释
/**
 * 用户管理器类
 * 负责用户的增删改查操作
 *
 * @class UserManager
 * @example
 * const manager = new UserManager();
 * const user = await manager.getById(1);
 */
class UserManager {
  /**
   * 创建用户管理器实例
   * @param {Object} apiClient - API 客户端
   */
  constructor(apiClient) {
    this.apiClient = apiClient;
  }

  /**
   * 根据 ID 获取用户
   * @param {number} id - 用户 ID
   * @returns {Promise<User>} 用户对象
   */
  async getById(id) {
    return this.apiClient.get(`/users/${id}`);
  }
}

// ❌ 错误 - 缺少类注释
class UserManager {
  constructor(apiClient) {
    this.apiClient = apiClient;
  }
}
```

### 常量注释

```javascript
// ✅ 正确 - 常量有注释说明用途
/**
 * @constant {number} MAX_RETRY_ATTEMPTS - 最大重试次数
 * @default 3
 */
const MAX_RETRY_ATTEMPTS = 3;

/**
 * @constant {string} API_BASE_URL - API 基础 URL
 */
const API_BASE_URL = 'https://api.example.com';

/**
 * @enum {number} UserStatus - 用户状态枚举
 */
const UserStatus = {
  /** 活跃状态 */
  ACTIVE: 1,
  /** 未激活状态 */
  INACTIVE: 0,
  /** 已删除 */
  DELETED: -1,
};

// ❌ 错误 - 缺少常量注释
const MAX_RETRIES = 3;
const API_URL = 'https://api.example.com';
```

## 单行注释

### 说明意图

```javascript
// ✅ 正确 - 说明为什么需要这样做
// 使用 WeakMap 避免内存泄漏，当对象被垃圾回收时自动清除映射
const privateData = new WeakMap();

// ❌ 错误 - 说明显而易见的代码
// 创建一个 WeakMap
const privateData = new WeakMap();

// ✅ 正确 - 解释复杂算法
// 使用两指针技术在 O(n) 时间内找到目标对
function findPair(numbers, target) {
  const seen = new Set();
  for (const num of numbers) {
    const complement = target - num;
    if (seen.has(complement)) {
      return [complement, num];
    }
    seen.add(num);
  }
  return null;
}

// ❌ 错误 - 注释重复代码
// 遍历数组查找
for (const num of numbers) {
  // ...
}
```

### TODO 和 FIXME

```javascript
// ✅ 正确 - 使用 TODO 标记待办事项
// TODO: 添加缓存层以提高性能
function getUser(id) {
  return fetch(`/api/users/${id}`);
}

// ✅ 正确 - 使用 FIXME 标记需要修复的问题
// FIXME: 这里存在潜在的内存泄漏问题，需要添加清理逻辑
let cache = new Map();
function cacheData(key, value) {
  cache.set(key, value);
}

// ✅ 正确 - 使用 HACK 标记临时解决方案
// HACK: 临时绕过第三方库的 bug，等待库更新后移除
function workaround(input) {
  return input.replace(/%20/g, '+');
}
```

## 禁止的注释

### 版本控制信息

```javascript
// ❌ 错误 - 包含作者、日期等版本控制信息
// Author: John Doe
// Date: 2024-01-01
// Modified: 2024-01-15
// Reviewed by: Jane Smith
function getUser(id) {
  return fetch(`/api/users/${id}`);
}

// ✅ 正确 - 不包含版本控制信息
function getUser(id) {
  return fetch(`/api/users/${id}`);
}
```

### 注释显而易见的代码

```javascript
// ❌ 错误 - 注释重复代码
// 增加计数器
count++;

// 获取用户
const user = getUser(1);

// 检查错误
if (error) {
  throw error;
}

// ✅ 正确 - 代码本身已经很清楚
count++;
const user = getUser(1);
if (error) {
  throw error;
}
```

## 注释最佳实践

### 复杂逻辑需要注释

```javascript
// ✅ 正确 - 为正则表达式添加注释
// 匹配邮箱地址：要求 @ 符号前后都有字符，且域名包含点
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ✅ 正确 - 为魔法数字添加注释
// 默认超时 5 秒，平衡用户体验和服务器负载
const DEFAULT_TIMEOUT = 5000;

// ✅ 正确 - 为设计决策添加注释
// 使用 Intl.NumberFormat 而非 toLocaleString()，因为：
// 1. 性能更好（可复用实例）
// 2. 更精细的控制
// 3. 一致的跨浏览器行为
const numberFormatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
});
```

### 保持注释与代码同步

```javascript
// ❌ 错误 - 注释与代码不一致
// 返回所有活跃用户
function getAllUsers() {
  return db.users.filter({ deleted: false });
}

// ✅ 正确 - 注释与代码一致
// 返回所有未删除的用户
function getAllUsers() {
  return db.users.filter({ deleted: false });
}
```

## 注释格式

### JSDoc 标签

```javascript
/**
 * 函数说明
 * @param {类型} 参数名 - 参数说明
 * @returns {类型} 返回值说明
 * @throws {错误类型} 错误说明
 * @example
 * // 使用示例
 * const result = functionName(arg1, arg2);
 */

/**
 * 回调函数类型
 * @callback CallbackName
 * @param {类型} 参数名 - 参数说明
 * @returns {类型} 返回值说明
 */

/**
 * 自定义类型
 * @typedef {Object} CustomType
 * @property {类型} 属性名 - 属性说明
 * @property {类型} 属性名 - 属性说明
 */
```

## 检查清单

提交代码前，确保：

- [ ] 所有导出函数有 JSDoc 注释
- [ ] 所有导出类有 JSDoc 注释
- [ ] 所有导出常量有 JSDoc 注释
- [ ] 注释说明"是什么"和"为什么"
- [ ] 注释与代码一致
- [ ] 没有注释显而易见的代码
- [ ] 没有版本控制信息（作者、日期）
- [ ] TODO/FIXME 有明确的描述
- [ ] 复杂逻辑有注释说明
