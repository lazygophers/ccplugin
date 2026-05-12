---
type: meta
title: 领域
tags: [meta]
---

# 领域 (Domains)

## 用途

项目 / 仓库 / 业务领域级笔记。按 `host/org/repo` 分层 (e.g. `github.com/foo/bar/`),每个 domain 是一个 git remote 或业务边界的根。

## 用法

- 走 `cortex-ingest` 命令摄取 git remote URL,自动建分层目录
- frontmatter 设 `type: domain`, 含 `repo_url` / `host` / `org` 字段
- 项目级 MOC、ADR、changelog 都归此目录

## 链接

- 上级: [[home]] · [[projects-moc]]
- 相关: [[sources/_index]] · [[questions/_index]]

```dataview
LIST FROM "domains" WHERE type = "domain" SORT updated DESC LIMIT 20
```
