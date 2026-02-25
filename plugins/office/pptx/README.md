# Office Pptx 插件

> PowerPoint pptx 文件读写和幻灯片操作插件。基于 MCP 协议提供 PowerPoint 操作工具。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-pptx@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install office-pptx@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **读取 pptx 文件** - 读取 PowerPoint 演示文稿
- **写入 pptx 文件** - 创建 PowerPoint 演示文稿
- **幻灯片操作** - 添加、删除、修改幻灯片
- **格式支持** - 支持文本、图片、表格等元素

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `office-pptx-skills` | PowerPoint 操作技能 |
| MCP Server | `pptx` | PowerPoint MCP 服务器 |

## MCP 工具

| 工具名称 | 描述 |
|---------|------|
| `read_pptx` | 读取 PowerPoint 文件 |
| `write_pptx` | 写入 PowerPoint 文件 |
| `add_slide` | 添加幻灯片 |
| `list_slides` | 列出幻灯片 |

## 快速开始

### 读取 PowerPoint 文件

```
读取 presentation.pptx 文件的内容
```

### 创建 PowerPoint 文件

```
创建一个新的演示文稿，包含标题页和内容页...
```

### 添加幻灯片

```
在演示文稿中添加一张新幻灯片...
```

## 许可证

MIT
