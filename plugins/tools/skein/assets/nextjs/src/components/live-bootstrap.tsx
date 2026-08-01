"use client";

import { useEffect } from "react";
import { startLive, subscribe } from "@/lib/live";
import { api } from "@/lib/api";

// Boots WS live-updates on client side; subscribes globally to trigger page reloads on "data" messages.
export function LiveBootstrap() {
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
    });
    return unsub;
  }, []);
  return null;
}
