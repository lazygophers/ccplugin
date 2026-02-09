# TypeScript 代码审查规范

## 核心原则

### ✅ 必须遵守

1. **审查所有变更** - 没有例外
2. **关注代码质量** - 不仅是功能正确性
3. **提供建设性反馈** - 具体的改进建议
4. **保持友好** - 审查是学习过程
5. **及时响应** - 尽快完成审查

### ❌ 禁止行为

- 仅审查代码风格（让工具处理）
- 批评开发者而非代码
- 忽略审查请求
- 模糊的反馈（"看起来不对"）

## 审查原则

### 审查重点

1. **功能正确性** - 代码是否实现预期功能
2. **类型安全** - 是否正确使用 TypeScript 类型系统
3. **代码可读性** - 代码是否清晰易懂
4. **可维护性** - 未来是否容易修改
5. **性能考虑** - 是否有明显的性能问题
6. **测试覆盖** - 是否有足够的测试
7. **错误处理** - 是否正确处理错误情况

### 审查顺序

```
1. 理解变更的目的
   - 阅读 PR 描述
   - 查看相关的 Issue
   - 理解变更的上下文

2. 审查设计
   - 设计是否合理
   - 是否有更简单的方案
   - 是否符合项目架构

3. 审查实现
   - 代码是否正确
   - 类型是否安全
   - 错误处理是否完善

4. 审查细节
   - 命名是否清晰
   - 注释是否必要
   - 代码格式是否正确

5. 提供反馈
   - 指出问题
   - 提供改进建议
   - 肯定好的做法
```

## 审查清单

### 功能性

```markdown
- [ ] 代码实现了 PR 描述的功能
- [ ] 代码处理了边界情况
- [ ] 错误处理正确且完善
- [ ] 没有明显的 bug
- [ ] 没有引入安全问题
```

### 类型安全

```markdown
- [ ] 没有使用 `any` 类型
- [ ] 没有使用 `@ts-ignore`
- [ ] 使用了类型守卫而非类型断言
- [ ] 正确使用了泛型
- [ ] 类型定义清晰且合理
```

### 代码质量

```markdown
- [ ] 代码可读性强
- [ ] 命名清晰且一致
- [ ] 没有重复代码
- [ ] 函数职责单一
- [ ] 没有过长的函数（超过 50 行）
```

### 测试

```markdown
- [ ] 新功能有对应的测试
- [ ] 测试覆盖核心逻辑
- [ ] 测试命名清晰
- [ ] 测试使用 AAA 模式
- [ ] 外部依赖已正确 Mock
```

### 文档

```markdown
- [ ] 公开 API 有 JSDoc
- [ ] 复杂逻辑有注释
- [ ] README 更新了（如需要）
- [ ] CHANGELOG 更新了（如需要）
```

## 常见问题

### 类型安全

```typescript
// ❌ 问题：使用 any 类型
function process(data: any) {
  return data.value;
}

// ✅ 建议：使用具体类型或泛型
function process<T extends { value: unknown }>(data: T) {
  return data.value;
}

// ❌ 问题：类型断言绕过检查
const user = data as User;

// ✅ 建议：使用类型守卫
function isUser(data: unknown): data is User {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'name' in data
  );
}
```

### 错误处理

```typescript
// ❌ 问题：单行错误处理
if (err) return err;

// ✅ 建议：多行处理，记录日志
try {
  await operation();
} catch (error) {
  console.error('error:', error);
  throw error;
}

// ❌ 问题：忽略 Promise 错误
fetchUser(userId).then(user => processUser(user));

// ✅ 建议：处理错误
fetchUser(userId)
  .then(user => processUser(user))
  .catch(error => {
    console.error('error:', error);
    handleError(error);
  });
```

### 命名

```typescript
// ❌ 问题：不清晰的命名
function d(u: string) { }
const x = getData();

// ✅ 建议：使用描述性名称
function deleteUser(userId: string) { }
const user = getUser();
```

### React 组件

```typescript
// ❌ 问题：使用 any 类型
interface Props {
  data: any;
}

// ✅ 建议：定义具体类型
interface Props {
  data: UserData[];
}

// ❌ 问题：缺少依赖项
useEffect(() => {
  fetchData(userId);
}, []);

// ✅ 建议：包含所有依赖
useEffect(() => {
  fetchData(userId);
}, [userId]);
```

## 反馈模板

### 建设性反馈

```markdown
### 类型安全

建议：
```typescript
// 当前
function validate(data: unknown): boolean {
  return typeof data === 'object' && data !== null;
}

// 改进
function isRecord(data: unknown): data is Record<string, unknown> {
  return typeof data === 'object' && data !== null;
}
```

使用类型守卫可以在后续代码中获得类型信息。

### 错误处理

当前代码忽略了一些错误情况。建议使用 Result 类型处理可能失败的操作：

```typescript
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: Error };
```

这样可以让错误处理更加明确。

### 命名

函数名 `d` 不够清晰，建议改为 `deleteUser` 以更好地表达意图。
```

### 赞扬良好实践

```markdown
### 亮点

- 很好地使用了 Zod 进行运行时验证
- 组件拆分得很合理，职责单一
- 测试覆盖充分，使用了参数化测试
- 类型定义清晰，使用了 Discriminated Union
```

## 审查工作流

### PR 审查步骤

```bash
# 1. 同步分支
git checkout main
git pull origin main

# 2. 检出 PR 分支
git checkout feature/branch-name
git pull origin feature/branch-name

# 3. 运行项目
pnpm install
pnpm typecheck
pnpm lint
pnpm test

# 4. 在 GitHub/GitLab 上进行审查
# 5. 提供反馈或批准
```

### 审查响应时间

```markdown
- 紧急修复：1 小时内响应
- 功能 PR：1 个工作日内响应
- 重构 PR：2 个工作日内响应
```

## 检查清单

完成审查前，确保：

- [ ] 理解了 PR 的目的
- [ ] 审查了所有变更的文件
- [ ] 在本地运行过代码
- [ ] 提供了具体的反馈
- [ ] 指出了好的实践
- [ ] 没有遗留审查评论
