# Statusline 重构文档

## 概述

Statusline 模块提供模块化、可扩展的状态栏显示功能。重构后的架构采用分层设计，支持多种布局模式、主题系统和增量渲染。

## 功能特性

- **模块化架构**: 清晰的模块划分，易于维护和扩展
- **多种布局模式**: 支持扩展布局和紧凑布局
- **主题系统**: 内置多种主题，支持自定义主题
- **增量渲染**: 只更新变化的部分，提高性能
- **缓存策略**: 多级缓存，提高查询性能
- **向后兼容**: 提供兼容层，平滑迁移

## 快速开始

### 基本使用

```python
from scripts.statusline.config.manager import get_default_config
from scripts.statusline.core.loop import StatuslineLoop

# 创建配置
config = get_default_config()

# 创建并启动主循环
loop = StatuslineLoop(config)
loop.start()
```

### 处理单个 Transcript

```python
from scripts.statusline.config.manager import get_default_config
from scripts.statusline.core.loop import StatuslineLoop

# 创建配置
config = get_default_config()

# 处理 transcript
loop = StatuslineLoop(config)
result = loop.process('{"role": "user", "content": "Hello"}')
print(result)
```

### 自定义配置

```python
from scripts.statusline.config.manager import Config, LayoutMode

# 创建自定义配置
config = Config(
    layout_mode=LayoutMode.COMPACT,
    theme="dark",
    layout_width=100,
    show_user=True,
    show_progress=True,
    show_resources=True,
)

# 使用自定义配置
loop = StatuslineLoop(config)
```

## 架构设计

### 模块结构

```
scripts/statusline/
├── config/          # 配置管理
├── utils/           # 工具函数
├── parser/          # 解析器
├── tracker/         # 状态追踪
├── layout/          # 布局系统
├── renderer/        # 渲染引擎
└── core/            # 核心逻辑
```

### 数据流

```
输入 → 解析器 → 事件模型 → 状态聚合 → 缓存 → 布局 → 渲染 → 输出
```

## 更多文档

- [快速开始](getting-started.md)
- [API 参考](api-reference.md)
- [配置指南](configuration.md)
- [主题定制](themes.md)
- [布局开发](layouts.md)
- [迁移指南](migration.md)
