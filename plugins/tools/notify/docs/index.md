# Notify 插件文档

> 系统通知插件 - 通过系统通知向用户实时提示会话状态变更

## 目录

1. [概述](index.md)
2. [Hook 事件](hooks.md)
3. [配置指南](configuration.md)
4. [故障排除](troubleshooting.md)

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin notify@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install notify@ccplugin-market
```

## 版本

当前版本：0.1.0

## 核心设计

- **默认配置在 Python**：`scripts/config.py` 定义全部 29 个 hook 的默认 message
- **配置只读禁止写入**：用户只能覆盖，不能保存
- **5 个 hook 默认启用**：stop, stop_failure, permission_request, pre_tool_use.askuserquestion, notification.permission_prompt

## 许可证

AGPL-3.0-or-later
