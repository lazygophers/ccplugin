# llms.txt 插件文档

> llms.txt 标准插件 - 通过 Agent 自动生成符合 llmstxt.org 规范的文件

## 组件

| 类型 | 名称 | 文件 |
|---|---|---|
| Agent | llms-generator | `agents/llms-generator.md` |
| Agent | llms-validator | `agents/llms-validator.md` |
| Skill | llms-spec | `skills/llms-spec/SKILL.md` |
| Skill | llms-generate | `skills/llms-generate/SKILL.md` |

## 安装

```bash
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin llms@ccplugin-market
```
