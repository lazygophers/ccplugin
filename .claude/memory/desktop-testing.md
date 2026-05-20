---
name: desktop-testing
description: @desktop 测试体系核心约定 - Vitest 单元 + WDIO E2E (暂移除), 覆盖率/查询/mock 优先级规则
type: project
---

# @desktop 测试约定

## 工具栈

| 层 | 工具 |
|---|---|
| 单元 | Vitest + Testing Library + jsdom + `@testing-library/user-event` |
| E2E (暂移除 2026-04-05, 待 Playwright 替换) | WebdriverIO + `@wdio/tauri-service` + Mocha/Chai |

E2E 移除原因: `@wdio/tauri-service` TS 编译错误。未来用 Playwright 或其他 Tauri 兼容方案。

## 覆盖率目标

- services/lib: 100%
- 组件渲染: 100%
- 用户交互: 核心流程
- 当前状态: 114 单测 / 25 文件 全绿

## 核心约定 (违反 = 不稳测试)

1. **测试隔离**: 每测试独立, `beforeEach` 清 mock
2. **异步**: 用 `findBy*` / `waitFor`, 禁裸 `await delay()`
3. **Mock 管理**: `vi.mocked(invoke).mockReset()` 在 `beforeEach`
4. **查询优先级**: `getByRole > getByText > querySelector` (可访问性优先)

## 命令

```bash
pnpm test:run        # 一次跑
pnpm test:watch      # 监听
pnpm test:coverage   # 覆盖率
```

## E2E 复用 (恢复时)

- 必先 `pnpm tauri build`
- 路径平台分: macOS `./target/release/<app>.app` / Windows `<app>.exe` / Linux `<app>`
- 超时 60s
- 定位走 role+text, 禁脆 selector

## 关联文件

`vitest.config.ts` / `wdio.conf.ts` / `src/test/setup.ts`
