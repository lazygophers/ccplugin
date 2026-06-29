# Implement — 为 API 加 OAuth2 登录

> 范例 implement — 展示前置检查 + 有序 checklist (五要素 + 执行层 + 回滚) + 验证汇总 + review gate + rollback。实际写作删本行。

## 前置检查

- [ ] design.md 已审, 无开放 TODO
- [ ] task.py start 后已创 worktree (整 task 改动隔离)
- [ ] `.env` 含 `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` / `JWT_SECRET`
- [ ] `cd packages/api && pnpm install` 通过

## 执行清单 (按依赖排序)

### S1: JWT 签发 + 校验工具 (对应 subtask S2-jwt-utils.md)

- 目标: 实现 `signJWT` / `verifyJWT` / `refreshJWT`, payload 含 userId + login
- 产出: `packages/api/src/auth/jwt.ts` + `tests/auth/test_jwt.py`
- 验证: `cd packages/api && pnpm test auth/jwt` 退出码 0, stdout 含 "3 passed"
- 资源: `packages/api/src/auth/jwt.ts`
- 依赖: 无
- 执行层: sub-agent (trellis-implement, 共享 task worktree)
- 回滚点: `git -C <worktree> checkout packages/api/src/auth/jwt.ts`

### S2: OAuth2 授权码端点 (对应 S1-oauth-endpoint.md)

- 目标: `POST /auth/github/callback` 收 code → 换 token → 签 JWT 返回
- 产出: `packages/api/src/auth/oauth.ts` + `routes.ts` + `tests/auth/test_oauth.py`
- 验证: `pnpm test auth/oauth` 退出码 0; 真实 code 联调返合法 JWT
- 资源: `packages/api/src/auth/oauth.ts` `packages/api/src/auth/routes.ts`
- 依赖: S1 (用 signJWT)
- 执行层: sub-agent (trellis-implement, 共享 task worktree)
- 回滚点: `git -C <worktree> checkout packages/api/src/auth/`

### S3: JWT 中间件挂载 (对应 S3-jwt-middleware.md)

- 目标: 受保护路由前置 JWT 校验, 无/非法 JWT 返 401
- 产出: `packages/api/src/middleware/auth.ts` + 路由挂载 diff + `tests/auth/test_middleware.py`
- 验证: `pnpm test auth/middleware` 退出码 0; `curl -i /api/orders` 无 JWT 返 401
- 资源: `packages/api/src/middleware/auth.ts` `packages/api/src/routes/*.ts`
- 依赖: S1 (用 verifyJWT)
- 执行层: sub-agent (trellis-implement, 共享 task worktree)
- 回滚点: `git -C <worktree> checkout packages/api/src/middleware/ packages/api/src/routes/`

## 验证命令汇总

```bash
cd packages/api
pnpm test auth          # 全 auth 测试
pnpm lint               # 退出码 0
pnpm type-check         # 退出码 0
# 端到端
curl -i http://localhost:3000/api/orders                          # 期望 401
curl -i -H "Authorization: Bearer $VALID_JWT" .../api/orders       # 期望 200
```

## Review Gates

- G1 (S1 完成后): 人工审 JWT 契约 (密钥来源 .env / 有效期 / claims 字段)
- G2 (S1+S2+S3 完成后): 端到端登录链路联调 + grep 全受保护路由确认中间件挂载

## Rollback 计划

- 若 S<X> 失败: 见各 subtask 回滚点, 在 worktree 内 checkout 对应文件
- 若整体失败: 丢弃整个 task worktree (`git worktree remove --force <path>`), 主分支零污染
- 若已合并后发现问题: `AUTH_MODE=static` feature flag 切回静态 token
