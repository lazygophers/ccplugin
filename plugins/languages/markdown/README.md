# Markdown 插件

> Markdown 开发插件提供高质量的 Markdown 编写规范和技术文档指导

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin markdown@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install markdown@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **开发规范指导** - 完整的 Markdown 编写规范
  - **Markdown 规范** - 遵循 CommonMark 标准
  - **技术文档规范** - 清晰的文档结构
  - **Mermaid 图表规范** - 流程图、序列图最佳实践

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `markdown-core` | Markdown 核心规范 |
| Skill | `markdown-mermaid` | Mermaid 图表规范 |

## 核心规范

### 必须遵守

1. **标题层级** - 按层级递进，不跳级
2. **代码块** - 指定语言类型
3. **链接格式** - 使用相对路径或完整 URL
4. **列表格式** - 保持一致的缩进
5. **空行规范** - 元素之间使用空行分隔

### 禁止行为

- 标题层级跳跃
- 代码块不指定语言
- 使用 HTML 标签（除非必要）
- 过长的行（>120 字符）

## 最佳实践

### 文档结构

```markdown
# 项目名称

> 简短描述

## 简介

## 安装

## 使用

## API

## 贡献

## 许可证
```

### 代码块

````markdown
```python
def hello():
    print("Hello, World!")
```
````

## 参考资源

- [CommonMark 规范](https://commonmark.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

## 许可证

AGPL-3.0-or-later
