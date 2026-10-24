# 开发：TS 源码与编译产物

- **改代码只改 `scripts/**/*.mts`**。同名 `.mjs` 是 tsc 编译产物，一起进仓库（`~/.agents` 的安装副本直接跑 `.mjs`，不带构建步骤）；手改 `.mjs` 会在下次编译时被覆盖。
- 编译即类型检查（strict）：`npm --prefix <ASK_ME_SKILL_DIR> run build`（首次先 `npm --prefix <ASK_ME_SKILL_DIR> install`）；只查不改用 `run typecheck`。pre-commit 钩子会自动编译、暂存产物并跑自测。
- 运行时要求 Node ≥ 18（`fetch` / `AbortSignal.timeout`）；package.json 的 `engines` 已声明。
- 浏览器资产 `assets/app/*.js` 保持 .js（Node 与浏览器共用，无构建），类型契约在同目录 `.d.ts`——改了 `.js` 的导出签名要同步改 `.d.ts`。
