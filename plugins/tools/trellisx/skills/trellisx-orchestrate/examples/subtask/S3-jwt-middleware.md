---
id: S3
slug: jwt-middleware
deliverable: D2
parent-task: 06-09-oauth-login
status: blocked
execution-layer: sub-agent
isolation: task
depends-on: [S2]
blocks: []
write-files: ["packages/api/src/auth/middleware.ts", "packages/api/tests/auth/test_middleware.py"]
exec-scope: package:api
estimated-tokens: 25000
---

# S3 · JWT 中间件挂载受保护路由

> 范例 subtask — 依赖 S2、与 S1 并行 (改不同文件)。展示依赖等待 + 并行资源不交。实际写作删本行。

## 目标

实现 `packages/api/src/middleware/auth.ts` JWT 校验中间件, 挂载到全部受保护路由 (`routes/orders.ts` 等), 无/非法 JWT 返 401, 合法放行。

## 产出

- `packages/api/src/middleware/auth.ts`
- 受保护路由挂载 diff (`packages/api/src/routes/*.ts`)
- `packages/api/tests/auth/test_middleware.py`

## 验证

```bash
cd packages/api && pnpm test auth/middleware
curl -i http://localhost:3000/api/orders                       # 期望 401
curl -i -H "Authorization: Bearer $VALID_JWT" .../api/orders    # 期望 200
```

期望: 测试退出码 0; 无 JWT 401; 合法 JWT 200。

## 资源 (冲突判定输入, 见 scheduling.md)

- **write-files** (frontmatter): `packages/api/src/auth/middleware.ts` `packages/api/tests/auth/test_middleware.py` (示例简写, 实际含 `src/middleware/*` + `src/routes/*` 改动)
- **exec-scope** (frontmatter): `package:api`
- 与 S1 关系: S1 改 `src/auth/*`, S3 改 `src/middleware/*` + `src/routes/*`, write-files 不交 → 无依赖边 → 可并行

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S2 | `auth/jwt.ts` 的 `verifyJWT` 导出 | 文件存在 + 函数可 import |

## 执行细节

中间件读 `Authorization: Bearer <token>` → `verifyJWT(token)` → null 则 401, 否则挂 `req.user` 后 next()。grep 全受保护路由确认无遗漏挂载。

### Dispatch Prompt (派 sub-agent)

# 隔离: 共享 task worktree (task.py start 已建, 不传 isolation:worktree)

```
Active task: .trellis/tasks/06-09-oauth-login

## 目标
实现 JWT 校验中间件并挂载全部受保护路由

## 已知
- 上游产出: packages/api/src/auth/jwt.ts 的 verifyJWT (S2 已完成)
- 关键约束: 无 JWT / 非法 JWT 返 401; 合法挂 req.user 后 next()
- 受保护路由清单: grep "router\\." packages/api/src/routes/ 确认全覆盖

## 工作目录与范围
- cwd: <worktree abs path>
- 可改文件: packages/api/src/middleware/auth.ts, packages/api/src/routes/*.ts, packages/api/tests/auth/test_middleware.py
- 禁改文件: **/dist/** **/*.generated.** .trellis/** packages/api/src/auth/**

## 输出格式
- 类型: diff
- 行数上限: 250

## 验收标准
- pnpm test auth/middleware 退出码 0
- curl 无 JWT → 401, 合法 JWT → 200
- grep 确认全受保护路由已挂中间件 (无裸奔接口)

## 失败处理
- 工具瞬时错误 → 重试 1 次
- 业务阻塞 → 输出 `需要: <问题>` 并停
- 资源不可用 → 报 Blocked, 不重试

## Sub-agent 自防护
你已是 trellis-implement, 直接做本 subtask。**禁调度、禁递归、禁并行派其他 subtask** (工具集无 Agent/Task, Recursion Guard); 调度归 main (见 scheduling.md), 你只执行这 1 个 subtask。
```

## 回滚

- 触发条件: 测试不过 / 有路由漏挂
- 步骤:
  ```bash
  git -C <worktree> checkout packages/api/src/middleware/ packages/api/src/routes/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 新增路由忘挂中间件 | 接口裸奔 | 验收 grep 全路由强制确认; G2 gate 复查 |

## 历史

- 2026-06-09: created
