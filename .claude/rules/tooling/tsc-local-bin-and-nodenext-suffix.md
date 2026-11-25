# TS 构建别 npx tsc（mise shim 会截走）；.mts 源里 import 写 .mjs 后缀

两条：

1. **`npx tsc` 被 mise shim 截走**，报 `No version is set for shim: tsc`。本仓库 Node 工具链
   版本不走 mise。用 skill 目录里的 `node_modules/.bin/tsc`，或
   `npm --prefix <skill-dir> run build`。
2. **`module: NodeNext` 下 `.mts` 源文件的相对 import 必须写编译后的 `.mjs` 后缀**
   （`import { log } from './log.mjs'`）。不用 sed 把 import 后缀批量改成
   `.mts`。
