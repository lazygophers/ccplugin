---
name: commit
description: git commit 提交规范
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