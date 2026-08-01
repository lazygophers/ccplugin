"use client";

import { type ReactNode } from "react";

export function ConfirmDialog({
  open, title, message, confirmText = "确认", cancelText = "取消",
  destructive = false, onConfirm, onCancel,
}: {
  open: boolean;
  title: string;
  message?: ReactNode;
  confirmText?: string;
  cancelText?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onCancel}>
      <div
        className="w-full max-w-sm rounded-xl border border-border/30 bg-card p-5 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="mb-2 text-base font-semibold text-foreground">{title}</h3>
        {message && <div className="mb-4 text-sm text-muted-foreground">{message}</div>}
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-md border border-border px-3 py-1.5 text-xs text-foreground hover:bg-muted/30"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`rounded-md px-3 py-1.5 text-xs text-white ${
              destructive ? "bg-destructive hover:bg-destructive/90" : "bg-primary hover:bg-primary/90"
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
