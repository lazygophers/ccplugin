> 样例 — type=memory level=L1, 完整可直接落盘到 memory/L1-long/shell-quoting-rules.md

---
type: memory
level: L1
created: 2026-06-09
updated: 2026-06-09
weight: 0.85
tags: [shell, bash, quoting, gotcha]
aliases: [shell-quote-cheatsheet]
---

# Shell 引号规则

长期记忆: bash/zsh 引号语义已固化, 多次验证可靠.

## 规则

- 单引号 `'...'`: 内部完全字面化, 含 `$` 也不展开; 内部不能有单引号
- 双引号 `"..."`: 展开 `$var` / `` `cmd` `` / `$(cmd)`; 反斜杠仅对 `$` `` ` `` `"` `\` `\n` 生效
- 无引号: 词法分割 + 路径展开 + 变量展开 — 含空格变量必踩坑

## 常见踩坑

含空格路径必须双引号: `cd "$dir"` 而非 `cd $dir`. 详见 [[never-commit-secrets]] 中提到的 `.env` 处理类似谨慎.

## HEREDOC

`<<'EOF'` 不展开, `<<EOF` 展开. 写 git commit message 用前者保留 `$` 字面值.
