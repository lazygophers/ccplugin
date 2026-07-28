---
title: cli
layer: recall
category: script
keywords: [cli,argparse,typer,script,output,rich,console,main,exit,return,sys.exit]
status: active
---

## CLI 工具：argparse 为默认（typer 仅富交互）

### 触发场景
编写新 CLI 工具或重构现有脚本。

### 陷阱-正解
**陷阱**：所有 CLI 都用 typer（过度设计）。
**正解**：默认用 argparse（标准库）；仅需子命令树、富格式化的用 typer。

### 规则
scripts/ 下 6:1 比例 argparse:typer 反映约定（argparse 为基线）。

### 案例
- argparse: check.py, update.py, clean.py （无需复杂 routing）
- typer: md2html.py (子命令 + 格式选项)

## CLI 输出走 rich Console（非裸 print）

### 触发场景
用户可见输出（表格、面板、进度)。

### 陷阱-正解
**陷阱**：裸 print。
**正解**：经 rich.console.Console (全仓 221 处示例)。

## main() 返回退出码，sys.exit 调用

### 铁律

- MUST：CLI 脚本定义 `def main() -> int` 函数，返回值为整数退出码（0=成功，1=失败）
- MUST：脚本尾部 `if __name__=="__main__": sys.exit(main())`
- MUST：main 内所有失败路径 return 非零码

### 反例表

| 禁 | 改为 |
|---|---|
| `def main():` 无返回类型 | `def main() -> int:` |
| 直接 print 结果无 return | return 0 或 1 |
| sys.exit(0) 在 main 内调用 | 仅在 `if __name__` 块 |
| 异常直接崩溃 | try/except 后 return 1 |
