---
description: "快速探索项目全貌：识别技术栈、映射目录结构、定位核心模块。当首次接触项目或需要建立整体认知时优先触发。宏观优先，5分钟内完成项目概览。深入分析请用其他explorer。"
model: sonnet
user-invocable: false
agent: task:explorer-general
hooks:
  SessionStop:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
  SubagentStart:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
---


# Skills(task:explorer-general) - 通用项目探索规范

## 范围

快速理解项目全貌：技术栈识别、目录结构映射、核心模块定位。不适用于深入代码分析(用explorer-code)、性能优化或安全审计。

## 核心原则

- **宏观优先**：先整体定位再深入，通过文档和配置建立全局视角
- **文档驱动**：优先README.md/CLAUDE.md/配置文件，文档不足时才通过代码推断
- **快速定位**：80/20原则，5分钟内完成项目全貌
- **标准输出**：统一JSON格式，便于后续处理

## 技术栈检测

| 语言 | 配置文件 | 框架识别(依赖) | 包管理器(lock文件) |
|------|---------|---------------|-------------------|
| JS/TS | package.json + tsconfig.json | react/vue/@angular/core/express/next/nuxt | npm(package-lock)/yarn(yarn.lock)/pnpm(pnpm-lock) |
| Go | go.mod | gin/echo/fiber/chi/grpc | go modules |
| Python | pyproject.toml/requirements.txt | django/flask/fastapi/tornado | poetry(poetry.lock)/pip/pipenv(Pipfile) |
| Rust | Cargo.toml | actix-web/rocket/axum/tokio | cargo |

构建工具：vite/webpack/rollup/parcel(devDependencies)。测试：jest/vitest/mocha/cypress(devDependencies)/pytest/内置。

## 目录结构模式

| 类型 | 特征目录 | 判断依据 |
|------|---------|---------|
| Frontend | src/public/components/pages/assets/styles | 有public+components，含前端框架依赖 |
| Backend | cmd/internal/pkg/routes/controllers/models/services | 无public/pages，有controllers/routes |
| Fullstack | frontend+backend 或 client+server | 同时存在前后端特征 |
| Library | src(lib)/tests/docs/examples | main/exports字段，有examples，无应用层目录 |
| CLI | cmd/bin/internal | package.json有bin字段 |
| Monorepo | packages/apps/libs | workspaces字段/pnpm-workspace/lerna/nx |

## 输出格式

JSON，必含：`project_name`/`description`/`tech_stack`(language/framework/build_tool/test_framework/package_manager)/`directory_structure[]`(path/purpose)/`core_modules[]`(name/path/purpose)/`dependencies`(production/development/key_deps[])/`project_type`/`uncertainty`(notes)

## Memory 集成

**探索前**：
1. `list_memories(topic_filter="explorer/general")` 列出已有 memory
2. 若存在匹配项目的 memory（subtopic=项目名），read_memory 加载
3. 验证 memory 中的文件路径（serena:find_file 检查 README/配置文件等）
4. 删除过时文件路径，将有效信息作为探索起点

**探索后**：
1. 对比探索前后信息差异
2. `write_memory("explorer/general", "{project_name}", content)` 创建新 memory 或 `edit_memory` 更新已有 memory
3. 添加时间戳：`last_updated: YYYY-MM-DD`
4. 确保内容不超过 10KB

详细规范参见 Skills(task:explorer-memory-integration)。

## 工具

Memory：`serena:list_memories`/`read_memory`/`write_memory`/`edit_memory`。
验证：`serena:find_file`(检查文件存在性)。
读取：`Read`(README.md→CLAUDE.md→配置文件)。目录：`serena:list_dir`(depth≤2)。搜索：`serena:search_for_pattern`。沟通：`SendMessage(@main)`。

## 规范

**必须**：探索前加载并验证 memory、先读文档再扫目录、技术栈基于配置确认、JSON标准格式、5分钟内完成、探索后更新 memory。
**禁止**：跳过 memory 验证、跳过文档阅读、深入每个文件、猜测技术栈、输出非结构化文本、创建超过 10KB 的 memory。
不确定时在uncertainty字段标注。Monorepo优先整体结构不深入子项目。

