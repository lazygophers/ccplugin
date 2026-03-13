# office-pptx

PowerPoint pptx 文件读写和幻灯片操作插件。基于 MCP 协议提供 PowerPoint 操作工具。

## 安装

```bash
claude plugin add ./plugins/office/pptx
```

## 功能特性

- 34 个专业工具，覆盖 PowerPoint 操作全流程
- 11 个功能模块：演示文稿管理、幻灯片操作、内容编辑、主题样式等
- 25+ 内置模板，支持快速创建专业演示文稿
- 支持文本、图片、表格、图表等多种内容类型
- 幻灯片布局和母版管理
- 批量操作和自动化支持

## 快速开始

安装插件后，可以直接在 Claude Code 中操作 PowerPoint 文件：

- 创建和编辑演示文稿
- 添加和管理幻灯片
- 插入文本、图片、表格等内容
- 应用主题和样式模板
- 导出和转换格式

## 技术实现

基于 [Office-PowerPoint-MCP-Server](https://github.com/GongRzhe/Office-PowerPoint-MCP-Server) MCP 服务，通过 `uvx --from office-powerpoint-mcp-server ppt_mcp_server` 运行。

## 许可证

AGPL-3.0-or-later
