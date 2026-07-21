# CLI-Design · 命令行接口设计

好的 CLI 像一门小语言：可猜、可组合、可脚本化、出错说人话。帮用户做命令结构、参数、输出、错误、帮助层面的设计决策。

## 适用 / 不适用

适用：命令行工具、devops 工具、代码生成器、构建工具、任何 `./tool <command>` 形态。

不适用：终端全屏交互 UI（→ tui-design）、Web（→ html-design）、App（→ app-design）。

## 设计原则（POSIX/GNU 传统 + 现代 UX）

1. **可猜**：命令与 flag 名字能猜到（`git status`、`docker run`）
2. **可组合**：stdin/stdout 管道友好，纯文本可管道
3. **可脚本化**：稳定输出、退出码语义、`--json` 机器可读
4. **说人话**：错误信息给原因 + 修复建议，不只甩 stack
5. **一致**：全局 flag 统一（`--verbose` / `--quiet` / `--config`）
6. **幂等默认**：危险操作要确认或 `--dry-run`

## 核心硬门 · 三方向初稿（100% 必走）

新 CLI 接口设计先出**三个差异化的命令结构方案**（如：扁平子命令 vs 名字空间分层 vs 动词-名词式），等用户选定。

## 决策路由

| 决策层 | 选什么 |
|--------|--------|
| 命令结构 | 单命令 / 子命令树 / 动词-名词 / 名字空间 |
| 参数形式 | positional vs flag、长短名、默认值 |
| 输出 | 人类可读 vs JSON vs 表格 vs 静默 |
| 交互 | 纯非交互 / 非交互默认+交互可选 / 全交互向导 |
| 配置 | flag > env > 配置文件 > 默认，优先级链 |

## 命令结构选择

| 结构 | 示例 | 何时用 |
|------|------|--------|
| 扁平单命令 | `curl <url>` | 单一功能工具 |
| 子命令树 | `git status / commit / push` | 多功能、功能正交 |
| 动词-名词 | `gh pr create / pr list` | 操作对象明确、组合清晰 |
| 名字空间 | `kubectl get pods / get svc` | 对象类型多、动词复用 |

原则：

- 子命令深度 ≤2 层（`tool ns action`），再深难记
- 常用命令给短别名（`git co` = checkout）
- 顶级命令列表即工具能力地图，命名要覆盖全部主功能

## 参数设计

### Positional vs Flag

| 形式 | 用 |
|------|---|
| positional | 必填、顺序自然、少量（`cp SRC DEST`） |
| flag | 可选、无序、布尔或键值（`--force`、`--output=out.txt`） |

- 必填用 positional，可选附加用 flag
- 超过 3 个 positional 用户记不住顺序 → 改 flag
- 每个 flag 有长名（`--force`）+ 短名（`-f`），短名留给高频

### 命名

- 长名用 `kebab-case`（`--dry-run`），禁下划线
- 布尔 flag 默认 false，`--no-` 前缀关闭（`--no-color`）
- 值 flag 支持空格与等号两种：`--output out.txt` 与 `--output=out.txt`

### 默认值

- 有合理默认（零参数能跑出有用结果最佳）
- 默认非破坏性（不默认删、不默认覆盖、不默认联网发副作用请求）

## 输出设计

### 格式分层

| 受众 | 格式 | 触发 |
|------|------|------|
| 人（终端） | 彩色 + 表格 + 进度 | 默认 TTY |
| 脚本（管道） | 纯文本无色 | 检测非 TTY 自动关色 |
| 程序 | JSON / YAML | `--json` / `--output=json` |

规则：

- **TTY 检测自动关色**：管道到 `less` / 文件时别吐 ANSI 转义
- **成功安静**：默认成功只输出关键结果，`--verbose` 才详述
- **进度可关**：长任务进度条在非 TTY 关掉，或改输出阶段日志
- **表格对齐**：人类表格列对齐；JSON 输出别混表格

### 退出码

| 码 | 语义 |
|----|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 用法错误（参数错、flag 不认识） |
| 特定码 | 工具自定义（如认证失败、未找到）可分级 |

退出码是脚本判失败的唯一可靠信号，禁成功返回非 0。

## 错误信息

好的错误三段：**发生了什么 + 为什么 + 怎么修**。

```
✗ 好：
error: cannot connect to database at localhost:5432
  cause: connection refused
  fix:  is postgres running? try `pg_ctl start` or check --db-host

✗ 差：
Error: ConnectionError
```

- 错误类型名给开发者，人话原因给用户
- 有具体值（哪个文件、哪个 key、哪个端口）
- 建议下一条命令时给可直接复制的命令
- 多错误批量报（lint 类工具一次报全部，别一次一个让用户跑 N 次）

## 帮助文本

三层帮助：

1. **`--help`（每命令）**：一句话用途 + 用法行 + flags 表（短名 长名 描述 默认值）
2. **无参数运行 / `-h`**：简短用法 + 提示去 `--help`
3. **顶级 help**：命令列表（工具能力地图）+ 全局 flags

```
Usage: tool <command> [flags]

Commands:
  build    Build the project
  test     Run tests
  deploy   Deploy to environment

Global Flags:
  -v, --verbose   Verbose output
      --config F  Config file (default ~/.toolrc)

Run 'tool <command> --help' for command-specific help.
```

- 用法行用标准约定：`<>` 必填、`[]` 可选、`|` 或、`...` 重复
- examples 段放具体场景命令
- 帮助也是设计，花时间写

## 配置优先级

稳定优先级链（高 → 低）：

```
命令行 flag > 环境变量 > 项目配置文件 > 全局配置文件 > 内置默认
```

- 每个配置项五层都能设
- env 用统一前缀（`TOOL_DB_HOST`）
- 配置文件支持项目级 + 全局级，项目级覆盖全局
- `--config` 可指定文件路径

## 交互

默认非交互（可脚本化）。需要交互时：

- 检测非 TTY 时 fallback 到 flag（禁在管道里卡住等输入）
- 危险操作（删除 / 覆盖 / 不可逆）要确认，或给 `--yes` 跳过
- 向导模式（`tool init`）可选，但永远有非交互等价 flag 路径

## 自检清单

- [ ] 零参数能跑出有用结果或明确引导
- [ ] flag 有长 + 短名，命名 kebab-case
- [ ] TTY 检测自动关色 / 关进度
- [ ] 退出码语义正确（成功 0、用法错 2）
- [ ] 错误三段（什么 / 为什么 / 怎么修）
- [ ] `--help` 三层齐全
- [ ] 配置五层优先级链
- [ ] 非交互可跑（管道不卡）
