# 最佳实践

Version 插件的最佳实践和建议。

## 版本更新策略

### 开发阶段

```bash
# 完成小任务
/version bump build

# 输出：1.0.0.0 → 1.0.0.1
```

### 测试阶段

```bash
# 修复 Bug
/version bump patch

# 输出：1.0.0.5 → 1.0.1.0
```

### 发布阶段

```bash
# 新功能发布
/version bump minor

# 输出：1.0.1.0 → 1.1.0.0

# 重大更新发布
/version bump major

# 输出：1.1.0.0 → 2.0.0.0
```

## 版本管理流程

### 功能开发

```bash
# 1. 开始开发
git checkout -b feature/new-feature

# 2. 完成任务
/version bump build

# 3. 提交代码
git add .version
git commit -m "chore: bump version to 1.0.0.1"

# 4. 合并分支
git checkout main
git merge feature/new-feature
```

### Bug 修复

```bash
# 1. 修复 Bug
git checkout -b fix/bug-fix

# 2. 修复完成
/version bump patch

# 3. 提交代码
git add .version
git commit -m "fix: 修复 xxx 问题"

# 4. 合并分支
git checkout main
git merge fix/bug-fix
```

### 版本发布

```bash
# 1. 确保所有测试通过
npm test

# 2. 更新版本
/version bump minor

# 3. 更新 CHANGELOG
# 编辑 CHANGELOG.md

# 4. 创建标签
git tag v1.1.0.0
git push origin v1.1.0.0

# 5. 发布
npm publish
```

## 版本号规划

### 初始版本

```
0.1.0.0 - 初始开发版本
0.2.0.0 - 添加核心功能
1.0.0.0 - 首个稳定版本
```

### 迭代版本

```
1.0.0.0 - 稳定版本
1.0.1.0 - Bug 修复
1.1.0.0 - 新功能
2.0.0.0 - 重大更新
```

## 常见问题

### 如何回退版本？

```bash
/version set 1.0.0.0
```

### 如何查看版本历史？

```bash
git log -- .version
```

### 版本文件应该提交吗？

是的，`.version` 文件应该提交到版本控制。
