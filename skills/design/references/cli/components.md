# CLI 媒介 · 组件（flags / 输出 / 错误 / 帮助）

CLI 的「组件」是 flags、参数、输出块、错误信息、帮助文本这些积木。布局见 [layout.md](layout.md)，场景见 [scenes.md](scenes.md)，风格见 [style.md](style.md)。

## flags 设计

### 命名

- 长名 `kebab-case`（`--dry-run`），禁下划线
- 布尔 flag 默认 false，`--no-` 前缀关闭（`--no-color`）
- 值 flag 支持空格与等号：`--output out.txt` 与 `--output=out.txt`
- 短名（`-f`）留给高频 flag

### 默认值

- 有合理默认（零参数能跑出有用结果最佳）
- 默认非破坏性（不默认删、不默认覆盖、不默认发副作用请求）

### 全局 flag（跨子命令统一）

| flag | 作用 |
|------|------|
| `--verbose` / `-v` | 详细输出 |
| `--quiet` / `-q` | 静默 |
| `--config <file>` | 指定配置文件 |
| `--no-color` | 关彩色 |
| `--json` / `--output=` | 输出格式 |
| `--dry-run` | 试运行不落盘 |

## 输出组件

### 表格（人）

列对齐，右对齐数字、左对齐文字、状态用标签不用色块文字。

### JSON（程序）

```json
{ "items": [...], "count": 3, "status": "ok" }
```

稳定 schema、UTF-8、`--jq` 友好。

### 进度

- 进度条：已知时长（TTY 时）
- spinner：未知时长
- 阶段日志：非 TTY / CI

### 退出码（关键组件）

| 码 | 语义 |
|----|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 用法错误（参数错、flag 不认识） |
| 特定码 | 工具自定义（认证失败、未找到） |

退出码是脚本判失败的唯一可靠信号，禁成功返回非 0。

## 错误信息组件

三段式：**发生了什么 + 为什么 + 怎么修**。

```
error: cannot connect to database at localhost:5432
  cause: connection refused
  fix:  is postgres running? try `pg_ctl start` or check --db-host
```

要点：

- 错误类型名给开发者，人话原因给用户
- 有具体值（哪个文件、哪个 key、哪个端口）
- 建议下一条命令时给可直接复制的命令
- 多错误批量报（lint 类一次报全部）

## 帮助文本组件

三层：

1. **`--help`（每命令）**：一句话用途 + 用法行 + flags 表（短名 长名 描述 默认值）
2. **无参数 / `-h`**：简短用法 + 提示去 `--help`
3. **顶级 help**：命令列表（能力地图）+ 全局 flags

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

## 自检

- [ ] flag 长短名齐全，kebab-case
- [ ] 退出码语义正确（成功 0、用法错 2）
- [ ] 错误三段（什么 / 为什么 / 怎么修）
- [ ] `--help` 三层齐全
- [ ] 输出 TTY 检测自动调整
