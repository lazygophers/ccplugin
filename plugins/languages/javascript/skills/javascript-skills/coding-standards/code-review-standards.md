# JavaScript 代码审查规范

## 核心原则

### 必须遵守

1. **代码质量** - 确保代码符合编码规范
2. **功能正确** - 确保代码实现正确的功能
3. **测试覆盖** - 确保代码有充分的测试
4. **文档完整** - 确保文档和注释完整
5. **性能考虑** - 确保代码性能合理

### 禁止行为

- 审查不仔细
- 审查延迟
- 审查时只看表面
- 审查时忽略测试
- 审查时忽略文档

## 审查原则

### 审查重点

1. **功能正确性** - 代码是否实现了预期的功能
2. **代码质量** - 代码是否符合编码规范
3. **测试覆盖** - 测试是否充分
4. **文档完整** - 文档和注释是否完整
5. **性能考虑** - 代码性能是否合理
6. **安全性** - 代码是否存在安全隐患

### 审查态度

- **建设性** - 提供建设性的反馈
- **尊重** - 尊重作者的劳动成果
- **及时** - 及时完成审查
- **仔细** - 仔细检查代码
- **学习** - 从审查中学习

## 审查清单

### 功能正确性

- [ ] 代码实现了预期的功能
- [ ] 边界条件已处理
- [ ] 错误处理完善
- [ ] 无逻辑错误
- [ ] 无潜在的 bug

### 代码质量

- [ ] 代码符合编码规范
- [ ] 命名清晰有意义
- [ ] 代码结构清晰
- [ ] 无重复代码
- [ ] 代码简洁易懂

### 测试覆盖

- [ ] 单元测试覆盖关键逻辑
- [ ] 集成测试覆盖关键流程
- [ ] 测试用例充分
- [ ] 测试代码质量高
- [ ] 无测试失败

### 文档完整

- [ ] 导出函数有 JSDoc
- [ ] 导出类有 JSDoc
- [ ] 复杂逻辑有注释
- [ ] README 已更新
- [ ] API 文档已更新

### 性能考虑

- [ ] 无性能瓶颈
- [ ] 无不必要的渲染（React）
- [ ] 无内存泄漏
- [ ] 异步操作正确处理
- [ ] 事件监听器正确清理

### 安全性

- [ ] 无 XSS 风险
- [ ] 无 CSRF 风险
- [ ] 输入验证完善
- [ ] 敏感信息不泄露
- [ ] 依赖无已知漏洞

## 审查流程

### 审查步骤

1. **理解需求** - 理解代码要实现的功能
2. **阅读代码** - 仔细阅读代码实现
3. **运行测试** - 运行测试确保功能正确
4. **检查清单** - 按照审查清单检查
5. **提供反馈** - 提供建设性的反馈
6. **确认修复** - 确认作者已修复问题

### 审查反馈

```markdown
# ✅ 正确 - 建设性的反馈

## 总体评价

代码质量很好，实现了预期的功能。有几个小问题需要修复。

## 问题

1. **命名问题**
   - `getUserData` 应该改为 `getUserById`，更清晰
   - `tmp` 变量名不够清晰，建议改为 `buffer`

2. **错误处理**
   - 第 45 行的错误处理不完整，建议添加日志
   - 第 78 行的错误被忽略，建议处理

3. **测试覆盖**
   - 缺少边界条件的测试
   - 建议添加错误场景的测试

## 建议

1. 使用 `Promise.allSettled` 替代 `Promise.all`
2. 添加函数注释说明参数和返回值
3. 考虑添加防抖优化性能

## 结论

修复上述问题后可以合并。

# ❌ 错误 - 不建设性的反馈

代码有问题，需要修复。
```

### 审查评论

```markdown
# ✅ 正确 - 具体的评论

## 第 45 行

\`\`\`javascript
if (error) {
  return;
}
\`\`\`

建议添加日志记录：

\`\`\`javascript
if (error) {
  console.error('Failed to fetch user:', error);
  return;
}
\`\`\`

## 第 78 行

\`\`\`javascript
const data = await fetchData();
\`\`\`

错误被忽略，建议处理：

\`\`\`javascript
try {
  const data = await fetchData();
  return data;
} catch (error) {
  console.error('Failed to fetch data:', error);
  throw error;
}
\`\`\`

# ❌ 错误 - 不具体的评论

代码有问题，需要修复。
```

## 审查最佳实践

### 审查时机

- **及时审查** - 收到 PR 后及时审查
- **专注审查** - 专注审查，避免分心
- **分批审查** - 大型 PR 分批审查

### 审查方法

- **整体审查** - 先整体了解代码变更
- **细节审查** - 再仔细检查代码细节
- **运行测试** - 运行测试确保功能正确
- **本地测试** - 本地运行代码验证

### 审查沟通

- **礼貌沟通** - 礼貌地提出问题和建议
- **解释原因** - 解释为什么需要修改
- **提供示例** - 提供修改示例
- **确认理解** - 确认作者理解反馈

## 常见问题

### 命名问题

```javascript
// ❌ 错误 - 命名不清晰
function getData(id) {
  return fetch(`/api/users/${id}`).then(r => r.json());
}

// ✅ 正确 - 命名清晰
async function getUserById(id) {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch user: ${id}`);
  }
  return response.json();
}
```

### 错误处理问题

```javascript
// ❌ 错误 - 错误处理不完整
async function fetchData() {
  const data = await fetch('/api/data');
  return data.json();
}

// ✅ 正确 - 错误处理完整
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch data:', error);
    throw error;
  }
}
```

### 性能问题

```javascript
// ❌ 错误 - 不必要的重渲染
function UserList({ users }) {
  return (
    <div>
      {users.map(user => (
        <UserCard key={user.id} user={user} onClick={() => handleClick(user.id)} />
      ))}
    </div>
  );
}

// ✅ 正确 - 使用 useCallback 避免重渲染
function UserList({ users }) {
  const handleClick = useCallback((id) => {
    console.log('Clicked user:', id);
  }, []);

  return (
    <div>
      {users.map(user => (
        <UserCard key={user.id} user={user} onClick={() => handleClick(user.id)} />
      ))}
    </div>
  );
}
```

### 测试覆盖问题

```javascript
// ❌ 错误 - 测试覆盖不足
describe('getUserById', () => {
  it('should return user', async () => {
    const user = await getUserById(1);
    expect(user.id).toBe(1);
  });
});

// ✅ 正确 - 测试覆盖充分
describe('getUserById', () => {
  it('should return user when id is valid', async () => {
    const user = await getUserById(1);
    expect(user.id).toBe(1);
    expect(user.name).toBeDefined();
  });

  it('should throw error when user not found', async () => {
    await expect(getUserById(999)).rejects.toThrow('User not found');
  });

  it('should throw error when id is invalid', async () => {
    await expect(getUserById(-1)).rejects.toThrow('Invalid user id');
  });
});
```

## 检查清单

审查代码前，确保：

- [ ] 理解代码要实现的功能
- [ ] 仔细阅读代码实现
- [ ] 运行测试确保功能正确
- [ ] 按照审查清单检查
- [ ] 提供建设性的反馈
- [ ] 确认作者已修复问题
- [ ] 礼貌地提出问题和建议
- [ ] 解释为什么需要修改
- [ ] 提供修改示例
- [ ] 确认作者理解反馈
