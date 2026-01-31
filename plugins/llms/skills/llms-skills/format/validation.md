# llms.txt 验证

## 验证清单

### 基本结构

- [ ] **H1 标题存在**
    - 文件开头必须是 `# 项目名称`
    - 标题不能为空

- [ ] **引用块格式正确**
    - 使用 `>` 开头
    - 位于 H1 标题之后
    - 包含关键信息

- [ ] **详细内容不包含标题**
    - 详细内容部分不能有 H2-H6 标题
    - 可以使用段落、列表等格式

- [ ] **H2 部分格式正确**
    - 使用 `## 部分名称` 格式
    - 每个部分包含文件列表
    - 文件列表使用 markdown 列表格式

### 链接格式

- [ ] **链接格式正确**
    - 格式：`[name](url): description`
    - name 不为空
    - url 有效（本地文件存在或远程 URL 可访问）

- [ ] **本地文件路径正确**
    - 使用相对于项目根目录的路径
    - 文件实际存在
    - 路径使用正斜杠 `/`

- [ ] **远程 URL 有效**
    - 包含协议（http:// 或 https://）
    - URL 格式正确
    - 可访问（推荐检查）

### 内容质量

- [ ] **语言简洁清晰**
    - 避免冗长的描述
    - 使用简洁的语言
    - 避免使用未解释的术语

- [ ] **描述有意义**
    - 每个链接都有描述（推荐）
    - 描述说明文件用途
    - 描述不超过一句话

- [ ] **分组合理**
    - Docs、Examples、Optional 分组清晰
    - 重要文档在前
    - Optional 仅包含次要信息

## 常见错误

### 格式错误

```markdown
# 错误示例 1：缺少 H1 标题

> 项目描述

## Docs

- [文档](docs.md)
```

**修复**：添加 H1 标题

```markdown
# 项目名称

> 项目描述
```

---

```markdown
# 错误示例 2：详细内容包含标题

# MyProject

> 描述

## 这不是详细内容

这是详细内容。
```

**修复**：移除详细内容中的标题

```markdown
# MyProject

> 描述

这是详细内容。
```

---

```markdown
# 错误示例 3：链接格式错误

## Docs

- [文档](docs.md) 缺少冒号和描述
```

**修复**：使用正确的链接格式

```markdown
## Docs

- [文档](docs.md): 文档描述
```

### 内容错误

```markdown
# 错误示例 4：描述过长

## Docs

- [API 文档](docs/api.md): 这是一个非常详细的 API 文档，包含了所有的 API 端点、参数说明、返回值格式、错误码说明等等各种详细内容...
```

**修复**：简化描述

```markdown
## Docs

- [API 文档](docs/api.md): 完整的 API 参考
```

---

```markdown
# 错误示例 5：Optional 包含重要信息

## Optional

- [快速开始](docs/quickstart.md): 入门指南
- [API 文档](docs/api.md): API 参考
```

**修复**：将重要信息移到其他部分

```markdown
## Docs

- [快速开始](docs/quickstart.md): 入门指南
- [API 文档](docs/api.md): API 参考

## Optional

- [贡献指南](CONTRIBUTING.md): 如何贡献
```

## 自动化验证

可以使用以下方法自动验证：

### 1. 使用 Python 脚本

```python
import re
from pathlib import Path

def validate_llms_txt(file_path: Path) -> list[str]:
    """验证 llms.txt 文件"""
    errors = []
    content = file_path.read_text()
    lines = content.split('\n')

    # 检查 H1 标题
    if not re.match(r'^#\s+\S+', content):
        errors.append("缺少 H1 标题")

    # 检查链接格式
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)(?::\s*(.+))?'
    for line in lines:
        if line.strip().startswith('- '):
            if not re.match(link_pattern, line):
                errors.append(f"链接格式错误: {line}")

    return errors
```

### 2. 使用 llms-plugin

安装插件后，通过 Agent 验证：

```
请验证当前项目的 llms.txt 文件
```

## 最佳实践

1. **保持简洁**
    - 只包含关键信息
    - 避免冗余描述
    - 使用简洁的语言

2. **结构清晰**
    - 使用标准的 H1/H2 格式
    - 合理分组文档
    - 保持一致的排序

3. **链接有效**
    - 定期检查链接有效性
    - 使用相对路径（本地文件）
    - 使用 HTTPS（远程 URL）

4. **描述准确**
    - 每个链接都有描述
    - 描述简明扼要
    - 避免使用未解释的术语

5. **定期更新**
    - 添加新文档时更新
    - 删除过时链接
    - 保持内容最新
