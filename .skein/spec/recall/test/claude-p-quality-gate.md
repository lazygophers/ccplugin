---
title: claude-p-quality-gate
layer: recall
category: test
keywords: [claude-p,skill,quality gate,stdin,--bare,test,macOS]
status: active
---

## skill 质量门标准命令形式（stdin + --bare）

### 触发场景
改写或诊断 skill 后需要用质量门验证 AI 理解是否正确，特别是带 YAML frontmatter 的 SKILL.md 文件。

### 陷阱-正解
**陷阱**：用 CLAUDE.md 记的命令 `claude -p "$(cat SKILL.md)" ...`，YAML 的 `---` 被当成 CLI 选项，报错。
**正解**：quality gate 命令必须用 stdin 管道形式，加 `--bare` 禁 hook 劫持，加 `2>/dev/null` 消 connector 警告。

### 标准命令形式

```bash
cat <SKILL.md 路径> | claude -p --bare "<问题>" --output-format stream-json 2>/dev/null \
  | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

### 为什么这样写

| 问题 | 原因 | 后果 |
|---|---|---|
| 用 `"$(cat ...)"` 插值而非管道 | frontmatter 的 `---` 被解析成 CLI 选项 | `error: unknown option '---'` |
| 缺 `2>/dev/null` | stderr 的 connector 警告混进 jq | `Invalid numeric literal` (jq 报错) |
| 缺 `--bare` | skein hook 注入把 prompt 劫持成 "exec mode"，或非 Anthropic 路由模型报错 | `API Error 400` |

### 端点抖动与重试

claude -p 端点偶发空返回/超时，需**重试循环**兜底。空返回 ≠「改写失败」，重试后有正常返回才下判断。

### macOS 环境差异

macOS 无 `timeout` 命令（用 `timeout -v` 需装 coreutils），脚本中若需超时控制改用 `sleep` + 后台 job 或 `gtimeout`（brew install coreutils）。

### predictability 验法 = 三跑一致

改写后的 skill，同一问题**连跑 3 次**质量门，三次返回的答案必须一致才算 predictability 达标（不只是「有返回」）。

### 关联
与 skill-quality-checklist.md 的「质量门验证法」章节同源，本条补充命令形式的细节与 macOS 差异
