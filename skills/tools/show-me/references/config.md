# 配置

## 两层与优先级

| 优先级 | 来源 | 位置 |
|---|---|---|
| 1（最高） | `render --style` 参数、内容 JSON 的 `style` | 用户点名风格时由模型写入内容 JSON |
| 2 | 项目级配置 | `<项目根>/.claude/.show-me/config.json` |
| 3 | 系统级配置 | `~/.claude/.show-me/config.json` |
| 4（最低） | 内置默认 | `scripts/show-me.mjs` 的 `DEFAULTS` |

- 项目根 = `git rev-parse --show-toplevel`；不在 git 仓库内时取当前工作目录。
- 环境变量 `SHOW_ME_HOME` 覆盖系统级配置目录（其下的 `config.json`），用于测试与隔离环境。
- 两份配置文件都可不存在。

## 合并规则

- 对象按键逐层合并（`author`、`watermark.*`、`byType` 逐键）。
- 字符串、布尔、数字、数组整体替换。
- 任意键写 `null` 表示「用下一层的值」；全部为 `null` 时取内置默认。
- 风格决定顺序：`--style` > 内容 `style` > `byType[type]` > `style` > `paper`。

## 配置项

| 键 | 类型 | 默认 | 作用 |
|---|---|---|---|
| `style` | `paper` \| `sketch` \| `terminal` | `paper` | 默认风格 |
| `byType` | 对象：产物类型 → 风格 | `{}` | 按 `type` 指定风格，键限 `research plan compare review explain report spec` |
| `outDir` | 路径模板 | `.scratch/{topic}/reports` | 输出目录，相对项目根；`{topic}` 替换为内容 `topic` |
| `open` | boolean | `true` | 生成后用 `open`（macOS）/ `xdg-open` 打开；`--no-open` 优先 |
| `switcher` | boolean | `true` | 页面顶部是否显示三种风格切换 |
| `author.name` | string | `lazygophers/ccplugin` | 署名文字，也是水印载荷的 `author` |
| `author.url` | http(s) URL | `https://github.com/lazygophers/ccplugin` | 署名链接 |
| `logo` | 文件路径或 `null` | `null` | 页头 logo，`.png` / `.svg`，渲染时内联为 data URI。项目级相对项目根解析，系统级相对系统级配置目录解析 |
| `watermark.visible.enabled` | boolean | `true` | 显性水印开关 |
| `watermark.visible.text` | 模板字符串 | `{author} · {date}` | 显性水印文字，`{author}` = `author.name`，`{date}` = 生成日期 |
| `watermark.visible.opacity` | number 0–1 | `0.06` | 显性水印透明度 |
| `watermark.hidden.zeroWidth` | boolean | `true` | 正文段落零宽字符 |
| `watermark.hidden.meta` | boolean | `true` | `<meta name="show-me:*">` 与 HTML 注释 |
| `watermark.hidden.pattern` | boolean | `true` | 约 1% 不透明度背景编码图案 |
| `watermark.hidden.images` | boolean | `true` | 位图最低位、SVG `<metadata>` |

不可配置：页脚左段的 skill 名与版本（取 SKILL.md `version`）、项目地址。配置中出现 `footer` 等键按未知键报错。

## 校验

- 未知键、类型不符：渲染失败，退出码 2，stderr 每行一条：`<文件路径>: <键名>: 未知键（可用：…）` 或 `<文件路径>: <键名>: 期望 <类型>，实际 <类型>`。
- 项目级配置按不可信输入处理：`logo` 必须存在且解析后（含符号链接）位于项目根内；`outDir` 不得指向项目根之外。
- JSON 语法错误：`<文件路径>: JSON 解析失败：…`。

## config 命令

```bash
show-me config [show]                              # 合并结果 + sources（每个键来自 default / system / project）+ 两份文件路径与 exists
show-me config get <key>                           # {"key","value","source"}；对象键的 source 为其下各叶子键的来源
show-me config set <key> <value> [--project]       # 默认写系统级，--project 写项目级
show-me config unset <key> [--project]             # 删除该层的该键
```

- `<key>` 为点路径：`style`、`byType.explain`、`author.url`、`watermark.visible.text` 等；不在配置项表内的键报 `<key>: 未知键（可用：…）`，退出码 2。
- `<value>` 按键的类型解析：布尔只接受 `true` / `false`；数字按十进制解析；对象键（`author`、`byType`、`watermark` 等）接受 JSON；其余按原样字符串；字面量 `null` 写入 null（表示沿用下一层）。
- `set` 写入前用与渲染相同的校验规则检查整份文件（未知键、类型、取值范围；项目级 `logo` 必须在项目根内且存在，`outDir` 不得越出项目根），不通过则不写、退出码 2，报错含键名与期望类型。
- 写入方式：目录不存在时创建；先写同目录临时文件再 rename，保留文件中其他键。
- `unset` 删除叶子后自下而上清理变空的对象；键不存在时 `removed: false`，文件不改。

示例（`SHOW_ME_HOME` 指向临时目录时的实跑输出）：

```text
$ show-me config set author.url https://example.com/me
{"action":"set","layer":"system","file":"<系统级目录>/config.json","key":"author.url","value":"https://example.com/me"}
$ show-me config set byType.explain sketch --project
{"action":"set","layer":"project","file":"<项目根>/.claude/.show-me/config.json","key":"byType.explain","value":"sketch"}
$ show-me config get byType
{"key":"byType","value":{"explain":"sketch"},"source":{"byType.explain":"project"}}
$ show-me config set open yes
show-me: open: 期望 boolean，实际 "yes"        # 退出码 2，文件不变
$ show-me config unset byType.explain --project
{"action":"unset","layer":"project","file":"<项目根>/.claude/.show-me/config.json","key":"byType.explain","removed":true}
```

## 示例

系统级 `~/.claude/.show-me/config.json`：

```json
{ "style": "paper", "author": { "name": "落心", "url": "https://github.com/<user>" } }
```

项目级 `<项目根>/.claude/.show-me/config.json`：

```json
{ "byType": { "explain": "sketch" }, "watermark": { "visible": { "text": "内部资料 · {date}" } } }
```

合并结果：`style=paper`；`explain` 类用 `sketch`；署名「落心」链到个人主页；显性水印「内部资料 · 2026-11-28」。用 `show-me config show` 查看合并结果与每个键的来源：

```json
{ "sources": { "style": "system", "byType.explain": "project", "author.name": "system", "watermark.visible.text": "project", "open": "default" } }
```
