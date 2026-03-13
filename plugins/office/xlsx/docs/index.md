# office-xlsx 插件文档

## 概述

office-xlsx 是一个基于 MCP 协议的 Excel 文件操作插件，提供对 .xlsx 文件的完整读写支持，并通过 Python 包装层提供格式转换、批量处理和智能分析功能。

## 架构

```
plugins/office/xlsx/
├── .claude-plugin/
│   └── plugin.json          # 插件配置和 MCP 服务定义
├── scripts/
│   ├── __init__.py
│   └── wrapper.py           # 包装层（格式转换、批量处理、分析）
├── skills/
│   └── office-xlsx-skills/
│       ├── SKILL.md          # 技能定义
│       └── examples.md       # 使用示例
├── docs/
│   ├── index.md              # 文档首页
│   └── api.md                # API 文档
├── pyproject.toml            # Python 依赖配置
├── README.md
└── llms.txt
```

## 组件说明

### MCP 服务（基础层）

使用 [mcp-excel-server](https://github.com/yzfly/mcp-excel-server) 提供 10 个基础 MCP 工具：读取、写入、分析、过滤、透视表、图表等。通过 `uvx mcp-excel-server` 启动。

### Python 包装层（增强层）

`scripts/wrapper.py` 提供 MCP 服务之外的额外功能：

- **格式转换**: xlsx <-> CSV, xlsx <-> JSON
- **批量处理**: 批量导入目录文件、批量导出工作表
- **统计分析**: 详细统计、相关性分析、图表生成（6 种类型）
- **智能洞察**: 数据质量评估、异常值检测、趋势分析

## 相关链接

- [API 文档](api.md)
- [mcp-excel-server GitHub](https://github.com/yzfly/mcp-excel-server)
