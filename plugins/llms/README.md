# llms.txt 插件

> llms.txt 标准插件 - 通过 Agent 自动生成符合 llmstxt.org 规范的文件

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin llms@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install llms@ccplugin-market
```

## 功能特性

- **Agent 驱动** — `llms-generator` 生成、`llms-validator` 验证
- **规范知识库** — 多文件 skill 组织，按需加载 llmstxt.org 完整规范
- **自动扫描** — 识别项目类型、文档目录、配置文件
- **配置管理** — `.llms.json` 支持增量更新
- **上下文变体** — 可选生成 `llms-ctx.txt` / `llms-ctx-full.txt`
- **输入提醒 Hook** — 用户提交涉及项目/文档/插件变更的请求时，提醒完成后维护 `llms.txt` / `.llms.json`

## 包含组件

| 类型 | 名称 | 描述 |
|---|---|---|
| Agent | `llms-generator` | 生成/更新 llms.txt |
| Agent | `llms-validator` | 验证 llms.txt 合规性 |
| Skill | `llms-spec` | 规范知识（格式/验证/案例/变体/工具） |
| Skill | `llms-generate` | 生成流程（扫描/配置） |
| Hook | `UserPromptSubmit` | 项目/文档/插件变更请求时提醒维护 llms.txt |

## 使用方式

### 生成 llms.txt

```
请为当前项目生成 llms.txt 文件
```

### 验证 llms.txt

```
请验证当前项目的 llms.txt 是否符合规范
```

### 手动编辑后重新生成

编辑 `.llms.json` 后：

```
根据 .llms.json 配置重新生成 llms.txt
```

## llms.txt 标准格式

| 部分 | 必需 | 说明 |
|---|---|---|
| H1 标题 | ✅ | 项目/网站名称（唯一必需部分） |
| 引用块 | ❌ | 项目摘要 |
| 详细内容 | ❌ | 段落、列表（不含标题） |
| H2 部分 | ❌ | 文件列表 |
| `## Optional` | ❌ | 短上下文时可跳过 |

## 项目结构

```
plugins/llms/
├── agents/
│   ├── llms-generator.md      # 生成 Agent
│   └── llms-validator.md      # 验证 Agent
├── skills/
│   ├── llms-spec/             # 规范知识
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── format.md
│   │       ├── validation.md
│   │       ├── examples.md
│   │       ├── ctx-variants.md
│   │       └── integrations.md
│   └── llms-generate/         # 生成流程
│       ├── SKILL.md
│       └── references/
│           ├── scanning.md
│           └── config.md
├── docs/
├── llms.txt
└── README.md
```

## 相关链接

- [llms.txt 标准](https://llmstxt.org/)
- [GitHub 仓库](https://github.com/AnswerDotAI/llms-txt)
- [CCPlugin Market](https://github.com/lazygophers/ccplugin)

## 许可证

AGPL-3.0-or-later
