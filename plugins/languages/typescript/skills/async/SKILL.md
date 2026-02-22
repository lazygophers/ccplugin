---
name: async
description: TypeScript 异步编程规范：async/await、Promise、错误处理。处理异步代码时必须加载。
---

# TypeScript 异步编程规范

## 相关 Skills

| 场景     | Skill        | 说明              |
| -------- | ------------ | ----------------- |
| 核心规范 | Skills(core) | TS 5.9+、严格模式 |

## async/await

```typescript
// ✅ 正确
async function getUser(id: string): Promise<User> {
	try {
		const response = await fetch(`/api/users/${id}`);
		if (!response.ok) {
			throw new Error(`HTTP ${response.status}`);
		}
		return response.json();
	} catch (error) {
		console.error("error:", error);
		throw error;
	}
}

// ❌ 禁止
if (err) return err; // 单行错误处理
```

## 并发处理

```typescript
// ✅ Promise.all
const users = await Promise.all([getUser("1"), getUser("2"), getUser("3")]);

// ✅ Promise.allSettled
const results = await Promise.allSettled([fetchUser(), fetchPosts()]);

// ✅ Promise.race
const result = await Promise.race([fetchWithTimeout(url, 5000), timeout(5000)]);
```

## 错误处理

```typescript
// ✅ 正确 - 多行处理
try {
	const data = await fetchData();
	return data;
} catch (error) {
	console.error("error:", error);
	throw error;
}

// ❌ 禁止 - 单行 if
if (err) return err;
```

## 检查清单

- [ ] 使用 async/await
- [ ] 多行错误处理
- [ ] 使用 Promise.all 并发
- [ ] 设置超时控制
