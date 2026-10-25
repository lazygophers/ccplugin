# skein assets/nextjs 双锁文件：package-lock.json 是死副本但必须同步维护

`plugins/tools/skein/assets/nextjs/package-lock.json` 是死副本（活的锁文件是
`pnpm-lock.yaml`，见 `plugins/tools/skein/scripts/tests/test_serve_frontend_build.py:41`
「本仓前端用 pnpm lockfile」），但被跟踪且用户已拍板保留——删它会被权限拒绝，别再试。
代价是 dependabot / audit 告警两份锁文件各报一遍。

依赖升级清告警的固定动作（2026-10-02 实测，commit dba370cc）：

1. `package.json` 顶版本 → `pnpm update`（`pnpm install` 会复用锁文件旧版本，
   不重新解析传递依赖，告警清不掉）
2. `npm update <pkg>` 同步重生成 `package-lock.json`（只动锁文件，不碰 pnpm
   装的 node_modules）。`npm install` 不行：package.json 没变时它按锁文件旧
   解析装包，锁文件零改动——pnpm update 清传递依赖告警正是这种，package.json
   不动（2026-10-25 实测）
3. `pnpm audit` 与 `npm audit` 双跑，双 0 才算完
