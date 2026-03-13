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

安装插件后，可以直接在 Claude Code 中操作 Excel 文件：

- 读取 Excel 文件内容
- 修改单元格数据
- 创建新的工作表
- 进行数据分析

## 技术实现

基于 [mcp-excel-server](https://github.com/yzfly/mcp-excel-server) MCP 服务，通过 `uvx` 运行。

## 许可证

AGPL-3.0-or-later
