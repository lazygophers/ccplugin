"use client";

import { useEffect, useState } from "react";
import { startLive, subscribe } from "@/lib/live";
import { api } from "@/lib/api";

// Boots WS live-updates on client side; subscribes globally to trigger page reloads on "data" messages.
// 断线时渲染顶部横幅提示 (非静默失效); 重连成功走 live.ts 的整页刷路径, 横幅随页面重载一并消失。
export function LiveBootstrap() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    // 动态设页面标题: SKEIN-<项目名>
    api.id().then((r) => {
      const parts = String(r).replace(/\/\.skein\/?$/, "").split("/");
      const proj = parts[parts.length - 1];
      if (proj) document.title = `SKEIN-${proj}`;
    }).catch(() => {});
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
        <i className="fa fa-exclamation-triangle mr-1.5" />
        连接已断开, 正在重连…
      </div>
    </div>
  );
}
