---
id: S2
slug: jwt-utils
deliverable: D1
parent-task: 06-09-oauth-login
status: ready
execution-layer: sub-agent
isolation: task
depends-on: []
blocks: [S1, S3]
estimated-tokens: 30000
---

# S2 · JWT 签发 / 校验 / 刷新工具

> 范例 subtask — 无依赖的前置基础件, 被 S1/S3 共同依赖。展示完整五要素 + dispatch prompt。实际写作删本行。

## 目标

实现 `packages/api/src/auth/jwt.ts` 三个纯函数: `signJWT` 签发含 userId+login 的 JWT, `verifyJWT` 校验并返 claims (失败返 null), `refreshJWT` 用 refresh token 换新 access JWT。

## 产出

- `packages/api/src/auth/jwt.ts` (3 导出函数)
- `packages/api/tests/auth/test_jwt.py` (≥ 3 测试: 主路径 / 过期 / 篡改)

## 验证

```bash
cd packages/api && pnpm test auth/jwt
```

期望: 退出码 0; stdout 含 "3 passed"; 篡改 token 用例验证 verifyJWT 返 null。

## 资源

- 独占文件: `packages/api/src/auth/jwt.ts` `packages/api/tests/auth/test_jwt.py`
- 端口 / 服务: 无
- 环境: 读 `.env` 的 `JWT_SECRET`
- 审批槽位: 否

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| 无 | — | 可立即启动 |

## 执行细节

纯工具函数, 无外部 IO (除读 env)。用 `jsonwebtoken` 库。

### Dispatch Prompt (派 sub-agent)

# 隔离: 共享 task worktree (task.py start 已建, 不传 isolation:worktree)

```
Active task: .trellis/tasks/06-09-oauth-login

## 目标
实现 packages/api/src/auth/jwt.ts 的 signJWT / verifyJWT / refreshJWT 三函数

## 已知
- 上游产出: 无 (本 subtask 是前置基础件)
- 关键约束: JWT_SECRET 从 .env 读, 禁硬编码; access ≤ 1h, refresh ≤ 7d
- 契约 (design.md): signJWT(payload) → string; verifyJWT(token) → claims | null; refreshJWT(rt) → string | null
- 用 jsonwebtoken 库

## 工作目录与范围
- cwd: <worktree abs path>
- 可改文件: packages/api/src/auth/jwt.ts, packages/api/tests/auth/test_jwt.py
- 禁改文件: **/dist/** **/*.generated.** .trellis/**

## 输出格式
- 类型: diff
- 行数上限: 200

## 验收标准
- cd packages/api && pnpm test auth/jwt 退出码 0, stdout 含 "3 passed"
- 测试覆盖: 主路径签发+校验 / 过期 token / 篡改 token (verifyJWT 返 null)

## 失败处理
- 工具瞬时错误 → 重试 1 次
- 业务阻塞 → 输出 `需要: <问题>` 并停
- 资源不可用 → 报 Blocked, 不重试

## Sub-agent 自防护
你已是 trellis-implement, 直接做, 禁再 spawn trellis-implement / trellis-check。
```

## 回滚

- 触发条件: 测试不过 / 契约不符
- 步骤:
  ```bash
  git -C <worktree> checkout packages/api/src/auth/jwt.ts packages/api/tests/auth/test_jwt.py
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| JWT_SECRET 未配 | 签发抛错 | 函数启动校验 env, 缺失明确报错 |

## 历史

- 2026-06-09: created
