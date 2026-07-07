# 噪声分类 · 保留清单 · 忽略落点 —— git-commit 详表

主流程见 [../SKILL.md](../SKILL.md)。本文件是排除判断的全量依据。

## §1 噪声完整分类(分语言/工具链)

排除 = 不 `git add`;是否写忽略清单看 §3。

### 通用
| pattern | 说明 |
| --- | --- |
| `*.tmp` `*.temp` `*~` `*.bak` `*.old` `*.orig` `*.rej` | 临时/备份/合并残留 |
| `*.swp` `*.swo` `.#*` `#*#` | vim/emacs 交换锁文件 |
| `*.log` `logs/` `*.log.*` | 日志 |
| `.DS_Store` `._*` `.Spotlight-V100` `.Trashes` | macOS |
| `Thumbs.db` `ehthumbs.db` `Desktop.ini` | Windows |
| `.idea/` `*.iml` `.vscode/`(除团队约定的 `.vscode/settings.json`) `*.sublime-*` | 编辑器/IDE |

### Node/JS
| pattern | 说明 |
| --- | --- |
| `node_modules/` | 依赖,永不提交 |
| `dist/` `build/` `out/` `.next/` `.nuxt/` `.output/` `.svelte-kit/` | 构建产物 |
| `coverage/` `.nyc_output/` | 覆盖率 |
| `npm-debug.log*` `yarn-debug.log*` `yarn-error.log*` `.pnpm-debug.log*` | 包管理器日志 |
| `.cache/` `.parcel-cache/` `.turbo/` `.eslintcache` | 缓存 |

### Python
| pattern | 说明 |
| --- | --- |
| `__pycache__/` `*.py[cod]` `*$py.class` | 字节码 |
| `.venv/` `venv/` `env/` `ENV/` | 虚拟环境 |
| `*.egg-info/` `.eggs/` `build/` `dist/` `wheels/` | 打包产物 |
| `.pytest_cache/` `.ruff_cache/` `.mypy_cache/` `.tox/` `.coverage` `htmlcov/` | 测试/类型/覆盖率缓存 |

### JVM
| pattern | 说明 |
| --- | --- |
| `target/` `build/` `out/` | Maven/Gradle 产物 |
| `*.class` `*.jar`(除有意提交的) `*.war` | 编译产物 |
| `.gradle/` | Gradle 缓存 |

### Go / Rust / C/C++ / 其它
| pattern | 说明 |
| --- | --- |
| `*.o` `*.a` `*.so` `*.dylib` `*.exe` `*.out` | 目标/二进制 |
| `target/`(Rust) | Cargo 产物 |
| `bin/` `obj/`(.NET) | 编译产物 |
| `vendor/`(视项目约定,Go modules 下多不提交) | 依赖 vendoring |

### 密钥/凭证(命中 → 🔴 STOP,不排除了事,走 [secrets-and-cleanup.md](secrets-and-cleanup.md))
`.env` `.env.local` `.env.*.local`(保留 `.env.example` `.env.sample`)、`*.pem` `*.key` `*.p12` `*.pfx`、`id_rsa*` `id_ed25519*` `*.ppk`、`*credentials*` `*secret*` `.npmrc`(含 token 时) `.pypirc` `.netrc` `.aws/credentials`。

## §2 保留清单(看着像噪声,实为应提交)

**误排除会破坏 CI 可复现或团队一致性:**

| 文件 | 为什么保留 |
| --- | --- |
| `package-lock.json` `pnpm-lock.yaml` `yarn.lock` | JS 锁文件,固定依赖版本 |
| `uv.lock` `poetry.lock` `Pipfile.lock` `requirements.txt` | Python 锁/依赖 |
| `Cargo.lock`(应用) | Rust 锁(库项目可不提交,应用必提交) |
| `composer.lock` `Gemfile.lock` `go.sum` `go.mod` | PHP/Ruby/Go 锁 |
| `.gitkeep` `.gitignore` `.gitattributes` | git 元文件 |
| `.env.example` `.env.sample` | 环境变量模板(不含真值) |
| `.vscode/extensions.json` `.editorconfig` | 团队共享编辑器约定 |
| `Dockerfile` `docker-compose.yml` `Makefile` | 构建/编排定义 |
| CI 配置 `.github/` `.gitlab-ci.yml` | 流水线定义 |

判据:**文件影响他人如何构建/运行本项目 → 提交;仅你本地产生、他人重跑会重新生成 → 排除。**

## §3 忽略落点决策 + 去重 + 语法

### 三档 exclude 源
| 档 | 路径 | 作用域 | 随 clone 分发 |
| --- | --- | --- | --- |
| 项目忽略 | `<repo>/.gitignore` | 全项目所有人 | ✅ |
| 仓库本地 | `<repo>/.git/info/exclude` | 仅本地此 clone | ❌ |
| 全局 | `core.excludesFile`(默认 `~/.config/git/ignore` 或 `~/.gitignore_global`) | 本机所有仓库 | ❌ |

落点选择:
- **项目所有人都会产生**(构建/依赖/覆盖率/`.env`) → `.gitignore`,防他人误提交。
- **仅你的机器/编辑器/OS**(`.DS_Store` `.idea/` `*.swp`) → 全局 `core.excludesFile`(推荐,一次配全机受益)或 `.git/info/exclude`(只此仓)。理由:团队用不同编辑器,写进项目 `.gitignore` 是污染。

### 去重(追加前必查)
```bash
git check-ignore -v <path>        # 有输出=已被某规则忽略(附来源文件:行号),不重复加
git config --get core.excludesfile # 查全局档路径
```

### pattern 语法要点
- `dir/` 尾斜杠 = 只匹配目录。
- `*.log` 匹配任意层级;`/*.log` 只匹配根级。
- `!pattern` = 取消忽略(白名单),但**父目录已整个被忽略时无法再 include 子项**。要保留 `logs/.gitkeep` 须写:
  ```
  logs/*
  !logs/.gitkeep
  ```
  而非 `logs/` + `!logs/.gitkeep`(后者无效)。
- 追加时**只加本次命中的 pattern**,不塞 gitignore.io 百行模板(大量用不上的 pattern 是噪声)。
