"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { startLive, subscribe } from "@/lib/live";
import { api } from "@/lib/api";
import { AlertTriangle } from "lucide-react";

// 项目名跨导航缓存 —— 每次路由切换都要重设标题, 但项目名一个会话内不变, 只请求一次。
let cachedProj: string | null = null;

// Boots WS live-updates on client side; subscribes globally to trigger page reloads on "data" messages.
// 断线时渲染顶部横幅提示 (非静默失效); 重连成功走 live.ts 的整页刷路径, 横幅随页面重载一并消失。
export function LiveBootstrap() {
  const [offline, setOffline] = useState(false);
  const pathname = usePathname();

  // 动态设页面标题: SKEIN-<项目名>。
  // 依赖 pathname 而非 [] —— App Router 每次客户端导航都会重新应用 layout.tsx 的
  // `metadata.title = "SKEIN"`, 只在挂载时设一次的话, 点任何链接跳转后项目名就没了。
  useEffect(() => {
    if (cachedProj) { document.title = `SKEIN-${cachedProj}`; return; }
    api.id().then((r) => {
      const parts = String(r).replace(/\/\.skein\/?$/, "").split("/");
      const proj = parts[parts.length - 1];
      if (proj) { cachedProj = proj; document.title = `SKEIN-${proj}`; }
    }).catch(() => {});
  }, [pathname]);

  useEffect(() => {
    startLive();
    const unsub = subscribe((msg) => {
      if (msg.type === "data") location.reload();
      if (msg.type === "offline") setOffline(true);
    });
    return unsub;
  }, []);

  if (!offline) return null;
  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-[300] flex justify-center pt-3">
      <div className="pointer-events-auto rounded-lg bg-coral-600/90 px-4 py-2 text-sm text-white shadow-lg backdrop-blur-md">
        <AlertTriangle className="mr-1.5 inline h-4 w-4" />
        连接已断开, 正在重连…
      </div>
    </div>
  );
}
