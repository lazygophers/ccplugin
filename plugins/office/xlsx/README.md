# Office Xlsx 插件

> Excel xlsx 文件读写和数据分析插件。基于 MCP 协议提供 Excel 操作工具。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-xlsx@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install office-xlsx@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **读取 xlsx 文件** - 使用 pandas 读取 Excel 文件
- **写入 xlsx 文件** - 使用 openpyxl 写入 Excel 文件
- **数据分析** - 支持数据统计和分析
- **多工作表支持** - 支持多工作表操作

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `office-xlsx-skills` | Excel 操作技能 |
| MCP Server | `xlsx` | Excel MCP 服务器 |

## MCP 工具

| 工具名称 | 描述 |
|---------|------|
| `read_xlsx` | 读取 Excel 文件 |
| `write_xlsx` | 写入 Excel 文件 |
| `analyze_xlsx` | 分析数据 |
| `list_sheets` | 列出工作表 |

## 快速开始

### 读取 Excel 文件

```
读取 data.xlsx 文件的内容
```

### 写入 Excel 文件

```
创建一个新的 Excel 文件，包含以下数据...
```

### 数据分析

```
分析 sales.xlsx 中的销售数据，计算总和和平均值
```

## 许可证

MIT
