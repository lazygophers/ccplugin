# CC Plugin Marketplace

Claude Code 插件市场 - 提供记忆、上下文、任务和知识库管理的独立插件集合。

## 概述

本仓库是一个插件市场，包含多个独立的 Claude Code 插件。每个插件都可以**独立安装和使用**，用户可以根据需求选择安装部分或全部插件。

## 可用插件

### 🧠 Memory Plugin - 记忆管理插件

基于知识图谱的记忆存储和检索系统。

**功能**：
- 长期记忆存储
- 标签化检索
- 元数据关联
- 知识图谱关系

**安装**: [plugins/memory/](plugins/memory/)

---

### 📝 Context Plugin - 上下文管理插件

会话上下文的持久化和恢复系统。

**功能**：
- 会话上下文保存
- 多角色上下文追踪
- 历史上下文检索
- 跨会话工作流

**安装**: [plugins/context/](plugins/context/)

---

### ✅ Task Plugin - 任务管理插件

开发任务的创建和管理系统。

**功能**：
- 结构化任务创建
- 优先级和状态管理
- 标签过滤
- 任务依赖关系

**安装**: [plugins/task/](plugins/task/)

---

### 📚 Knowledge Plugin - 知识库管理插件

基于向量数据库的知识管理系统。

**功能**：
- 向量数据库存储
- 语义搜索
- 多源知识整合
- 知识图谱关联

**安装**: [plugins/knowledge/](plugins/knowledge/)

---

## 快速开始

### 前置要求

- Claude Code >= 1.0.0
- Python >= 3.10
- uv (推荐) 或 pip

### 安装插件

#### 方法 1：安装单个插件

```bash
# 进入插件目录
cd plugins/memory

# 使用 uv 安装
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -e ".[dev]"
```

#### 方法 2：安装所有插件

```bash
# 克隆市场仓库
git clone https://github.com/lazygophers/ccplugin
cd ccplugin

# 安装所有插件
./install-all.sh  # 或查看各插件的 README.md
```

### 配置 Claude Code

在 Claude Code 配置中添加所需插件：

```json
{
  "plugins": [
    {
      "path": "/path/to/ccplugin/plugins/memory"
    },
    {
      "path": "/path/to/ccplugin/plugins/context"
    }
  ]
}
```

## 项目结构

```
ccplugin/                        # 插件市场根目录
├── marketplace.json             # 市场元数据
├── README.md                    # 本文件
├── plugins/                     # 插件目录
│   ├── memory/                  # 记忆管理插件
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── src/memory/
│   │   │   ├── server.py        # MCP Server
│   │   │   └── ...
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── context/                 # 上下文管理插件
│   │   ├── .claude-plugin/
│   │   ├── src/context/
│   │   ├── tests/
│   │   └── README.md
│   ├── task/                    # 任务管理插件
│   │   ├── .claude-plugin/
│   │   ├── src/task/
│   │   ├── tests/
│   │   └── README.md
│   └── knowledge/               # 知识库管理插件
│       ├── .claude-plugin/
│       ├── src/knowledge/
│       ├── tests/
│       └── README.md
└── docs/                        # 市场文档
    ├── 插件能力说明.md
    ├── 快速开始.md
    └── ...
```

## 插件独立性

每个插件都是**完全独立**的：

- ✅ 独立的 MCP Server
- ✅ 独立的依赖管理 (pyproject.toml)
- ✅ 独立的配置文件 (.claude-plugin/plugin.json)
- ✅ 独立的测试套件
- ✅ 可单独安装和卸载

## 技术栈

**共同依赖**：
- MCP SDK >= 1.1.0
- Pydantic >= 2.0
- Python >= 3.10

**插件特定依赖**：
- Memory: NetworkX (知识图谱)
- Context: SQLAlchemy (会话存储)
- Task: SQLAlchemy (任务数据库)
- Knowledge: ChromaDB (向量数据库)

## 开发

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/lazygophers/ccplugin
cd ccplugin

# 进入特定插件进行开发
cd plugins/memory
uv pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
ruff check src/ --fix

# 类型检查
mypy src/
```

### 添加新插件

1. 在 `plugins/` 下创建新目录
2. 参考现有插件结构创建文件
3. 在 `marketplace.json` 中注册插件
4. 添加插件文档

## 路线图

**v0.1.0** (当前)
- [x] 插件市场基础架构
- [x] 4 个插件的接口实现
- [x] 完整的测试覆盖

**v0.2.0** (计划)
- [ ] Memory Plugin 完整实现
  - [ ] NetworkX 知识图谱
  - [ ] 关系推理
  - [ ] 记忆合并

**v0.3.0** (计划)
- [ ] Context Plugin 完整实现
  - [ ] SQLAlchemy 会话存储
  - [ ] 上下文压缩
  - [ ] 智能摘要

**v0.4.0** (计划)
- [ ] Task Plugin 完整实现
  - [ ] 任务依赖管理
  - [ ] 状态流转
  - [ ] 优先级调度

**v0.5.0** (计划)
- [ ] Knowledge Plugin 完整实现
  - [ ] ChromaDB 向量检索
  - [ ] 多模态支持
  - [ ] 知识图谱整合

## 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 上创建 issue。

## 作者

luoxin

---

**注意**: 每个插件都有独立的文档和使用说明，请查看各插件目录下的 README.md 文件。
