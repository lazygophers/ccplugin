# skein assets/nextjs 双锁文件：package-lock.json 是死副本但必须同步维护

`plugins/tools/skein/assets/nextjs/package-lock.json` 是死副本（活的锁文件是
`pnpm-lock.yaml`，见 `plugins/tools/skein/scripts/tests/test_serve_frontend_build.py:41`
「本仓前端用 pnpm lockfile」），被跟踪且保留，不删。

依赖升级清告警的固定动作：

1. `package.json` 顶版本 → `pnpm update`（不用 `pnpm install`）
2. `npm update <pkg>` 同步重生成 `package-lock.json`（只动锁文件，不碰 pnpm
   装的 node_modules）。不用 `npm install`
3. `pnpm audit` 与 `npm audit` 双跑，双 0 才算完
