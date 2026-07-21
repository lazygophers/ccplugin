# CLI 媒介 · 命令结构与布局

命令结构是 CLI 的信息架构——决定用户怎么发现和记忆能力。场景见 [scenes.md](scenes.md)，组件（flags/输出/错误）见 [components.md](components.md)，命名与输出风格见 [style.md](style.md)。

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
- 顶级命令列表即工具能力地图，命名覆盖全部主功能

## 参数布局（Positional vs Flag）

| 形式 | 用 |
|------|---|
| positional | 必填、顺序自然、少量（`cp SRC DEST`） |
| flag | 可选、无序、布尔或键值（`--force`、`--output=out.txt`） |

- 必填用 positional，可选附加用 flag
- 超过 3 个 positional 用户记不住顺序 → 改 flag
- 每个 flag 有长名（`--force`）+ 短名（`-f`），短名留给高频

## 用法行约定（布局语法）

标准占位符：

- `<>` 必填 positional
- `[]` 可选
- `|` 互斥
- `...` 可重复

```
Usage: tool <command> [--flag <value>] [--verbose] [args...]
```

布局原则：

- 用法行简短，一眼看出怎么调
- 子命令各有用法行
- examples 段放具体场景命令

## 信息层级

```
tool                      ← 顶级 help = 能力地图
  └─ <command>            ← 子命令 help = 该命令用法 + flags
       └─ --help          ← 详细 help
```

三层帮助（详见 [components.md](components.md) 帮助文本段）：顶级 / 子命令 / `-h` 简短。

## 自检

- [ ] 子命令深度 ≤2
- [ ] 命令名覆盖全部主功能（能力地图完整）
- [ ] positional ≤3，超出改 flag
- [ ] 用法行用标准占位符约定
