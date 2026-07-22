# CLI 媒介 · 风格模板（命名 / 输出 / 错误 / help 样式）

CLI 风格 = 命名风格 + 输出样式 + 错误语气 + help 排版的一致性。本文件给方法论 + **现成风格模板**，复制即用。布局见 [layout.md](layout.md)，场景见 [scenes.md](scenes.md)，组件见 [components.md](components.md)。

## 选型流程

1. **定调性**：工具面向开发者 / 运维 / 终端用户？严肃 or 友好？
2. **出三方向**：风格组合（极简 / 详细 / 友好），差异化
3. **并排对比**：同命令在三种风格下的实际输出，选
4. **固化**：风格写进 help / 错误 / 输出模板，全局一致

## 命名风格

| 风格 | 命令 | flag | 示例 |
|------|------|------|------|
| 小写连词 | `kebab-case` | `--dry-run` | `git push --force-with-lease` |
| 动词主导 | 动词打头 | 短名高频 | `gh pr create --draft` |
| 名字空间 | `ns action` | `--output=json` | `kubectl get pods -o wide` |

统一用一种，禁混（别有的命令 kebab 有的 snake）。

---

## 现成风格模板

### 模板 1 · 极简 Unix 风（严肃、开发者）

调性：安静、可组合、Unix 传统。

```
$ tool build
$ tool build --verbose
compiling src/... done (1.2s)
$

# 错误
$ tool deploy prod
error: no such environment "prod"
  run `tool env list` to see available
$ echo $?
1
```

要点：

- 成功无输出（或仅结果）
- 错误前缀 `error:`，一行，带修复提示
- 无 emoji、无彩色（除非 `--color`）
- 进度仅在 verbose

### 模板 2 · 彩色友好风（现代 CLI，如 npm / cargo）

调性：彩色状态、emoji 点缀、信息丰富。

```
$ tool build
⚙  Building project...
✔  Compiled 42 files (1.2s)
📦 Output: dist/app

$ tool deploy prod
✖  Failed: environment "prod" not found
   ℹ  run `tool env list` to see available
$ echo $?
1
```

要点：

- 前缀图标（⚙ ✔ ✖ ℹ ⚠）
- 绿成功 / 红失败 / 黄警告 / 蓝信息
- TTY 检测自动关色关图
- 步骤化输出

### 模板 3 · 结构化表格风（数据型工具，如 docker / kubectl）

调性：表格为主、列对齐、可 `-o` 切格式。

```
$ tool list
NAME        STATUS    AGE
app-1       running   3d
app-2       stopped   1h
app-3       running   12d

$ tool list -o json
[{"name":"app-1","status":"running","age":"3d"}, ...]
```

要点：

- 默认人类表格，`-o json/yaml/wide` 切程序格式
- 列对齐，数字右对齐
- 状态用标签词（running/stopped）不靠色
- 宽表自动截断 + 省略

### 模板 4 · 向导对话风（onboarding / init 类）

调性：交互式、引导、可选。

```
$ tool init
? Project name (my-app)
? Template: (Use arrow keys)
❯ library
  cli
  server
? Enable telemetry? (y/N)
✔  Created my-app
```

要点：

- 默认值在括号、Enter 接受
- 非 TTY 时 fallback 到 flag（`tool init --name x --template cli --no-telemetry`）
- 进度可中断

---

## 输出样式约定

### 彩色语义（模板 2 用）

| 语义 | 色 | 前缀 |
|------|----|------|
| 成功 | 绿 | `✔` |
| 失败 | 红 | `✖` |
| 警告 | 黄 | `⚠` |
| 信息 | 蓝 | `ℹ` |
| 进行中 | 青 | `⚙` / spinner |

ANSI 备用（非 TTY 关）：

```
RED=\033[31m  GREEN=\033[32m  YELLOW=\033[33m  BLUE=\033[34m  RESET=\033[0m
```

### Shell 兼容速查

彩色 / 交互输出跨 shell 差异：

| Shell | ANSI 色 | Unicode emoji | 补全框架 | 备注 |
|------|:---:|:---:|------|------|
| bash | ✅ | ✅ | bash-completion | Linux 默认，兼容底线 |
| zsh | ✅ | ✅ | zsh-completions / Oh-My-Zsh | macOS 默认 |
| fish | ✅ | ✅ | 内置(无需框架) | 语法不同，脚本不能复用 |
| PowerShell | ⚠️ 需 `$PSStyle` | ✅ | PSReadLine | Win 默认，ANSI 需 7.2+ |
| nushell | ⚠️ 结构化输出 | ✅ | 内置 | 数据优先，禁纯文本污染 |
| cmd.exe | ❌ 有限 | ⚠️ 乱码 | 无 | 仅作底线兼容，降级无色无 emoji |

### 跨 shell 安全原则

- **TTY 检测**：`isatty(stdout)` 为假（管道 / 重定向 / CI）→ 全关色、全关 emoji、表格降级为 `-o` 结构化输出
- **emoji**：bash/fish 通用；PowerShell 可用；cmd.exe / 管道降级纯 ASCII 前缀（`>>` `!!` `--` `!!`）
- **补全**：生成时按 shell 分文件（`completion.bash` / `_tool.zsh` / `tool.fish` / `_tool.ps1`），别指望一份通吃
- **脚本安全**：输出禁含未转义的特殊字符（`\x1b` 在非 TTY 会污染日志）

### help 排版风格

统一：

- 用法行用 `<>` `[]` `|` `...` 约定
- flags 表三列：短名长名、描述、默认值
- examples 段给可直接复制的命令
- 末尾提示「Run `tool <cmd> --help` for more」

## 错误语气

- 严肃风：`error: <what>` + `  fix: <how>`，无情绪
- 友好风：`✖ <what>` + `  ℹ <how>`，略温和
- 都要：具体值 + 可执行修复建议

## 自检

- [ ] 命名风格统一（不混 kebab/snake）
- [ ] 输出风格统一（三方向选定一种）
- [ ] 彩色 TTY 检测自动关
- [ ] 错误带修复建议
- [ ] help 排版一致
