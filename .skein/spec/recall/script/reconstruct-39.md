---
title: main() 返回退出码，sys.exit 调用
layer: recall
category: script
keywords: [cli,main,exit,return,sys.exit]
source: reconstruct
authored-by: skein-spec
created: 1784346676
status: active
related: []
updated: 1784346676
---

## 铁律

- MUST：CLI 脚本定义 `def main() -> int` 函数，返回值为整数退出码（0=成功，1=失败）
- MUST：脚本尾部 `if __name__=="__main__": sys.exit(main())`
- MUST：main 内所有失败路径 return 非零码

## 反例表

| 禁 | 改为 |
|---|---|
| `def main():` 无返回类型 | `def main() -> int:` |
| 直接 print 结果无 return | return 0 或 1 |
| sys.exit(0) 在 main 内调用 | 仅在 `if __name__` 块 |
| 异常直接崩溃 | try/except 后 return 1 |
