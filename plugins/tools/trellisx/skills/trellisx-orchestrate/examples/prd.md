# 为 API 加 OAuth2 登录

> 范例 PRD — trellis 原生骨架 (Goal / What I already know / Assumptions / Open Questions / Requirements / Acceptance Criteria / Definition of Done / Out of Scope / Technical Notes) + trellisx 编排增强 (Deliverable 矩阵 / Subtask 拆分 / mermaid 调度图)。实际写作时删除本行引言。

## Goal

为 `packages/api` 加 GitHub OAuth2 授权码登录, 用户登录后签发 JWT, 受保护接口校验 JWT 通过率 100%, 替换现有写死在 .env 的静态 token。

## What I already know

### 现状

- 现有 API 仅支持静态 token (`.env` 的 `STATIC_TOKEN`), 无法多用户
- 路由在 `packages/api/src/routes/`, 中间件在 `packages/api/src/middleware/`
- 已有 `jsonwebtoken` 依赖 (package.json)

### 调研结论

- OAuth provider 选型见 `research/oauth2-provider-comparison.md` — 选 GitHub (团队已有组织账号)
- JWT 无状态优于 server session (水平扩展, 见 design.md 取舍)

## Assumptions (temporary)

- GitHub OAuth App 已注册, `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` 可配进 .env
- 现有受保护路由全部在 `routes/` 下, 无散落他处
- 前端能配合改造登录跳转 (本 task 不含前端)

## Open Questions

- refresh token 是否需持久化以支持主动失效? (暂定不持久化, 靠短有效期, 后续按需加)

## Deliverable 矩阵 (trellisx 编排)

| ID | 交付物 | 类型 | 独立验收 | 优先级 |
| --- | --- | --- | --- | --- |
| D1 | OAuth2 授权码流程 + JWT 签发 | diff | `POST /auth/github/callback` 返回合法 JWT, `tests/auth/test_oauth.py` 全绿 | P0 |
| D2 | JWT 中间件保护现有接口 | diff | 无 JWT 访问 `GET /api/orders` 返 401, 带合法 JWT 返 200 | P0 |

## Requirements

1. **OAuth2 授权码流程** (D1):
   - `POST /auth/github/callback` 收 `code` → 换 GitHub access_token + 用户 login
   - 签发含 `userId` + `login` 的 JWT 返前端
2. **JWT 工具** (D1):
   - `signJWT` / `verifyJWT` / `refreshJWT`, 密钥从 `.env` 的 `JWT_SECRET` 读
   - access ≤ 1h, refresh ≤ 7d
3. **JWT 中间件** (D2):
   - 受保护路由前置校验, 无/非法 JWT 返 401, 合法挂 `req.user` 后放行
   - 全部受保护路由必须挂载, 无遗漏

## Subtask 拆分 (trellisx 编排)

每个 subtask 有独立文件 `.trellis/tasks/<task>/subtask/<id>-<slug>.md`。本节仅概览。

| ID | Subtask | 所属 Deliverable | 边界 (改动 / 读取范围) | 简要说明 | 详情文件 |
| --- | --- | --- | --- | --- | --- |
| S1 | JWT 签发 + 校验工具 | D1 | `packages/api/src/auth/jwt.ts` | 签发 / 校验 / 刷新 JWT | `subtask/S2-jwt-utils.md` |
| S2 | OAuth2 授权码端点 | D1 | `packages/api/src/auth/oauth.ts` `routes.ts` | GitHub 回调换 token 签 JWT | `subtask/S1-oauth-endpoint.md` |
| S3 | JWT 中间件挂载 | D2 | `packages/api/src/middleware/auth.ts` `routes/*.ts` | 受保护路由前置校验 | `subtask/S3-jwt-middleware.md` |

### Subtask 调度图

```mermaid
flowchart LR
    S1[S1 · JWT 工具] --> S2[S2 · OAuth2 端点]
    S1 --> S3[S3 · JWT 中间件]
    S2 --> G1{{G1 · D1 验收}}
    S3 --> G2{{G2 · D2 验收}}
    classDef serial fill:#fff3e0,stroke:#e65100;
    classDef parallel fill:#e0f7fa,stroke:#006064;
    class S1 serial
    class S2,S3 parallel
```

- S1 (JWT 工具) 是 S2 / S3 共同前置, 必须先完成
- S2 / S3 依赖 S1 后可并行 (改不同文件, 资源不交)
- G1 / G2 为 deliverable 验收门

## Acceptance Criteria

- [ ] D1 + D2 全部 P0 deliverable 独立验收通过
- [ ] `cd packages/api && pnpm test auth` 退出码 0
- [ ] 端到端: GitHub 登录 → 拿 JWT → 访问受保护接口 200, 无 JWT 401
- [ ] `pnpm lint && pnpm type-check` 退出码 0
- [ ] `grep -rn "STATIC_TOKEN" packages/api/src/` 仅剩灰度兼容层 (无新增引用)

## Definition of Done

- 全部 Requirements 实现 + Acceptance Criteria 勾选
- 全部变更自动暂存 (CLAUDE.md §1)
- task worktree 已合并到当前分支 + `git worktree remove` 清理
- bump `.version` (用户可见的登录方式变更)

## Out of Scope

- 其他 OAuth provider (Google / 微信)
- 用户资料管理 / 权限分级 (RBAC)
- 前端登录页改造 (另起 task)
- refresh token 持久化主动失效 (见 Open Questions)

## Technical Notes

### 文件位置

- JWT 工具: `packages/api/src/auth/jwt.ts`
- OAuth 流程: `packages/api/src/auth/oauth.ts` + `routes.ts`
- 中间件: `packages/api/src/middleware/auth.ts`
- 测试: `packages/api/tests/auth/`

### 灰度 / 回滚

- feature flag `AUTH_MODE=static|oauth`, 默认 static; 出问题改回 static
- 详细回滚见 `design.md` 回滚节 + 各 subtask 回滚点

### 验证命令

```bash
cd packages/api && pnpm test auth
curl -i http://localhost:3000/api/orders                          # 期望 401
curl -i -H "Authorization: Bearer $VALID_JWT" .../api/orders       # 期望 200
```
