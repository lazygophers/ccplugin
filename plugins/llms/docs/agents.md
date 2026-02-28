# 代理系统

llms.txt 插件提供的代理。

## llms-generator 代理

### 职责

- 扫描项目文件
- 提取项目信息
- 生成 llms.txt 文件
- 创建配置文件

### 工作流程

1. **扫描项目**
   - README.md / pyproject.toml / package.json
   - docs/ 目录
   - examples/ 目录

2. **提取信息**
   - 项目名称、描述
   - 文档文件列表
   - 示例文件列表

3. **生成文件**
   - 按照 llms.txt 标准格式
   - 创建 .llms.json 配置

4. **验证格式**
   - 检查是否符合标准
   - 验证链接有效性

### 使用方式

```
请为当前项目生成 llms.txt 文件
```

### 输出示例

```markdown
# My Project

> A brief description of the project

Detailed information about the project.

## Docs

- [README](README.md): Project documentation
- [API](docs/api.md): API reference

## Examples

- [Basic](examples/basic.py): Basic usage example

## Optional

- [External](https://example.com/docs): External documentation
```
