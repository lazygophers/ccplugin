---
description: 通用项目探索规范 - 快速理解项目全貌、识别技术栈、目录结构和核心模块的执行规范
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (3000+ tokens) -->

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

## 工具

读取：`Read`(README.md→CLAUDE.md→配置文件)。目录：`serena:list_dir`(depth≤2)。搜索：`serena:find_file/search_for_pattern`。沟通：`SendMessage(@main)`。

## 规范

**必须**：先读文档再扫目录、技术栈基于配置确认、JSON标准格式、5分钟内完成。
**禁止**：跳过文档阅读、深入每个文件、猜测技术栈、输出非结构化文本。
不确定时在uncertainty字段标注。Monorepo优先整体结构不深入子项目。

<!-- /STATIC_CONTENT -->
