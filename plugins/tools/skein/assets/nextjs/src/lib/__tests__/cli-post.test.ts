// CLI 端点失败传播测试。
// 守的是「点确认没反应」那个 bug: 后端 CLI 非零退出时 HTTP 仍是 200 (body.ok=false),
// api 若原样 resolve, 调用方就会当成成功弹「已确认规划」, 而 task 状态压根没动。
//
// 运行 (从 nextjs 项目根目录):
//   npx tsc src/lib/__tests__/cli-post.test.ts --outDir /tmp/cliout \
//     --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/cliout/__tests__/cli-post.test.js
import { api, ApiError } from "../api";

function assert(cond: boolean, msg: string) {
  if (!cond) { console.error("FAIL: " + msg); process.exit(1); }
}

type FetchStub = (input: unknown, init?: unknown) => Promise<Response>;

function stubFetch(body: Record<string, unknown>): { calls: string[] } {
  const calls: string[] = [];
  const stub: FetchStub = async (input) => {
    calls.push(String(input));
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      headers: { get: () => "application/json" },
      json: async () => body,
      text: async () => JSON.stringify(body),
    } as unknown as Response;
  };
  (globalThis as unknown as { fetch: FetchStub }).fetch = stub;
  return { calls };
}

async function main() {
  // 1) CLI 失败 (ok=false) → 必须抛, 且带上 stderr 原文供 UI 展示
  {
    const { calls } = stubFetch({ ok: false, exit: 1, stdout: "", stderr: "t1 planning 未就绪 (2 项待补)\n" });
    let err: unknown = null;
    try { await api.confirm("t1"); } catch (e) { err = e; }
    assert(err instanceof ApiError, "ok=false 必须抛 ApiError, 不能当成功返回");
    assert((err as ApiError).message === "t1 planning 未就绪 (2 项待补)", "报错文案必须是 CLI 的 stderr 原文");
    assert(calls.length === 1 && calls[0].includes("/__skein__/task/confirm"), "应真的打了一次 task/confirm 请求");
  }

  // 2) stderr 为空时不能抛出空串, 要回落到可读的 exit code 文案
  {
    stubFetch({ ok: false, exit: 2, stdout: "  ", stderr: "  " });
    let msg = "";
    try { await api.del("t1"); } catch (e) { msg = (e as ApiError).message; }
    assert(msg.includes("exit 2"), "无 stderr 时应回落到 exit code 文案, 实得: " + JSON.stringify(msg));
  }

  // 3) CLI 成功 → 原样返回, 不误伤正常路径
  {
    stubFetch({ ok: true, exit: 0, stdout: "done", stderr: "" });
    const r = await api.confirm("t1");
    assert(r.ok === true && r.stdout === "done", "ok=true 应原样返回 body");
  }

  // 4) finish 端点走同一条通道, 同样不许静默成功
  {
    stubFetch({ ok: false, id: "t1", exit: 1, stdout: "", stderr: "worktree 有未提交改动" });
    let msg = "";
    try { await api.finish("t1"); } catch (e) { msg = (e as ApiError).message; }
    assert(msg === "worktree 有未提交改动", "finish 也必须抛出 CLI 报错");
  }

  console.log("PASS cli-post.test.ts");
}

main();
