---
name: git-workflow
description: Git工作流 - 分支管理、Commit规范、PR流程、合并策略、版本发布
user-invocable: true
context: fork
model: sonnet
skills:
  - code-review
---

# Git工作流（Git Workflow）

本 Skill 提供标准化的 Git 工作流指导，涵盖分支管理、提交规范、代码审查和版本发布。

## 概览

**核心能力**：
1. **工作流选择** - Git Flow、GitHub Flow、Trunk-Based Development
2. **分支管理** - 分支命名、生命周期、保护规则
3. **Commit规范** - Conventional Commits、提交粒度、消息格式
4. **PR流程** - 创建、审查、合并、冲突解决
5. **版本发布** - 语义化版本、发布流程、回滚策略

**适用场景**：
- **个人项目**：简化的 GitHub Flow
- **小团队**：GitHub Flow + PR Review
- **大型项目**：Git Flow + Release Management
- **持续部署**：Trunk-Based Development

## 执行流程

### 阶段1：选择工作流

**目标**：根据项目特点选择合适的工作流

**步骤**：
1. 使用 `AskUserQuestion` 询问以下信息（如果用户输入不明确）：
   - 团队规模：「个人」「小团队（<10人）」「中型团队（10-50人）」「大型团队（>50人）」
   - 发布频率：「持续部署」「每周发布」「每月发布」
   - 质量要求：「快速迭代」「稳定优先」

2. 推荐工作流：
   - **GitHub Flow**（推荐）：简单、适合持续部署
   - **Git Flow**：适合定期发布、需要多版本维护
   - **Trunk-Based Development**：适合高频部署、强依赖自动化测试

### 阶段2：分支管理

**目标**：规范分支命名和生命周期

**步骤**：
1. **主分支**（长期分支）：
   - `main`/`master`：生产环境代码，受保护
   - `develop`（Git Flow）：开发分支，集成最新功能

2. **功能分支**（短期分支）：
   - **命名规范**：`feature/描述` 或 `feature/issue-编号-描述`
   - **示例**：`feature/user-authentication`、`feature/123-add-payment`
   - **生命周期**：从 `develop`/`main` 创建 → 开发 → PR → 合并 → 删除

3. **修复分支**：
   - **Hotfix**：`hotfix/描述`（从 `main` 创建，紧急修复生产问题）
   - **Bugfix**：`bugfix/描述`（从 `develop` 创建，修复开发环境问题）

4. **发布分支**（Git Flow）：
   - **命名规范**：`release/版本号`
   - **示例**：`release/1.2.0`
   - **用途**：版本发布前的最后准备（版本号更新、文档）

### 阶段3：Commit规范

**目标**：统一提交消息格式，提升可读性

**步骤**：
1. **Conventional Commits 格式**：
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```

2. **Type 类型**：
   - `feat`: 新功能
   - `fix`: 修复bug
   - `docs`: 文档变更
   - `style`: 代码格式（不影响功能）
   - `refactor`: 重构（既不是新功能也不是bug修复）
   - `perf`: 性能优化
   - `test`: 测试相关
   - `chore`: 构建工具、依赖更新

3. **Scope 范围**（可选）：
   - 影响的模块：`auth`、`payment`、`user`
   - 示例：`feat(auth): add JWT authentication`

4. **Subject 主题**：
   - 简明扼要（≤50字符）
   - 使用动词原形（add、fix、update）
   - 不以句号结尾

5. **Body 正文**（可选）：
   - 详细说明变更原因和内容
   - 每行≤72字符

6. **Footer 脚注**（可选）：
   - 关闭Issue：`Closes #123`
   - 破坏性变更：`BREAKING CHANGE: ...`

### 阶段4：PR流程

**目标**：规范化 Pull Request 流程

**步骤**：
1. **创建PR前**：
   - 确保本地测试通过
   - 同步最新代码（`git pull origin main`）
   - 解决冲突
   - 自我审查代码

2. **PR模板**：
   ```markdown
   ## 变更说明
   简要描述本次变更的目的和内容

   ## 变更类型
   - [ ] 新功能
   - [ ] Bug修复
   - [ ] 重构
   - [ ] 文档更新

   ## 测试计划
   - [ ] 单元测试通过
   - [ ] 集成测试通过
   - [ ] 手动测试完成

   ## 相关Issue
   Closes #123

   ## 截图（如适用）
   ```

3. **代码审查清单**：
   - [ ] 代码符合项目规范
   - [ ] 测试覆盖率≥80%
   - [ ] 无安全漏洞
   - [ ] 文档已更新
   - [ ] 无性能问题

4. **合并策略**：
   - **Squash Merge**（推荐）：多个提交合并为一个，保持历史简洁
   - **Merge Commit**：保留所有提交历史
   - **Rebase Merge**：线性历史，但需要团队熟悉rebase

### 阶段5：版本发布

**目标**：规范化版本管理和发布流程

**步骤**：
1. **语义化版本（SemVer）**：
   - **格式**：`MAJOR.MINOR.PATCH`（例如：`1.2.3`）
   - **MAJOR**：不兼容的API变更
   - **MINOR**：向后兼容的功能新增
   - **PATCH**：向后兼容的bug修复

2. **发布流程（Git Flow）**：
   ```bash
   # 1. 创建发布分支
   git checkout -b release/1.2.0 develop

   # 2. 更新版本号
   # 编辑 package.json、setup.py 等

   # 3. 更新 CHANGELOG.md
   # 记录本次发布的变更

   # 4. 提交变更
   git commit -m "chore(release): bump to 1.2.0"

   # 5. 合并到 main
   git checkout main
   git merge --no-ff release/1.2.0
   git tag -a v1.2.0 -m "Release 1.2.0"

   # 6. 合并到 develop
   git checkout develop
   git merge --no-ff release/1.2.0

   # 7. 删除发布分支
   git branch -d release/1.2.0

   # 8. 推送到远程
   git push origin main develop --tags
   ```

3. **CHANGELOG.md 格式**：
   ```markdown
   # Changelog

   ## [1.2.0] - 2026-03-20
   ### Added
   - JWT authentication (#123)
   - User profile management (#124)

   ### Fixed
   - Login timeout issue (#125)

   ### Changed
   - Updated API response format (#126)
   ```

**详细工作流模式** → 参见 [examples.md](./examples.md)

## 最佳实践

### Commit 最佳实践

- **原子性提交**：每次提交只做一件事
- **频繁提交**：小步快跑，便于回滚
- **有意义的消息**：清晰描述变更内容
- **避免大文件**：二进制文件、日志文件使用 .gitignore

### 分支最佳实践

- **分支保护**：`main` 分支设置保护规则（禁止直接推送、要求PR、要求审查）
- **及时删除**：合并后删除功能分支
- **同步更新**：定期从 `main`/`develop` 拉取最新代码
- **避免长期分支**：功能分支生命周期≤2周

### PR 最佳实践

- **小而频繁**：单个PR变更≤500行代码
- **自我审查**：提交PR前先自己审查一遍
- **CI/CD集成**：PR自动触发测试
- **及时响应**：24小时内完成审查

**详细冲突处理和工具配置** → 参见 [examples.md](./examples.md)

## 工具集成

- **Git客户端**：GitKraken、Sourcetree、GitHub Desktop
- **代码审查**：GitHub PR、GitLab MR、Bitbucket PR
- **CI/CD**：GitHub Actions、GitLab CI、Jenkins
- **分支管理**：GitFlow extension、Git aliases

## 相关 Skills

- **code-review** - 代码审查（PR审查）
- **refactoring** - 重构指导（重构分支管理）
- **testing** - 测试策略（CI测试）
