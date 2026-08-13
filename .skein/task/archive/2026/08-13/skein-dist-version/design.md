# SKEIN 前端 dist 版本戳 + 过期检测加固 — 详细设计

## 根因
`_src_newer_than_dist()` (`skeinlib/web/serve.py:82`) 只靠文件 mtime 比对源码与 dist 产物。
marketplace 副本经 git clone/pull 落盘时，源码与 dist 文件的 mtime 会被同一批操作刷新，
相对新旧关系不可靠 —— dist 可能被误判「未过期」，从而漏过重建。
`/task/detail` 等嵌套 SPA 路由 (`serve.py:675` 附近) 直接裸读 `dist_dir()/task/detail/index.html`，
无存在性判断、无 `ensure_dist_built` 兜底，产物缺失时抛未捕获 `FileNotFoundError` → 用户看到裸 500。

## 方案
1. **版本戳**: `ensure_dist_built()` 编译成功后，在 `dist_dir()` 下写一个版本戳文件 (如
   `.build-stamp`)，内容为 `assets/nextjs/src` 下所有源文件内容的聚合 hash (不用 git SHA —
   marketplace 副本可能是非 git 目录/浅 clone，git 信息不可靠；内容 hash 与部署方式无关)。
2. **过期检测升级**: `_src_newer_than_dist()` 优先比较「当前源码 hash」与「戳文件记录的 hash」，
   不一致 → 过期。戳文件缺失 (旧版本产物/占位页) 仍按现状逻辑判过期，保持向后兼容。mtime 判断
   保留作为 hash 计算异常时的兜底 (不引入新的失败模式)。
3. **嵌套路由兜底**: 抽一个小 helper 读取 `dist_dir()` 下任意子路径的 `index.html`，文件不存在
   时返回 `ensure_dist_serveable()` 同款风格的友好占位 HTML (说明未构建/正在重建)，不再让
   `FileNotFoundError` 冒穿到 ASGI 层。`/` 与 `/task/detail` 两个已知 SPA 入口都走这个 helper。

## 不做
- 不接入真实 `next build` 跑全流程测试 (太慢/依赖 node, 沿用现有 mock 测试模式)。
- 不改 Next.js 源码或构建产物目录结构。
- 不做 git SHA 版本戳 (marketplace 副本 git 信息不可靠, 内容 hash 更稳)。

## 测试接缝 (seam)
复用现有接缝 `test_serve_frontend_build.py` (已覆盖 `_src_newer_than_dist`/`ensure_dist_built`/
`ensure_dist_serveable` 的决策逻辑，不跑真构建) —— 本次改动同一文件内新增用例:
- 版本戳写入/比对 (`_src_newer_than_dist` 命中 hash 不一致时返回 True，即使 mtime 更新)
- 嵌套路由 helper 在目标文件缺失时返回占位而不抛异常
