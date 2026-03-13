# office-docx

Word docx 文件读写和文档操作插件。基于 MCP 协议提供 Word 操作工具。

## 安装

```bash
claude plugin add ./plugins/office/docx
```

## 功能特性

- 创建和编辑 Word 文档
- 段落和文本管理（添加、修改、删除）
- 表格操作（创建、编辑、格式化）
- 图片插入和管理
- 页眉页脚设置
- 样式和格式化
- 文档属性管理
- 支持 37+ 种操作工具

## 快速开始

安装插件后，可以直接在 Claude Code 中操作 Word 文件：

- 创建新的 Word 文档
- 读取和修改文档内容
- 添加表格、图片等元素
- 设置文档格式和样式

## 技术实现

基于 [office-word-mcp-server](https://github.com/GongRzhe/Office-Word-MCP-Server) MCP 服务，通过 `uvx --from office-word-mcp-server word_mcp_server` 运行。

## 许可证

AGPL-3.0-or-later
