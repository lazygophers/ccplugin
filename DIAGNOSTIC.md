# Semantic MCP 服务器诊断指南

## 问题分析

当运行 `uvx --from git+https://github.com/lazygophers/ccplugin.git@master semantic-mcp --mcp` 时出现错误。

## 诊断步骤

### 1. 查看详细日志

所有错误日志都被记录到：
```bash
~/.lazygophers/ccplugin/error.log
```

查看日志文件了解具体的初始化步骤和失败原因：
```bash
tail -f ~/.lazygophers/ccplugin/error.log
```

### 2. 运行诊断脚本

在项目目录中运行诊断脚本：
```bash
cd /Users/luoxin/persons/lyxamour/ccplugin
python3 test_semantic_init.py
```

这会显示：
- ✓ 模块导入状态
- ✓ 配置加载状态
- ✓ 数据路径设置
- ✓ 索引器初始化步骤和错误信息

## 常见问题

### 问题：fastembed 未安装
```
错误: 未安装 fastembed
安装命令: uv pip install fastembed
```

**解决方案**：
这个依赖已经在 `pyproject.toml` 中列出，当 `uvx` 正确安装所有依赖时应该自动安装。

如果本地测试时出现此错误，可以手动安装：
```bash
uv pip install fastembed
```

### 问题：索引器初始化失败但返回详细错误
查看 `~/.lazygophers/ccplugin/error.log` 文件中的错误堆栈跟踪。

## MCP 服务器启动流程

1. **加载模块** - 导入 CodeIndexer, Config, Utils
2. **检查初始化状态** - 允许未初始化的情况
3. **加载配置** - 使用默认配置或加载已有配置
4. **获取数据路径** - 确定索引数据存储位置
5. **初始化索引器** - 加载存储和嵌入模型
6. **启动 MCP 服务器** - 即使索引器初始化失败也继续启动

## 改进说明

### 最近改进（2026-01-10）

1. **修复 stdio_server 使用** - 正确处理异步流
2. **简化初始化逻辑** - 允许未初始化的情况下运行
3. **增强日志输出** - 详细的初始化步骤跟踪
4. **文件日志处理** - 所有错误记录到 error.log

## 调试建议

1. 首先查看 `error.log` 获得完整的错误堆栈
2. 运行 `test_semantic_init.py` 诊断脚本
3. 检查依赖是否正确安装（特别是 fastembed）
4. 如果问题持续，检查 pyproject.toml 中的依赖版本
