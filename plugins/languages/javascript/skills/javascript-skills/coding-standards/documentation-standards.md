# JavaScript 文档规范

## 核心原则

### 必须遵守

1. **README 完整** - 项目必须有 README.md
2. **API 文档** - 公开 API 必须有 JSDoc 文档
3. **代码注释** - 导出函数和类必须有 JSDoc 注释
4. **文档更新** - 代码变更时同步更新文档
5. **文档清晰** - 文档简洁明了，易于理解

### 禁止行为

- 缺少 README.md
- 公开 API 无文档
- 注释与代码不一致
- 文档包含过时信息
- 文档过于冗长

## README 规范

### README 结构

```markdown
# 项目名称

简短描述项目的主要功能和用途。

## 功能特性

- 功能 1：描述
- 功能 2：描述
- 功能 3：描述

## 快速开始

### 安装

\`\`\`bash
# 使用 pnpm（推荐）
pnpm install

# 或使用 npm
npm install
\`\`\`

### 使用

\`\`\`javascript
import { getUser } from 'my-project';

const user = await getUser(123);
console.log(user);
\`\`\`

## 项目结构

\`\`\`
src/
├── features/
│   ├── auth/
│   └── dashboard/
├── shared/
│   ├── hooks/
│   ├── utils/
│   └── components/
└── main.js
\`\`\`

## 开发指南

### 环境要求

- Node.js 22 LTS 或更高版本
- pnpm 9 或更高版本

### 运行项目

\`\`\`bash
# 开发模式
pnpm dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
\`\`\`

### 运行测试

\`\`\`bash
# 运行所有测试
pnpm test

# 运行测试并生成覆盖率报告
pnpm test:coverage
\`\`\`

## API 文档

详见 [API 文档](docs/api.md)

## 贡献指南

详见 [贡献指南](CONTRIBUTING.md)

## 许可证

MIT License
\`\`\`
```

### README 最佳实践

```markdown
# ✅ 正确 - 清晰的 README

# MyProject

一个现代化的 JavaScript 工具库，提供实用的工具函数和组件。

## 功能特性

- **类型安全**：完整的 TypeScript 类型定义
- **模块化**：按需导入，tree-shaking 友好
- **高性能**：优化的算法和数据结构
- **易用性**：简洁的 API 设计

## 快速开始

### 安装

\`\`\`bash
pnpm add my-project
\`\`\`

### 使用

\`\`\`javascript
import { debounce, formatDate } from 'my-project';

// 防抖函数
const handler = debounce(() => console.log('Hello'), 300);

// 格式化日期
const date = formatDate(new Date(), 'YYYY-MM-DD');
\`\`\`

# ❌ 错误 - 不完整的 README

# MyProject

JavaScript 项目。
```

## API 文档

### API 文档结构

```markdown
# API 文档

## 用户 API

### 获取用户

**描述**

根据用户 ID 获取用户信息。

**请求**

\`\`\`javascript
GET /api/users/:id
\`\`\`

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| ------ | ---- | ---- | ---- |
| id | number | 是 | 用户 ID |

**查询参数**

| 参数名 | 类型 | 必填 | 说明 |
| ------ | ---- | ---- | ---- |
| includePosts | boolean | 否 | 是否包含用户帖子 |
| includeFriends | boolean | 否 | 是否包含好友列表 |

**响应**

\`\`\`javascript
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "posts": [],
  "friends": []
}
\`\`\`

**错误码**

| 错误码 | 说明 |
| ------ | ---- |
| 404 | 用户不存在 |
| 401 | 未授权访问 |

**示例**

\`\`\`javascript
const response = await fetch('/api/users/123?includePosts=true');
const user = await response.json();
\`\`\`
```

### API 文档最佳实践

```markdown
# ✅ 正确 - 完整的 API 文档

## 用户 API

### 获取用户信息

\`\`\`javascript
getUser(id: number, options?: GetUserOptions): Promise<User>
\`\`\`

根据用户 ID 获取用户信息，可选择性包含用户的帖子和好友列表。

**参数**

- `id` (number): 用户 ID，必须大于 0
- `options` (GetUserOptions, 可选):
  - `includePosts` (boolean): 是否包含用户帖子，默认 false
  - `includeFriends` (boolean): 是否包含好友列表，默认 false

**返回值**

Promise<User>：用户信息对象

**抛出异常**

- `NotFoundError`: 用户不存在
- `ValidationError`: 参数验证失败

**示例**

\`\`\`javascript
// 基本用法
const user = await getUser(123);

// 包含帖子
const userWithPosts = await getUser(123, { includePosts: true });
\`\`\`

# ❌ 错误 - 不完整的 API 文档

## 获取用户

\`\`\`javascript
getUser(id)
\`\`\`

获取用户。
```

## 代码注释

### JSDoc 注释

```javascript
// ✅ 正确 - 导出函数必须有 JSDoc
/**
 * 异步获取用户信息
 *
 * @param {number} userId - 用户 ID
 * @param {Object} options - 配置选项
 * @param {boolean} [options.includePosts=false] - 是否包含用户帖子
 * @returns {Promise<User>} 用户信息对象
 * @throws {NotFoundError} 用户不存在时抛出
 *
 * @example
 * const user = await fetchUser(123, { includePosts: true });
 */
async function fetchUser(userId, options = {}) {
  const { includePosts = false } = options;
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
```

### 类文档注释

```javascript
// ✅ 正确 - 完整的类文档
/**
 * 用户管理器
 *
 * 负责用户的增删改查操作，提供缓存的用户数据获取。
 *
 * @class UserManager
 * @example
 * const manager = new UserManager(apiClient);
 * const user = await manager.getById(1);
 */
class UserManager {
  /**
   * 创建用户管理器实例
   * @param {ApiClient} apiClient - API 客户端实例
   */
  constructor(apiClient) {
    this.apiClient = apiClient;
    this.cache = new Map();
  }

  /**
   * 根据 ID 获取用户（带缓存）
   * @param {number} id - 用户 ID
   * @returns {Promise<User>} 用户对象
   */
  async getById(id) {
    if (this.cache.has(id)) {
      return this.cache.get(id);
    }
    const user = await this.apiClient.get(`/users/${id}`);
    this.cache.set(id, user);
    return user;
  }
}

// ❌ 错误 - 缺少类文档
class UserManager {
  constructor(apiClient) {
    this.apiClient = apiClient;
  }
}
```

## 文档最佳实践

### 文档更新

```javascript
// ✅ 正确 - 代码变更时同步更新注释
/**
 * 获取用户列表
 *
 * @deprecated 使用 {@link getUsersPaginated} 替代
 * 将在 v2.0 版本中移除
 *
 * @param {number} [limit=10] - 返回数量限制
 * @returns {Promise<User[]>} 用户列表
 */
function getUsers(limit = 10) {
  return fetch(`/api/users?limit=${limit}`).then(r => r.json());
}

/**
 * 分页获取用户列表
 *
 * @param {Object} options - 分页选项
 * @param {number} [options.page=1] - 页码
 * @param {number} [options.pageSize=10] - 每页数量
 * @returns {Promise<PaginatedResponse<User>>} 分页用户数据
 */
function getUsersPaginated(options = {}) {
  const { page = 1, pageSize = 10 } = options;
  return fetch(`/api/users?page=${page}&pageSize=${pageSize}`)
    .then(r => r.json());
}

// ❌ 错误 - 代码变更但注释未更新
/**
 * 获取用户列表
 */
function getUsers() {
  // 实际上这个函数已经改为分页获取
  return fetch('/api/users?page=1&pageSize=10').then(r => r.json());
}
```

### 文档清晰

```markdown
# ✅ 正确 - 清晰的文档

## 安装依赖

使用以下命令安装项目依赖：

\`\`\`bash
pnpm install
\`\`\`

# ❌ 错误 - 不清晰的文档

## 安装

你可以通过运行 pnpm install 命令来安装这个项目的依赖，安装完成后就可以使用了。
```

## 组件文档（React/Vue）

### React 组件文档

```jsx
/**
 * UserCard 组件
 *
 * 展示用户信息的卡片组件，支持编辑和删除操作。
 *
 * @component
 * @param {Object} props - 组件属性
 * @param {User} props.user - 用户数据
 * @param {Function} [props.onEdit] - 编辑回调函数
 * @param {Function} [props.onDelete] - 删除回调函数
 * @param {boolean} [props.showActions=true] - 是否显示操作按钮
 * @returns {JSX.Element} 用户卡片组件
 *
 * @example
 * <UserCard
 *   user={userData}
 *   onEdit={(id) => console.log('Edit:', id)}
 *   onDelete={(id) => console.log('Delete:', id)}
 * />
 */
export function UserCard({ user, onEdit, onDelete, showActions = true }) {
  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      {showActions && (
        <div className="actions">
          <button onClick={() => onEdit(user.id)}>编辑</button>
          <button onClick={() => onDelete(user.id)}>删除</button>
        </div>
      )}
    </div>
  );
}
```

### Vue 组件文档

```vue
<script>
/**
 * UserCard 组件
 *
 * 展示用户信息的卡片组件，支持编辑和删除操作。
 *
 * @component
 * @props {User} user - 用户数据
 * @props {Function} [onEdit] - 编辑回调函数
 * @props {Function} [onDelete] - 删除回调函数
 * @props {boolean} [showActions=true] - 是否显示操作按钮
 *
 * @example
 * <UserCard
 *   :user="userData"
 *   :on-edit="handleEdit"
 *   :on-delete="handleDelete"
 * />
 */
export default {
  name: 'UserCard',
  props: {
    user: {
      type: Object,
      required: true,
    },
    onEdit: Function,
    onDelete: Function,
    showActions: {
      type: Boolean,
      default: true,
    },
  },
};
</script>
```

## 检查清单

提交代码前，确保：

- [ ] 项目有 README.md
- [ ] README.md 包含项目描述、功能特性、快速开始
- [ ] 公开 API 有 JSDoc 文档
- [ ] API 文档包含参数、返回值、异常、示例
- [ ] 导出类有 JSDoc 注释
- [ ] 导出函数有 JSDoc 注释
- [ ] 注释与代码一致
- [ ] 文档清晰易懂
- [ ] 文档无过时信息
- [ ] 代码变更时同步更新文档
