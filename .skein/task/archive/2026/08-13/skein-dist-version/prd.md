# SKEIN 前端 dist 版本戳 + 过期检测加固 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
- [ ] dist 产物过期检测不再依赖不可靠的文件 mtime，改用构建时写入的版本戳(内容 hash)判定；嵌套路由(如 /task/detail)读取产物前有存在性兜底，不再抛裸 FileNotFoundError
## 边界
- 改动限 skeinlib/web/serve.py (ensure_dist_built/_src_newer_than_dist/嵌套路由 handler)
- 版本戳写入时机: ensure_dist_built 编译成功后写；戳内容取 assets/nextjs/src 下源文件内容 hash (不依赖 git, marketplace 副本可能非 git 仓/浅 clone)；不改 Next.js 前端源码/构建产物结构
## User Stories
1. 用户在 marketplace 装的插件里打开 task 详情页，之前遇到裸 500 FileNotFoundError，现在要么正常渲染要么看到友好的『前端未构建/正在重建』提示
2. 开发者改了 assets/nextjs/src 下源码后重启 skein board，即使 git 操作把文件 mtime 全部刷平，dist 仍被正确判定为过期并触发重建
## 验收标准
- [ ] ensure_dist_built 编译成功后 dist/ 下存在版本戳文件，内容随源码变化而变化；_src_newer_than_dist 在版本戳不匹配时返回 True，即使 dist/index.html mtime 晚于源码文件
- [ ] /task/detail (及其余嵌套 SPA 路由) 读取的目标文件不存在时不再抛未捕获异常，返回友好占位或 404 JSON
## 验证方式
- 新增/改造 test_serve_frontend_build.py 用例覆盖: 版本戳写入、戳不匹配触发重建、mtime 骗过旧逻辑但戳能识破、嵌套路由文件缺失时的兜底行为
## Testing Decisions
- [ ] uv run pytest plugins/tools/skein/scripts/tests/test_serve_frontend_build.py -q 全绿; 不跑真实 next build (沿用现有 mock 模式)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein subtask list skein-dist-version`)
