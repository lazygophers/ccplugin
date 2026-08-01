"use client";

import { useState, useCallback, createContext, useContext, type ReactNode } from "react";

type Toast = { id: number; msg: string; type: "info" | "success" | "error" };

const ToastCtx = createContext<(msg: string, type?: Toast["type"]) => void>(() => {});

export function useToast() {
  return useContext(ToastCtx);
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback((msg: string, type: Toast["type"] = "info") => {
    const id = ++nextId;
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 2500);
  }, []);

  return (
    <ToastCtx.Provider value={show}>
      {children}
      <div className="pointer-events-none fixed bottom-6 left-1/2 z-[200] flex -translate-x-1/2 flex-col items-center gap-2">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`pointer-events-auto rounded-lg px-4 py-2 text-sm shadow-lg backdrop-blur-md ${
              t.type === "success" ? "bg-seaweed-600/90 text-white"
              : t.type === "error" ? "bg-coral-600/90 text-white"
              : "bg-card/90 text-foreground border border-border/30"
            }`}
          >
            {t.type === "success" && <i className="fa fa-check-circle mr-1.5" />}
            {t.type === "error" && <i className="fa fa-exclamation-circle mr-1.5" />}
            {t.msg}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
