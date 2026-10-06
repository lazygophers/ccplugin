# TS 构建别 npx tsc（mise shim 会截走）；.mts 源里 import 写 .mjs 后缀

两坑同出自 2026-10-06 ask-ui .mjs → TypeScript 迁移：

1. **`npx tsc` 被 mise shim 截走**，报 `No version is set for shim: tsc`。本仓库 Node 工具链
   版本不走 mise。用 skill 目录里的 `node_modules/.bin/tsc`，或
   `npm --prefix <skill-dir> run build`。
2. **`module: NodeNext` 下 `.mts` 源文件的相对 import 必须写编译后的 `.mjs` 后缀**
   （`import { log } from './log.mjs'`）。写 `.mts` 编译不过（除非开
   `allowImportingTsExtensions` + `noEmit`，本仓不用）。别用 sed 把 import 后缀批量改成
   `.mts`——那是往错误方向改，改完还得改回来。

出处：2026-10-06 ask-ui 迁移 session 实录；NodeNext 后缀规则另见
skills/tools/ask-ui/SKILL.md「开发：TS 源码与编译产物」一节。
