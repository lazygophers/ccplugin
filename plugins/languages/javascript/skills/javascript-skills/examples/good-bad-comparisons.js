/**
 * JavaScript 代码对比示例（Good vs Bad）
 *
 * 本文件展示了符合规范和不符合规范的代码对比。
 * 遵循 javascript-skills/* 规范。
 */

// =============================================================================
// 1. 命名规范
// =============================================================================

// ✅ Good - 清晰的命名
const MAX_RETRY_ATTEMPTS = 3;
const API_BASE_URL = 'https://api.example.com';

const isActive = true;
const hasChildren = false;
const isLoading = true;

function getUserById(userId) {
  return fetch(`/api/users/${userId}`);
}

async function fetchUserPosts(userId) {
  const response = await fetch(`/api/users/${userId}/posts`);
  return response.json();
}

class UserManager {
  async getUser(id) {
    return fetch(`/api/users/${id}`).then(r => r.json());
  }
}

// ❌ Bad - 不清晰的命名
const max_retry_attempts = 3;  // 应该 UPPER_SNAKE_CASE
const apiBaseUrl = 'https://api.example.com';  // 应该 UPPER_SNAKE_CASE

const active = true;  // 缺少 is 前缀
const children = false;  // 缺少 has 前缀
const loading = true;  // 缺少 is 前缀

function user(id) {  // 动词不明确
  return fetch(`/api/users/${id}`).then(r => r.json());
}

function data() {  // 完全没有描述性
  return fetch('/api/data').then(r => r.json());
}

class user_manager {  // 应该 PascalCase
  get_user(id) {  // 应该 camelCase
    return fetch(`/api/users/${id}`).then(r => r.json());
  }
}

// =============================================================================
// 2. 变量声明
// =============================================================================

// ✅ Good - 使用 const/let
const config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
};

let currentPage = 1;
const itemsPerPage = 20;

// ❌ Bad - 使用 var
var config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
};
var currentPage = 1;  // var 有函数作用域问题

// =============================================================================
// 3. 异步编程
// =============================================================================

// ✅ Good - async/await + 错误处理
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

// ✅ Good - Promise.allSettled
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

// ❌ Bad - 不处理错误
async function fetchUserDataBad(userId) {
  const response = await fetch(`/api/users/${userId}`);
  return await response.json();  // 没有错误处理
}

// ❌ Bad - Promise.all（一个失败全部失败）
async function fetchAllDataBad() {
  const results = await Promise.all([
    fetchUsers(),    // 如果这个失败，全部失败
    fetchPosts(),
    fetchComments(),
  ]);
  return results;
}

// ❌ Bad - 回调地狱
function fetchUserDataBad(userId, callback) {
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

// =============================================================================
// 4. 函数定义
// =============================================================================

// ✅ Good - 函数声明有注释
/**
 * 计算折扣后价格
 * @param {number} originalPrice - 原价
 * @param {number} discountRate - 折扣率（0-1）
 * @returns {number} 折后价格
 */
function calculateDiscountPrice(originalPrice, discountRate) {
  if (discountRate < 0 || discountRate > 1) {
    throw new Error('Discount rate must be between 0 and 1');
  }
  return originalPrice * (1 - discountRate);
}

// ✅ Good - 箭头函数用于简单操作
const double = (x) => x * 2;
const add = (a, b) => a + b;

// ❌ Bad - 没有注释
function calcPrice(p, d) {
  return p * (1 - d);
}

// ❌ Bad - 过于复杂的箭头函数
const processData = (data) => {
  const result = [];
  for (const item of data) {
    if (item.active) {
      const transformed = {
        id: item.id,
        name: item.name.toUpperCase(),
        value: item.value * 2,
      };
      result.push(transformed);
    }
  }
  return result;
};

// =============================================================================
// 5. 对象和数组操作
// =============================================================================

// ✅ Good - 使用展开运算符
const user = { name: 'Alice', age: 25 };
const updatedUser = { ...user, age: 26 };

const items = [1, 2, 3];
const newItems = [...items, 4];

// ✅ Good - 使用解构
const { name, age } = user;
const [first, ...rest] = items;

// ❌ Bad - 直接修改
const userBad = { name: 'Alice', age: 25 };
userBad.age = 26;  // 直接修改

const itemsBad = [1, 2, 3];
itemsBad.push(4);  // 直接修改

// =============================================================================
// 6. 条件语句
// =============================================================================

// ✅ Good - 清晰的条件
function getDiscount(user) {
  if (!user) {
    return 0;
  }

  if (user.isPremium) {
    return 0.2;
  }

  if (user.hasLoyaltyCard) {
    return 0.1;
  }

  return 0;
}

// ✅ Good - 早期返回
function validateUser(user) {
  if (!user) {
    throw new Error('User is required');
  }

  if (!user.email) {
    throw new Error('Email is required');
  }

  if (!user.password) {
    throw new Error('Password is required');
  }

  return true;
}

// ❌ Bad - 嵌套过深
function getDiscountBad(user) {
  if (user) {
    if (user.isPremium) {
      return 0.2;
    } else {
      if (user.hasLoyaltyCard) {
        return 0.1;
      } else {
        return 0;
      }
    }
  }
  return 0;
}

// =============================================================================
// 7. 模块导出
// =============================================================================

// ✅ Good - 具名导出（推荐）
export const API_BASE_URL = 'https://api.example.com';
export async function fetchUser(id) {
  return fetch(`${API_BASE_URL}/users/${id}`);
}
export function formatDate(date) {
  return new Date(date).toLocaleDateString();
}

// ✅ Good - 默认导出仅用于主要功能
export default class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async get(path) {
    return fetch(`${this.baseUrl}${path}`);
  }
}

// ❌ Bad - 混合导出
export const API_BASE_URL = 'https://api.example.com';
export default {
  fetchUser(id) { },
  formatDate(date) { },
};

// ❌ Bad - 默认导出对象（难以 tree-shaking）
export default {
  getUser(id) { },
  createUser(data) { },
  updateUser(id, data) { },
  deleteUser(id) { },
};

// =============================================================================
// 8. 错误处理
// =============================================================================

// ✅ Good - 自定义错误类
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

// 使用自定义错误
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('Invalid email format', 'email');
  }
}

// ❌ Bad - 使用通用 Error
function validateEmailBad(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email');  // 太笼统
  }
}

// =============================================================================
// 9. 字符串处理
// =============================================================================

// ✅ Good - 使用模板字符串
function greet(name, timeOfDay) {
  return `Good ${timeOfDay}, ${name}!`;
}

function buildUrl(baseUrl, path, params) {
  const queryString = new URLSearchParams(params).toString();
  return `${baseUrl}${path}?${queryString}`;
}

// ❌ Bad - 使用字符串拼接
function greetBad(name, timeOfDay) {
  return 'Good ' + timeOfDay + ', ' + name + '!';
}

function buildUrlBad(baseUrl, path, params) {
  return baseUrl + path + '?param=' + params.param;  // 不安全
}

// =============================================================================
// 10. 数组方法
// =============================================================================

// ✅ Good - 使用数组方法
const numbers = [1, 2, 3, 4, 5];

const doubled = numbers.map(n => n * 2);
const evens = numbers.filter(n => n % 2 === 0);
const sum = numbers.reduce((acc, n) => acc + n, 0);
const hasEven = numbers.some(n => n % 2 === 0);
const allPositive = numbers.every(n => n > 0);

// ❌ Bad - 使用 for 循环
const doubledBad = [];
for (let i = 0; i < numbers.length; i++) {
  doubledBad.push(numbers[i] * 2);
}

// =============================================================================
// 11. 代码组织
// =============================================================================

// ✅ Good - 按功能组织
// users.js

// ====== 类型定义 ======
/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

// ====== 常量 ======
const USER_API_BASE = '/api/users';

// ====== 工具函数 ======
/**
 * 验证用户数据
 */
function validateUser(user) {
  return !!(user && user.name && user.email);
}

/**
 * 格式化用户显示名称
 */
function formatUserName(user) {
  return user.name.trim();
}

// ====== API 函数 ======
/**
 * 获取用户列表
 */
async function fetchUsers() {
  const response = await fetch(USER_API_BASE);
  return response.json();
}

/**
 * 创建新用户
 */
async function createUser(userData) {
  const response = await fetch(USER_API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  return response.json();
}

// ====== 导出 ======
export { fetchUsers, createUser, validateUser, formatUserName };

// ❌ Bad - 混乱的组织
let users = [];
const url = '/api/users';

function getData() {
  fetch(url).then(r => r.json()).then(data => {
    users = data;
  });
}

function check() {
  return users.length > 0;
}

const API = url;

class Manager {
  constructor() {
    this.url = url;
  }
}

export { Manager, check, getData };

// =============================================================================
// 导出总结
// =============================================================================

/**
 * Good vs Bad 对比总结
 *
 * ✅ Good Practices:
 * - 使用 const/let 而非 var
 * - 使用 camelCase, PascalCase, UPPER_SNAKE_CASE 命名
 * - 使用 async/await 而非回调
 * - 使用 Promise.allSettled 处理多个异步操作
 * - 函数有 JSDoc 注释
 * - 使用展开运算符而非直接修改对象
 * - 早期返回简化条件逻辑
 * - 使用自定义错误类
 * - 使用模板字符串
 * - 使用数组方法而非 for 循环
 * - 按功能组织代码
 *
 * ❌ Bad Practices:
 * - 使用 var 声明变量
 * - 命名不清晰或不符合约定
 * - 回调地狱
 * - 不处理错误
 * - 没有注释
 * - 直接修改对象和数组
 * - 嵌套过深的条件语句
 * - 使用通用 Error
 * - 字符串拼接
 * - 代码组织混乱
 */
