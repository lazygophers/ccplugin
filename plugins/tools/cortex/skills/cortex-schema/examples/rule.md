> 样例 — type=rule, 完整可直接落盘到 memory/L0-core/never-commit-secrets.md

---
type: rule
level: L0
created: 2026-06-09
updated: 2026-06-09
tags: [safety, hardrule, secrets, git]
aliases: [no-secret-commit, secret-hygiene]
---

# 永远不提交凭证

L0 硬规则: 任何 API key / token / 私钥 / `.env` 文件禁入 git 历史. 一旦泄漏视同公开, 立即吊销 + 轮换.

## 适用范围

- 所有 git 仓库 (含 private)
- 含 `.env` `*.pem` `*.key` `id_rsa` `credentials.json` 等
- pre-commit hook 必须装 `gitleaks` 或同类扫描

## 违例处理

1. `git filter-repo` 重写历史
2. 吊销并轮换全部受影响凭证 (参考 [[shell-quoting-rules]] 的 shell 转义注意事项)
3. 通知 owner

## 关联

- 入门: [[secret-hygiene-checklist]]
- 工具: [[gitleaks-setup]]
