/**
 * JavaScript 错误处理示例
 *
 * 本文件展示了错误处理的正确和错误方式对比。
 * 遵循 javascript-skills/coding-standards/error-handling.md 规范。
 */

// =============================================================================
// 1. 基本错误处理
// =============================================================================

// ✅ 正确 - 多行处理 + 统一日志格式
async function fetchUserCorrect(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', {
      message: error.message,
      stack: error.stack,
      userId,
    });
    throw error;  // 重新抛出，让调用者处理
  }
}

// ❌ 错误 - 静默失败
async function fetchUserBadSilent(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    return await response.json();
  } catch (error) {
    // 静默忽略 - 调用者不知道发生了什么
  }
}

// ❌ 错误 - 不处理错误
async function fetchUserBadNoHandle(userId) {
  const response = await fetch(`/api/users/${userId}`);
  return await response.json();
}

// =============================================================================
// 2. 自定义错误类
// =============================================================================

// ✅ 正确 - 自定义错误类
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

class NotFoundError extends Error {
  constructor(resource, identifier) {
    super(`${resource} with identifier '${identifier}' not found`);
    this.name = 'NotFoundError';
    this.resource = resource;
    this.identifier = identifier;
  }
}

// 使用自定义错误的示例
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('Invalid email format', 'email');
  }
  return true;
}

function validatePassword(password) {
  if (!password || password.length < 8) {
    throw new ValidationError('Password must be at least 8 characters', 'password');
  }
  return true;
}

// =============================================================================
// 3. API 错误处理
// =============================================================================

// ✅ 正确 - 统一的 API 错误处理
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

// 使用示例
async function loadUserData(userId) {
  try {
    const user = await apiRequest(`/api/users/${userId}`);
    return user;
  } catch (error) {
    if (error.status === 404) {
      console.error('User not found');
      return null;
    }
    if (error.status === 401) {
      console.error('Unauthorized - redirecting to login');
      redirectToLogin();
      return null;
    }
    console.error('Failed to load user:', error.message);
    return null;
  }
}

// =============================================================================
// 4. 表单验证错误
// =============================================================================

// ✅ 正确 - 表单验证错误处理
class FormValidationError extends Error {
  constructor(errors) {
    super('Validation failed');
    this.name = 'FormValidationError';
    this.errors = errors;  // { field: message }
  }
}

function validateLoginForm(formData) {
  const errors = {};

  // 验证邮箱
  if (!formData.email) {
    errors.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = 'Invalid email format';
  }

  // 验证密码
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

// =============================================================================
// 5. Promise.allSettled 处理多个异步操作
// =============================================================================

// ✅ 正确 - 使用 allSettled 处理多个请求
async function fetchAllDataCorrect() {
  const results = await Promise.allSettled([
    fetch('/api/users').then(r => r.json()),
    fetch('/api/posts').then(r => r.json()),
    fetch('/api/comments').then(r => r.json()),
  ]);

  const data = {
    users: results[0].status === 'fulfilled' ? results[0].value : null,
    posts: results[1].status === 'fulfilled' ? results[1].value : null,
    comments: results[2].status === 'fulfilled' ? results[2].value : null,
  };

  // 记录失败的请求
  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      const endpoints = ['users', 'posts', 'comments'];
      console.error(`Failed to fetch ${endpoints[index]}:`, result.reason);
    }
  });

  return data;
}

// ❌ 错误 - 使用 Promise.all（一个失败全部失败）
async function fetchAllDataBad() {
  const results = await Promise.all([
    fetch('/api/users').then(r => r.json()),    // 如果这个失败，全部失败
    fetch('/api/posts').then(r => r.json()),
    fetch('/api/comments').then(r => r.json()),
  ]);
  return results;
}

// =============================================================================
// 6. 错误边界（React）
// =============================================================================

// ✅ 正确 - 错误边界组件
class ErrorBoundary {
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
        '<div class="error-fallback">' +
          '<h2>Something went wrong</h2>' +
          `<p>${this.state.error?.message || 'Unknown error'}</p>` +
          '<button onclick="this.parentElement.remove()">Try again</button>' +
        '</div>'
      );
    }
    return this.props.children;
  }
}

// =============================================================================
// 7. 带重试的错误处理
// =============================================================================

// ✅ 正确 - 带重试的请求
async function fetchWithRetry(url, maxRetries = 3, delay = 1000) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      lastError = error;
      const waitTime = delay * Math.pow(2, attempt);  // 指数退避

      console.warn(`Attempt ${attempt + 1} failed, retrying in ${waitTime}ms`);

      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  console.error('All retries exhausted:', lastError);
  throw lastError;
}

// =============================================================================
// 8. 超时控制
// =============================================================================

// ✅ 正确 - 带超时的请求
async function fetchWithTimeout(url, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

// =============================================================================
// 运行示例
// =============================================================================

// 模拟重定向到登录页
function redirectToLogin() {
  console.log('Redirecting to login...');
}

// 测试验证函数
function testValidation() {
  console.log('\n=== 测试验证函数 ===');

  // 测试邮箱验证
  try {
    validateEmail('invalid-email');
  } catch (error) {
    console.log('Email validation caught:', error.message, '- Field:', error.field);
  }

  // 测试密码验证
  try {
    validatePassword('short');
  } catch (error) {
    console.log('Password validation caught:', error.message, '- Field:', error.field);
  }

  // 测试表单验证
  try {
    validateLoginForm({ email: 'invalid', password: 'short' });
  } catch (error) {
    console.log('Form validation caught:', error.name);
    console.log('Errors:', error.errors);
  }
}

// 测试 API 错误处理
async function testApiError() {
  console.log('\n=== 测试 API 错误处理 ===');

  try {
    // 模拟失败的请求
    await fetchUserCorrect(999);
  } catch (error) {
    console.log('API error handled correctly');
  }
}

// 主函数
async function main() {
  console.log('JavaScript 错误处理示例');
  console.log('========================\n');

  testValidation();
  await testApiError();

  console.log('\n=== 示例完成 ===');
  console.log('✅ 所有错误处理示例已演示');
}

// 导出函数供测试使用
export {
  ValidationError,
  AuthenticationError,
  NetworkError,
  NotFoundError,
  ApiError,
  FormValidationError,
  validateEmail,
  validatePassword,
  validateLoginForm,
  apiRequest,
  fetchWithRetry,
  fetchWithTimeout,
  fetchAllDataCorrect,
};

// 运行示例（在浏览器中）
if (typeof window !== 'undefined') {
  main().catch(console.error);
}
