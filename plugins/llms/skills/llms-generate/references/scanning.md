# 项目扫描策略

## 配置文件识别

按优先级检测项目元数据：

| 文件 | 提取信息 |
|---|---|
| `package.json` | `name`, `description`, `repository`, `homepage` |
| `pyproject.toml` | `[project]` 下 `name`, `description` |
| `Cargo.toml` | `[package]` 下 `name`, `description` |
| `go.mod` | `module` 路径 |
| `README.md` | 项目标题、首段描述 |

## 文档目录发现

| 目录 | 分组 |
|---|---|
| `docs/`, `doc/`, `documentation/` | Docs |
| `examples/`, `example/`, `examples/` | Examples |
| `guides/`, `tutorials/` | Docs |
| `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` | Optional |

## 文件类型过滤

### 包含

- `.md` Markdown 文档
- `.mdx` MDX 文档
- `.rst` reStructuredText
- `.txt` 纯文本（如 README.txt）
- `.py` / `.js` / `.ts` 示例代码

### 排除

- `node_modules/`, `vendor/`, `.git/`
- 构建输出：`dist/`, `build/`, `out/`
- 锁文件：`*.lock`, `package-lock.json`
- 自动生成：`*.min.js`, `*.map`

## 元数据提取优先级

1. 已有 `.llms.json` → 以配置为准
2. `package.json` / `pyproject.toml` → 提取 name + description
3. `README.md` H1 + 首段 → 降级方案
4. 目录名 → 最终降级

## 扫描流程

1. 查找 `.llms.json` → 存在则读取跳至步骤 5
2. 检测项目类型（`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`）
3. 提取项目名称和描述
4. 扫描文档/示例目录，按规则分组
5. 构建配置数据结构（参见 config.md）
6. 输出 `llms.txt` + `.llms.json`
