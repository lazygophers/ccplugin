# LLMS.txt Plugin

> 通过 Agent 自动生成符合 [llms.txt 标准](https://llmstxt.org/) 的文件

## 功能

- **Agent 驱动**：通过 `llms-generator` Agent 智能扫描并生成文件
- **自动扫描项目**：识别 README、配置文件、文档目录等
- **混合链接支持**：同时支持本地文件路径和远程 URL
- **技能标准**：内置 LLMS.txt 标准规范，确保生成文件符合标准

## 安装

```bash
/plugin install ./plugins/llms
```

## 使用

### 通过 Agent 生成

直接请求 Claude Code 生成 llms.txt：

```
请为当前项目生成 llms.txt 文件
```

Agent 会自动：
1. 扫描项目文件
2. 提取项目信息
3. 生成符合标准的 llms.txt
4. 创建 `.llms.json` 配置文件

### 手动编辑配置

生成后，可以编辑 `.llms.json` 来调整内容：

```json
{
  "project_name": "项目名称",
  "description": "项目描述",
  "details": [
    "项目详细信息",
    "- 重要说明"
  ],
  "sections": {
    "Docs": [
      {
        "title": "README",
        "path": "README.md",
        "description": "项目说明文档"
      }
    ],
    "Examples": [],
    "Optional": []
  }
}
```

然后请求重新生成：
```
根据 .llms.json 配置重新生成 llms.txt
```

## LLMS.txt 标准格式

生成的文件遵循以下格式：

```markdown
# 项目名称

> 项目简短摘要

项目详细信息

## Docs

- [README](README.md): 项目说明文档
- [API 文档](docs/api.md): API 参考

## Examples

- [示例1](examples/example1.py): 基本用法

## Optional

- [扩展文档](https://example.com/docs.md): 外部文档
```

### 格式说明

| 部分 | 必需 | 说明 |
|------|------|------|
| H1 标题 | ✅ | 项目/网站名称 |
| 引用块 | ❌ | 项目摘要 |
| 详细内容 | ❌ | 段落、列表等（不含标题） |
| H2 部分 | ❌ | 文件列表 |
| Optional | ❌ | 可在短上下文时跳过 |

## 链接格式

### 本地文件

```markdown
- [API 文档](docs/api.md): API 参考
```

### 远程 URL

```markdown
- [外部文档](https://example.com/docs): 外部资源
```

## Agent 工作流程

1. **扫描项目**
   - README.md / pyproject.toml / package.json
   - docs/、examples/ 等目录

2. **提取信息**
   - 项目名称、描述
   - 文档文件列表
   - 示例文件列表

3. **生成文件**
   - 按照 LLMS 标准格式
   - 创建 .llms.json 配置

4. **验证格式**
   - 检查是否符合标准
   - 验证链接有效性

## 技能规范

插件包含 `llms-standard` 技能，定义了：

- LLMS.txt 标准格式
- 链接格式规范
- 验证清单
- 完整示例

## 相关链接

- [LLMS.txt 标准](https://llmstxt.org/)
- [CCPlugin Market](https://github.com/lazygophers/ccplugin)
- [Claude Code](https://claude.ai/code)

## License

AGPL-3.0-or-later
