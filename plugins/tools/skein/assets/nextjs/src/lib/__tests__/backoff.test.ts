// 重连退避 (backoffDelayMs) 纯函数测试 — 只断言数学性质, 不硬编码具体数值 (调参一次就红):
//   1) 上界随 attempt 单调不减, 并收敛到上限 5min 后触顶不再增长
//   2) attempt=0 时上界 <= 2000ms
//   3) 同一 attempt 下多次取值不全等, 且全部落在 [0, 上界] 内 —— 注入自己的随机源, 不 mock 全局 Math.random
//   4) 重置 (attempt=0) 回到最短间隔
//
// 运行 (从 nextjs 项目根目录):
//   npx tsc src/lib/__tests__/backoff.test.ts --outDir /tmp/bfout \
//     --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/bfout/backoff.test.js

import { backoffDelayMs } from "../live";

let pass = 0, fail = 0;
function assert(cond: boolean, msg: string) {
  if (cond) { pass++; return; }
  fail++;
  console.error(`FAIL: ${msg}`);
}

const CAP_MS = 5 * 60 * 1000;

// 固定随机源取上界 (random() 恒返回 1 → 结果即为 upper 本身)
function upperOf(attempt: number): number {
  return backoffDelayMs(attempt, () => 1);
}

// ── 断言 1: 上界随 attempt 单调不减, 且收敛到上限后不再增长 ──
{
  let prevUpper = upperOf(0);
  let cappedAt = -1;
  for (let attempt = 1; attempt <= 20; attempt++) {
    const upper = upperOf(attempt);
    assert(upper >= prevUpper, `attempt=${attempt} 上界 ${upper} 应 >= attempt=${attempt - 1} 上界 ${prevUpper}`);
    if (cappedAt === -1 && upper === CAP_MS) cappedAt = attempt;
    prevUpper = upper;
  }
  assert(cappedAt !== -1, "多次 attempt 增长后上界应触顶到上限");
  assert(upperOf(20) === CAP_MS, "触顶后继续增长 attempt 上界不应再变化 (钉死在上限)");
}

// ── 断言 2: attempt=0 时上界 <= 2000ms ──
{
  const upper = upperOf(0);
  assert(upper <= 2000, `attempt=0 上界 ${upper} 应 <= 2000ms`);
}

// ── 断言 3: 同一 attempt 下多次取值不全等, 且全部落在 [0, 上界] 内 (注入随机源) ──
{
  const attempt = 3;
  const upper = upperOf(attempt);
  let sequenceIndex = 0;
  const fakeRandoms = [0, 0.25, 0.5, 0.75, 0.999999];
  const nextFakeRandom = () => fakeRandoms[sequenceIndex++ % fakeRandoms.length];
  const values = Array.from({ length: fakeRandoms.length }, () => backoffDelayMs(attempt, nextFakeRandom));
  const unique = new Set(values);
  assert(unique.size > 1, `同一 attempt 下多次取值不应全等, 实际: ${values.join(", ")}`);
  for (const v of values) {
    assert(v >= 0 && v <= upper, `抖动值 ${v} 应落在 [0, ${upper}] 内`);
  }
}

// ── 断言 4: 重置 (attempt=0) 回到最短间隔 —— 触顶后重置的上界应等于初始上界 ──
{
  const initialUpper = upperOf(0);
  const cappedUpper = upperOf(15);
  assert(cappedUpper > initialUpper, "触顶后的上界应远大于初始上界, 前置条件不成立测试无意义");
  const resetUpper = upperOf(0);
  assert(resetUpper === initialUpper, `重置 (attempt=0) 上界 ${resetUpper} 应等于初始上界 ${initialUpper}`);
}

console.log(`${pass} passed, ${fail} failed`);
if (fail > 0) process.exit(1);
