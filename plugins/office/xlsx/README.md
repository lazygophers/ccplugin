# office-xlsx

Excel xlsx 文件读写和数据分析插件。基于 MCP 协议提供 Excel 操作工具。

## 安装

```bash
claude plugin add ./plugins/office/xlsx
```

## 功能特性

- 读取 Excel 文件内容和结构
- 创建和编辑 Excel 工作簿
- 工作表管理（创建、删除、重命名）
- 单元格数据读写
- 数据分析和统计

## 快速开始

安装插件后，直接用自然语言描述需求即可：

```
"读取 sales.xlsx 并统计每月销售额"
"创建一个 Excel 文件，包含用户列表和三列数据"
"把 data.csv 转换为 xlsx 格式"
```

## 技术实现

基于 [mcp-excel-server](https://github.com/yzfly/mcp-excel-server) MCP 服务，通过 `uvx` 运行。

## 许可证

AGPL-3.0-or-later
