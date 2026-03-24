import net from "node:net";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const port = Number(process.env.CCPLUGIN_DESKTOP_DEV_PORT ?? "1420");

function canConnect(host) {
  return new Promise((resolve) => {
    const socket = net.connect({ host, port });
    const done = (ok) => {
      socket.removeAllListeners();
      socket.destroy();
      resolve(ok);
    };
    socket.once("connect", () => done(true));
    socket.once("error", () => done(false));
    socket.setTimeout(300, () => done(false));
  });
}

async function main() {
  const inUse = (await canConnect("127.0.0.1")) || (await canConnect("::1"));
  if (!inUse) return;

  let details = "";
  try {
    const { stdout } = await execFileAsync("lsof", [
      "-nP",
      `-iTCP:${port}`,
      "-sTCP:LISTEN",
    ]);
    details = stdout.trim();
  } catch {
  }

  console.error(`\n[ccplugin-desktop] 端口 ${port} 已被占用，无法启动 dev server。`);
  if (details) {
    console.error("\n当前占用进程（lsof）：\n" + details);
  }

  console.error(`\n建议：`);
  console.error(`- macOS/Linux：先执行 \`lsof -nP -iTCP:${port} -sTCP:LISTEN\` 查看 PID，然后 \`kill <PID>\``);
  console.error(`- Windows：执行 \`netstat -ano | findstr :${port}\` 查看 PID，然后在任务管理器结束进程`);
  console.error(`\n常见原因：上一次 \`tauri dev\` / \`npm run dev\` 未退出。\n`);

  process.exit(1);
}

await main();
