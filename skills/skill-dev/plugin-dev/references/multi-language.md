# 多语言脚本与分发

> 编译型语言陷阱 + 三种脚本分发方案 + 跨平台 + 共享代码。主 SKILL.md 流程 A 步骤 4 脚本行的细节层。

## 🔴 核心陷阱：`claude plugin add` 不编译不装依赖

安装只做三件事：
1. 复制插件文件到 `~/.claude/plugins/cache`
2. 解析 `plugin.json`
3. 注册 commands/agents/skills

**用户机器没装 go/rustc = 二进制源码跑不起来。** 没装 jq/pip3 = 脚本崩。

## 三种方案对比

| 方案 | 目录形态 | 适用 | 代价 |
|------|---------|------|------|
| **预编译多平台二进制**（推荐）| `bin/<tool>-<os>-<arch>[.exe]`，hook command 按平台选 | Go/Rust/C++ 重逻辑 | 每次发版交叉编译 4+ 平台 |
| **解释型脚本** | `scripts/*.py` / `.sh`，shebang `#!/usr/bin/env python3` | 轻逻辑、原型 | 需 SessionStart 后台装依赖 |
| **uvx/pyproject 分发** | `pyproject.toml` + `scripts/` as package；hook 调 `uvx --from . <entry>` | Python 重插件（version/notify 范式）| 用户需有 `uvx`；首次启动慢 |

详见 `docs/supported-languages.md` + `docs/compiled-languages-guide.md`。

## 方案 1：预编译多平台二进制

```
my-plugin/
├── bin/
│   ├── mytool-darwin-arm64     # macOS Apple Silicon
│   ├── mytool-darwin-amd64     # macOS Intel
│   ├── mytool-linux-amd64      # Linux
│   └── mytool-windows-amd64.exe
└── scripts/select-platform.sh  # wrapper 按平台选
```

- **hook command 选二进制**：
  ```bash
  ${CLAUDE_PLUGIN_ROOT}/bin/mytool-$(uname -s | tr A-Z a-z)-$(uname -m)
  ```
  或 wrapper 脚本 `case "$(uname -s)-$(uname -m)"` 分发
- 🛓 **禁只放 `mytool.go` 源码** — 装到用户机器编不出来
- 发版时 CI 交叉编译 4 平台（darwin-arm64/amd64, linux-amd64, windows-amd64）

## 方案 2：解释型脚本

```python
#!/usr/bin/env python3
import sys, json
def main():
    data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    # ...
if __name__ == "__main__":
    main()
```

- shebang `#!/usr/bin/env python3`（禁 `#!/usr/bin/python`）
- 外部依赖（jq/pip3 包）→ `requirements.txt` 列齐 + SessionStart 后台自装（skein 范式：`pip3 install -r requirements.txt >/dev/null 2>&1 &`）

## 方案 3：uvx / pyproject 分发（Python 重插件）

version / notify 真实用此模式。`pyproject.toml`：

```toml
[project]
name = "version"
version = "0.0.195"
description = "..."
requires-python = ">=3.11"
dependencies = ["click>=8.1.0", "lib"]

[tool.setuptools.packages.find]
where = ["."]
include = ["scripts*"]

[tool.setuptools.package-data]
"*" = ["*.py", "*.json", "*.md"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]   # 测试依赖独立
```

- `scripts/` 打成 package；`package-data` 含非 py 文件
- hook 经 `uvx --from ${CLAUDE_PLUGIN_ROOT} <entry>` 或装出的 console script 调
- 用户需有 `uvx`（uv 自带）；首次启动慢（装包）

### 跨插件共享代码走 lib 子目录

version pyproject 用 uv source 引本仓库 `lib/` 共享包：

```toml
[tool.uv.sources.lib]
git = "https://github.com/lazygophers/ccplugin"
subdirectory = "lib"
rev = "master"
```

- 多插件复用同一底层（schema/解析/CLI 框架）走此路
- 🛓 **禁**在各插件 `scripts/` 内重复粘代码（DRY）

## 跨平台（darwin / linux / WSL）

| 问题 | 约定 |
|------|------|
| **python3 不是 python** | shebang `#!/usr/bin/env python3`，禁假设 `python` 指向 py3 |
| **依赖显式化** | 用 `jq`/`pip3` 等外部工具时，`requirements.txt` 列齐 + SessionStart 后台自装；禁假设用户机器已装 |
| **路径禁含空格假设** | `${CLAUDE_PLUGIN_ROOT}` 含空格时，hook command 用引号包裹；脚本内 `os.path.join` 禁字符串拼 |
| **shell 便携** | hook 脚本 `#!/usr/bin/env bash` + `set -euo pipefail`；需兼容 sh 时禁 bashism（`[[ ]]` / `<(...)`）|
| **二进制按平台选** | darwin-arm64 / darwin-amd64 / linux-amd64 / windows-amd64.exe |

## 调试

- **`claude --debug`** — 看 plugin 加载顺序 / hook 触发 / 变量替换实况
- **加载失败二分** — 先 `jq .` 验 manifest → 体检查悬挂 → 只挂 skills 逐个加定位坏组件
- **hook 不触发** — 查 matcher 拼写 / event 名 / command 路径 / 脚本 `+x`
- 见 `hooks.md` 调试段

## tests/ 目录（cortex 范式）

```
my-plugin/
└── tests/
    ├── fixtures/           # 测试输入数据
    └── e2e-report.md       # 端到端测试报告
```

- 重逻辑插件建议加 `tests/`，跑 `pytest`（version pyproject 的 `dev` optional dep）
- hook 脚本的纯函数（解析/路径计算）单测覆盖；副作用部分手测
