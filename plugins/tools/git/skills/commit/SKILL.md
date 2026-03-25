---
description: git commit 提交规范
user-invocable: true
context: fork
model: haiku
memory: project
---

**提交信息生成模板**

```
<type>(<scope>): <subject>

<body>
<footer>
```

其中：

- `type`: 必填，类型，可选值：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore`、`revert`、`build`、`ci`、`wip`、
  `workflow`、`types`、`release`、`other`
- `scope`: 可选，作用域，如：`app`、`api`、`db`、`utils`、`server`、`client`、`config`、`test`、`docs`、`build`、`ci`、`wip`、
  `workflow`、`types`、`release`、`other`
- `subject`: 必填，提交信息，不超过50个字符，如：`add app module`、`fix api bug`、`update docs`、`refactor code`、
  `perf optimize`、`test add unit test`、`chore update build`、`revert commit`、`build update package`、`ci add ci`、
  `wip add wip`、`workflow update workflow`、`types update types`、`release update release`、`other update other`
- `body`: 可选，详细描述，不超过80个字符，如：`add app module`、`fix api bug`、`update docs`、`refactor code`、`perf optimize`、
  `test add unit test`、`chore update build`、`revert commit`、`build update package`、`ci add ci`、`wip add wip`、
  `workflow update workflow`、`types update types`、`release update release`、`other update other`
- `footer`: 可选，关闭issue，如：`close #123`、`fix #123`、`resolve #123`、`close #123, #456`、`fix #123, #456`、
  `resolve #123, #456`

**注意**

- 如果一次提交涉及到多个不同的类型，则需要使用多个`commit`进行提交，每个`commit`的`type`和`subject`需要分别填写
- 不允许将以下类型的文件提交:
  - 备份文件：如 `.*.bak`
  - 日志文件：如 `.*.log`
  - 临时文件：如 `.*.tmp`/`.*.temp`
  - 二进制文件：如 `.*.exe`/`.*.dll`/`.*.so`/`.*.dylib`/`.*.a`/`.*.lib`/`.*.o`/`.*.obj`/`.*.img`
  - 压缩文件：如 `.*.zip`/`.*.rar`/`.*.7z`/`.*.tar`/`.*.gz`/`.*.bz2`/`.*.xz`/`.*.tar.gz`

## 执行过程检查清单

### 提交前检查
- [ ] 运行 `git status` 查看未提交的文件和变更类型
- [ ] 确认变更文件列表符合预期
- [ ] 确认没有意外的文件变更（敏感信息、临时文件）
- [ ] 确认代码已通过本地测试
- [ ] 确认代码已通过 lint 检查
- [ ] 确认没有提交备份/日志/临时/二进制/压缩文件

### 提交信息生成检查
- [ ] type 字段已填写（feat/fix/docs/style/refactor/perf/test/chore/revert/build/ci/wip/workflow/types/release/other）
- [ ] scope 字段已填写（如适用）
- [ ] subject 不超过 50 个字符
- [ ] subject 清晰描述变更内容
- [ ] body 不超过 80 个字符（如适用）
- [ ] footer 包含关闭的 issue（如适用，如 close #123）
- [ ] 一次提交仅涉及一个类型（多类型需拆分为多个commit）

### 提交信息格式检查
- [ ] 格式符合模板：`<type>(<scope>): <subject>`
- [ ] subject 使用祈使语气（"添加"而非"添加了"）
- [ ] subject 首字母小写
- [ ] subject 结尾无句号

## 完成后检查清单

### 提交验证检查
- [ ] 使用 `git log -1` 确认提交成功
- [ ] 确认提交信息正确
- [ ] 确认提交包含了预期的文件变更
- [ ] 确认没有敏感信息泄露

### 提交质量检查
- [ ] 提交是原子的（只做一件事）
- [ ] 提交信息清晰易懂
- [ ] 提交不包含无关变更
- [ ] 提交不破坏构建
- [ ] 提交可独立回退
