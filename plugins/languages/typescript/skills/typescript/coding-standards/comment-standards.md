# TypeScript 注释规范

## 核心原则

### ✅ 必须遵守

1. **注释解释"为什么"而非"是什么"** - 代码应该自解释
2. **使用 JSDoc** - 为公开 API 提供文档
3. **保持注释最新** - 代码变更时同步更新注释
4. **避免废话** - 不重复代码已表达的内容
5. **标记 TODO** - 使用 @todo 标记待办事项

### ❌ 禁止行为

- 注释显而易见的代码
- 过时的注释
- 使用注释"隐藏"糟糕的代码
- 大块注释掉的代码

## JSDoc 规范

### 函数文档

```typescript
/**
 * 获取用户信息。
 *
 * @param id - 用户 ID
 * @returns 用户对象，如果不存在则返回 null
 * @throws {ValidationError} 如果 ID 格式无效
 * @throws {NotFoundError} 如果用户不存在
 *
 * @example
 * ```ts
 * const user = await getUser('123');
 * if (user) {
 *   console.log(user.name);
 * }
 * ```
 */
async function getUser(id: string): Promise<User | null> {
  if (!isValidId(id)) {
    throw new ValidationError('Invalid ID format', 'id');
  }
  return userRepository.findById(id);
}

// ✅ 简单函数可以省略详细文档
function add(a: number, b: number): number {
  return a + b;
}
```

### 类型文档

```typescript
/**
 * 用户类型。
 *
 * @remarks
 * 包含用户的基本信息和状态。
 *
 * @example
 * ```ts
 * const user: User = {
 *   id: '123',
 *   name: 'John',
 *   email: 'john@example.com',
 *   status: 'active',
 * };
 * ```
 */
type User = {
  /** 用户唯一标识符 */
  id: string;

  /** 用户名称 */
  name: string;

  /** 用户邮箱 */
  email: string;

  /**
   * 用户状态。
   *
   * - `active`: 活跃用户
   * - `inactive`: 非活跃用户
   * - `suspended`: 已暂停用户
   */
  status: 'active' | 'inactive' | 'suspended';
};
```

### 类文档

```typescript
/**
 * 用户服务类。
 *
 * @remarks
 * 提供用户的 CRUD 操作和业务逻辑处理。
 *
 * @example
 * ```ts
 * const service = new UserRepository(apiClient);
 * const user = await service.findById('123');
 * ```
 */
class UserRepository {
  /**
   * 创建用户仓库实例。
   *
   * @param client - HTTP 客户端
   */
  constructor(private readonly client: HttpClient) {}

  /**
   * 根据 ID 查找用户。
   *
   * @param id - 用户 ID
   * @returns 用户对象，如果不存在则返回 null
   */
  async findById(id: string): Promise<User | null> {
    // ...
  }
}
```

## 注释原则

### 解释为什么

```typescript
// ✅ 好的注释 - 解释原因
// 使用 setTimeout 确保 UI 在状态更新后重新渲染
setTimeout(() => {
  scrollToBottom();
}, 0);

// ✅ 好的注释 - 解释非显而易见的决定
// 这里使用 while 而不是 for 因为需要动态修改索引
let i = 0;
while (i < items.length) {
  if (shouldRemove(items[i])) {
    items.splice(i, 1);
  } else {
    i++;
  }
}

// ❌ 坏的注释 - 重复代码
// 获取用户
const user = await getUser(id);

// 设置用户名称
user.name = 'John';
```

### 标记待办事项

```typescript
// ✅ 使用 @todo 标记待办事项
// @todo: 添加缓存以提高性能
async function getUser(id: string): Promise<User> {
  return userRepository.findById(id);
}

// ✅ 使用 @todo 标记已知问题
// @todo: 处理分页逻辑
function searchUsers(query: string): User[] {
  return users.filter(u => u.name.includes(query));
}

// ✅ 使用 FIXME 标记需要修复的问题
// FIXME: 这里应该使用更高效的算法
function sortItems(items: Item[]): Item[] {
  return items.sort((a, b) => a.value - b.value);
}
```

### 警告注释

```typescript
// ✅ 使用 WARNING 标记潜在危险
// WARNING: 此函数会修改原始数组，调用前请先克隆
function sortItems(items: Item[]): Item[] {
  return items.sort((a, b) => a.value - b.value);
}

// ✅ 使用注意标记重要事项
// NOTE: 这个 API 返回的是 UTC 时间，需要转换时区
const serverTime = await getServerTime();
```

## 禁止的注释

### 废弃代码

```typescript
// ❌ 禁止 - 大块注释掉的代码
// function oldGetUser(id: string): Promise<User> {
//   return fetch(`/api/users/${id}`).then(r => r.json());
// }

// ✅ 使用版本控制系统管理代码历史
// 删除的代码应该通过 git 恢复，而不是注释掉
```

### 显而易见的注释

```typescript
// ❌ 禁止 - 重复代码
// 创建用户
const user = new User();

// 设置用户名称
user.name = 'John';

// 返回用户
return user;

// ✅ 代码应该自解释
const user = new User();
user.name = 'John';
return user;
```

### 无用的注释

```typescript
// ❌ 禁止 - 无意义的注释
// 这是一个函数
function foo() {
  // 返回值
  return 42;
}

// ✅ 如果代码简单，不需要注释
function foo() {
  return 42;
}
```

## React 组件注释

### 组件文档

```typescript
/**
 * 用户头像组件。
 *
 * @remarks
 * 显示用户的头像图片，支持不同尺寸和回退方案。
 *
 * @example
 * ```tsx
 * <Avatar
 *   src="/avatars/user.jpg"
 *   alt="用户头像"
 *   size="large"
 * />
 * ```
 */
interface AvatarProps {
  /** 图片源地址 */
  src: string;

  /** 替代文本 */
  alt: string;

  /**
   * 头像尺寸。
   * @defaultValue "medium"
   */
  size?: 'small' | 'medium' | 'large';

  /** 回退组件（加载失败时显示） */
  fallback?: React.ReactNode;
}

export function Avatar({ src, alt, size = 'medium', fallback }: AvatarProps) {
  // ...
}
```

### Hook 注释

```typescript
/**
 * 用户状态 Hook。
 *
 * @remarks
 * 提供用户登录状态和认证方法的访问。
 *
 * @example
 * ```tsx
 * function ProfilePage() {
 *   const { user, login, logout } = useAuth();
 *   if (!user) return <Login onLogin={login} />;
 *   return <UserProfile user={user} onLogout={logout} />;
 * }
 * ```
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);

  // ...
}
```

## 检查清单

提交代码前，确保：

- [ ] 公开 API 有 JSDoc 文档
- [ ] 注释解释"为什么"而非"是什么"
- [ ] 没有注释掉的大块代码
- [ ] TODO 有 @todo 标记
- [ ] 警告有 WARNING 标记
- [ ] 注释与代码保持同步
- [ ] 没有显而易见的注释
