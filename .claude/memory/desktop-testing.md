---
name: desktop-testing-complete
description: Desktop 测试体系完整记录
type: project
---

# Desktop 测试体系完成记录

**日期**: 2026-04-05

## 测试框架选择

### 单元测试：Vitest + Testing Library
- **Vitest**: 快速的单元测试框架，与 Vite 深度集成
- **Testing Library**: React 组件测试最佳实践
- **jsdom**: 浏览器环境模拟
- **@testing-library/user-event**: 真实用户交互模拟

### E2E 测试：WebdriverIO + Tauri Service
- **WebdriverIO**: 标准 Web 自动化测试框架
- **@wdio/tauri-service**: Tauri 应用官方支持
- **Mocha + Chai**: 测试运行器和断言库

## 测试覆盖范围

### 组件测试 (16 个)
- PluginCard: 安装/卸载/更新按钮、scope 显示、loading 状态
- UI 组件: Button, Dialog, Badge
- 布局组件: Layout, TopBar, Sidebar

### 服务测试 (9 个)
- MarketplaceService: 获取插件列表、搜索、分类过滤
- Tauri Commands: 安装/卸载/更新命令，scope 参数传递

### 页面测试 (7 个)
- Marketplaces: 市场列表加载、空状态显示
- Dashboard, Settings, Logs 等其他页面

### E2E 测试（配置完成）
- 插件安装流程：scope 选择、确认安装
- 安装状态显示：用户/项目/local 范围标识
- 市场导航：页面加载、空状态、搜索过滤

## 测试配置文件

### vitest.config.ts
```typescript
- 测试环境: jsdom
- 覆盖率阈值: 100% (services/lib)
- 排除: node_modules, dist, src/test, src/e2e
- 设置文件: src/test/setup.ts
```

### wdio.conf.ts
```typescript
- Runner: local
- Capabilities: Tauri 应用配置
- Framework: Mocha
- Services: @wdio/tauri-service
```

## 运行命令

```bash
# 单元测试
pnpm test:run           # 运行一次
pnpm test:watch         # 监听模式
pnpm test:ui            # UI 界面
pnpm test:coverage      # 覆盖率报告

# E2E 测试（需先构建 Tauri 应用）
pnpm test:e2e           # 运行 E2E 测试
pnpm test:all           # 运行所有测试
```

## 测试数据管理

### Fixtures (src/test/fixtures.ts)
- pluginFixtures: 标准插件数据集
- 包含 installed_scope 字段
- 用于单元测试的 mock 数据

### Mock 设置 (src/test/setup.ts)
- Tauri API mock (@tauri-apps/api/*)
- localStorage mock
- 自动清理 (afterEach)

## 测试覆盖率目标

**当前状态**:
- ✅ 单元测试: 114 个测试全部通过
- ✅ 测试文件: 25 个
- ⏳ E2E 测试: 配置完成，需构建后验证

**覆盖范围**:
- 组件渲染: 100%
- 服务层: 100%
- 用户交互: 核心流程覆盖
- 错误处理: 部分覆盖

## 重要约定

1. **测试隔离**: 每个测试独立运行，beforeEach 清理 mock
2. **异步测试**: 使用 findBy/waitFor 等待异步操作
3. **Mock 管理**: vi.mocked(invoke).mockReset() 在 beforeEach
4. **查询优先级**: getByRole > getByText > querySelector (可访问性优先)

## E2E 测试注意事项

1. **构建依赖**: E2E 测试需要先构建 Tauri 应用 (`pnpm tauri build`)
2. **应用路径**: wdio.conf.ts 需根据平台配置应用路径
   - macOS: `./target/release/ccplugin-desktop.app`
   - Windows: `./target/release/ccplugin-desktop.exe`
   - Linux: `./target/release/ccplugin-desktop`
3. **超时设置**: E2E 测试默认 60s 超时
4. **元素定位**: 优先使用 role 和文本定位，避免脆弱的选择器

## 未来改进方向

1. **增加视觉回归测试**: Percy 或 Chromatic
2. **性能测试**: Lighthouse CI 集成
3. **可访问性测试**: axe-core 集成
4. **API Mock Server**: MSW 用于复杂场景

---

**相关文件**:
- vitest.config.ts - 单元测试配置
- wdio.conf.ts - E2E 测试配置
- src/test/setup.ts - 测试环境设置
- src/e2e/*.spec.ts - E2E 测试用例
