---
name: show-me
version: 0.1.0
argument-hint: "[config [show | get <key> | set <key> <value> | unset <key>] [--project]]"
description: 把给人读的产物排成一页离线 HTML 阅读页：模型只写内容 JSON，预编译渲染器负责排版、配色、图表、页脚与水印，三种风格（科研风 paper / 手绘风 sketch / 程序员风 terminal）。凡是要交给人阅读的成品都用它，用户没点名也用：调研报告、技术方案、对比选型、评审与审计结论、原理讲解、进度报告、复盘、规格说明（research report, proposal, comparison, review, explainer, status report, retrospective, spec, "write it up", "给我一份报告"）。不用于：闲聊、一两句能答完的问题、原样转述命令输出、commit message / 邮件 / Slack 消息等指定格式成品、派给 agent 的内部回报。
---

# show-me

内容与样式分离：模型写一份只有内容的 JSON，`show-me render` 把它注入预编译渲染器模板，写出单文件 HTML（离线可开、≤1.5MB）。不在现场构建前端项目，不手写 HTML/CSS。

## 第 0 节：参数

- `$ARGUMENTS` 以 `config` 开头：只处理配置，不生成页面。把参数原样传给 CLI：

  ```bash
  node <本 SKILL.md 所在目录>/scripts/show-me.mjs $ARGUMENTS
  ```

  然后用一两句话告诉用户结果：`show`（或只有 `config`）列出每个键的值与来源层（default 内置默认 / system 系统级 / project 项目级）；`get` 报值与来源；`set` / `unset` 报写入的层与文件路径。退出码 2 时原样转述 stderr 里的键名与期望类型。
- 无参数：走下面的主流程出页。

## 主流程

1. **判断是否出页**。产物要交给人读，且属于下表任一类型，就出页；否则直接在对话里回答。

   | type | 产物 |
   |---|---|
   | `research` | 调研报告 |
   | `plan` | 方案、计划 |
   | `compare` | 对比、选型 |
   | `review` | 评审、审计 |
   | `explain` | 原理讲解 |
   | `report` | 进度报告、复盘 |
   | `spec` | 规格说明 |

2. **写内容 JSON**，放在项目 `.scratch/<topic>/` 下（如 `.scratch/<topic>/content.json`）。必填：`topic`（安全文件名，决定输出文件名）、`type`、`title`、`summary`（`point` 一句话结论 + `text` 摘要 + 至多 3 条 `points`）、`blocks`（≥1）、`references`（出处，可为空数组）。块类型与字段见 [references/content-schema.md](references/content-schema.md)。
3. **渲染**：

   ```bash
   node <本 SKILL.md 所在目录>/scripts/show-me.mjs render .scratch/<topic>/content.json
   ```

   stdout 一行 JSON：`{"path": "<绝对路径>", "style": "paper", "version": 1}`。退出码 0 成功，2 为输入或配置错误（stderr 列出文件、键名、期望类型），1 为内部错误。
4. **回复用户**：一句结论 + 产物文件的绝对路径链接（取 stdout 的 `path`）。不在回复里复述页面内容。

同一 topic 再次渲染时自动写成下一版（`<topic>-v2.html`…），旧版保留；v≥2 时页头链接上一版。内容里写 `changes`（字符串数组）会在正文前显示「与上一版的变更」。

## 写内容的规则

- 先写结论：`summary.point` 是一句话结论，`points` 是不超过 3 条要点。
- 一个 `heading` 开一个面板，每个面板回答一个子问题；面板内的图、表、代码各带 `caption`，可选 `point` 写本块要点。
- 数据用结构化块（`table` / `kv` / `chart` / `flow` / `graph` / `steps`），不要把表格写进段落。
- 画关系图：有分叉或合并（git 分支、调用树、架构依赖）用 `graph`，纯顺序步骤用 `flow`。
- 需要用户做的事放 `steps` 块，置于末尾一节，标题写「需要你做的事」。
- 每条事实性结论在 `references` 给出处（URL、`file::symbol`、命令）。出处清单只列本轮实际读过的来源（读过的网页、文件、命令输出）；凭记忆的知识不列为出处，确需提及时在该条 `text` 末尾标「未核对」。
- 图片只用本地文件路径（相对内容 JSON 所在目录）或 `data:` URI；远程 URL 会被拒绝，页面必须离线。
- 不写样式、颜色、字号；不写页脚、水印、署名、生成时间，这些由 CLI 按配置填写。

## 风格选择

| 风格 | 取值 | 适合 |
|---|---|---|
| 科研风 | `paper` | 调研、规格、评审：期刊式标题横幅、指标卡、摘要框、旁注、三线表、编号参考文献 |
| 手绘风 | `sketch` | 原理讲解、复盘：白板点阵、马克笔手绘框与箭头、hachure 柱状图、便利贴 |
| 程序员风 | `terminal` | 技术方案、代码相关进度：深色终端配色、编辑器窗口卡片、框线流程图、代码高亮 |

页面不打包字体：科研风用 `serif` 通用族，程序员风与代码用 `monospace`，手绘风沿用浏览器默认字体。

决定顺序：`--style` 参数 > 内容 JSON 的 `style` > 配置 `byType[type]` > 配置 `style` > `paper`。用户在对话里点名风格时写进内容 JSON 的 `style`；未点名时不写，交给配置。页面顶部默认有三种风格切换（配置 `switcher`）。

## 命令

| 命令 | 作用 |
|---|---|
| `render <content.json> [--out <file>] [--no-open] [--style paper\|sketch\|terminal]` | 渲染；`--out` 指定输出文件（版本号按该目录计算），`--no-open` 不打开浏览器 |
| `decode <file \| ->` | 从 HTML、粘贴文本（`-` 读 stdin）或 PNG 读出隐水印载荷 |
| `config [show]` | 打印合并后的配置、每个键的来源（default / system / project）与两份配置文件路径、是否存在 |
| `config get <key>` | 读取单个键（点路径，如 `author.url`），输出值与来源 |
| `config set <key> <value> [--project]` | 写入系统级（默认）或项目级配置；值按键类型解析，校验不通过不写 |
| `config unset <key> [--project]` | 删除该层的该键，空对象一并清理 |

## 常见错误与处理

| 现象 | 原因 | 处理 |
|---|---|---|
| `<file>: <键>: 未知键（可用：…）` | 配置或内容 JSON 键名拼错 | 按提示的可用键改名 |
| `<file>: <键>: 期望 <类型>，实际 <类型>` | 值类型不符 | 改成期望类型；要沿用下一层配置时写 `null` |
| `topic: 期望安全文件名` | topic 含 `/`、空格或以符号开头 | 改成字母、数字、`. _ -` 组成的短名 |
| `blocks[i].<字段>: <块> 块缺少必填字段` | 块缺字段 | 按 content-schema 补齐 |
| `logo: 路径必须在项目根内` / `outDir: 不得指向项目根之外` | 项目级配置越界 | 改成项目根内的相对路径 |
| `页面须离线` | 图片 src 是远程 URL | 先下载到本地，再写相对路径 |
| `产物 N 字节，超过上限` | 内联图片过大 | 压缩或移除图片 |
| 浏览器没有打开 | 配置 `open: false` 或用了 `--no-open` | 直接给用户文件链接 |

## 参考

- 内容 JSON schema 与示例：见 [references/content-schema.md](references/content-schema.md)
- 内容块清单（块 → 用途 → 三种风格下的样子）：见 [references/blocks.md](references/blocks.md)
- 配置（两层、配置项、合并与校验）：见 [references/config.md](references/config.md)
- 水印与 decode：见 [references/watermark.md](references/watermark.md)

## 维护：重建渲染器

渲染器源码在 `renderer/`（Vite + React + Tailwind + shadcn，单文件输出）。改源码后：

```bash
pnpm -C <本目录>/renderer install --frozen-lockfile
pnpm -C <本目录>/renderer build   # 产物复制为 assets/renderer.html
node <本目录>/scripts/self-test.mjs
```

CLI 只依赖 Node 内置模块；`renderer/` 的 npm 依赖只用于构建模板，运行时不需要。
