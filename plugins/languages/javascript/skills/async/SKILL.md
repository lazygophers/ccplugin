---
name: async
description: JavaScript 异步编程规范：async/await、Promise、错误处理。处理异步代码时必须加载。
---

# JavaScript 异步编程规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | ES2024-2025 标准、强制约定 |

## async/await

```javascript
// ✅ 推荐
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    return await response.json();
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// ❌ 禁止
async function fetchData() {
  const response = await fetch('/api/data');
  return await response.json();
}
```

## Promise 并行

```javascript
// ✅ Promise.allSettled
const results = await Promise.allSettled([
  fetchUser(),
  fetchPosts(),
  fetchComments()
]);

// ✅ Promise.all（全部成功）
const [user, posts] = await Promise.all([
  fetchUser(),
  fetchPosts()
]);
```

## 超时控制

```javascript
async function fetchWithTimeout(url, timeout = 5000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}
```

## 检查清单

- [ ] 所有 await 有 try-catch
- [ ] 使用 Promise.allSettled 处理并行
- [ ] 设置超时控制
- [ ] 使用 AbortController 取消请求
