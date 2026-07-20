---
title: CLI 工具：argparse 为默认（typer 仅富交互）
layer: recall
category: script
keywords: [cli,argparse,typer,script]
source: reconstruct
authored-by: skein-spec
created: 1784345946
status: active
related: []
updated: 1784345946
---

## 触发场景
编写新 CLI 工具或重构现有脚本。

## 陷阱-正解
**陷阱**：所有 CLI 都用 typer（过度设计）。
**正解**：默认用 argparse（标准库）；仅需子命令树、富格式化的用 typer。

## 规则
scripts/ 下 6:1 比例 argparse:typer 反映约定（argparse 为基线）。

## 案例
- argparse: check.py, update.py, clean.py （无需复杂 routing）
- typer: md2html.py (子命令 + 格式选项)
