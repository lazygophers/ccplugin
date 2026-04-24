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

安装插件后，直接用自然语言描述需求即可：

```
"创建一个 10 页的项目汇报 PPT，使用蓝色主题"
"在 slides.pptx 第 3 页后插入一张包含表格的幻灯片"
"读取 presentation.pptx 并提取所有文本内容"
```

## 技术实现

基于 [Office-PowerPoint-MCP-Server](https://github.com/GongRzhe/Office-PowerPoint-MCP-Server) MCP 服务，通过 `uvx --from office-powerpoint-mcp-server ppt_mcp_server` 运行。

## 许可证

AGPL-3.0-or-later
