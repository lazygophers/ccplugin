"""规则记忆库 (`.skein/spec`) — namespace × inclusion 两个正交维度。

- **namespace** = 内容类型, 即所在目录 (rules / product / map / external, 自由可扩展,
  由目录扫描得而非白名单)。
- **inclusion** = 加载策略, 写在每篇 frontmatter 里 (`always` 常驻注入 SessionStart /
  `auto` 按需召回 / `fileMatch` 按 globs 命中 / `manual` 纯手动检索)。

**两者正交**: 目录不决定加载策略, 搬文件改不了它 —— 这一条曾被文档写反过, 教用户把文件从
`spec/core/` 移到 `spec/recall/` 来「降级」, 而那什么也不会发生。

## 模块
`text` 文本纯函数 (frontmatter 解析 / 摘要 / slug) · `model` 常量 + 预算 + 库根定位 ·
`core` `Spec` 基类 (路径 / 扫描 / inclusion 判定) · `index` 重建索引 + sqlite FTS + 召回 ·
`inject` core 正文与 SessionStart/SubagentStart 注入 · `write` sediment 写盘 ·
`maintain` 体检 / 降级 / 归档 / 重构 · `cli` argparse 入口。
"""
