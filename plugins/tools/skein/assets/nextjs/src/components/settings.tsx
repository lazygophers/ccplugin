"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Cfg {
  max_active: number;
  auto_commit: boolean;
  retain_days: number;
  worktree?: { enabled?: boolean; root?: string };
  web?: { serve?: boolean; board_open?: boolean };
  spec?: { always_budget?: number };
  [key: string]: unknown;
}

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const [cfg, setCfg] = useState<Cfg | null>(null);
  const [form, setForm] = useState<Cfg | null>(null);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getConfig().then((r) => {
      const c = r as unknown as Cfg;
      setCfg(c);
      setForm({ ...c });
    }).catch(() => setErr("读取配置失败"));
  }, []);

  if (!form) {
    return (
      <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40" onClick={onClose}>
        <div className="rounded-lg bg-card/60 p-6 text-sm text-muted-foreground" onClick={e => e.stopPropagation()}>
          {err || "加载配置中…"}
        </div>
      </div>
    );
  }

  const save = async () => {
    if (!cfg) return;
    // ponytail: full payload, delete hooks (RCE defense), same as old settings.js
    const payload = JSON.parse(JSON.stringify(cfg)) as Record<string, unknown>;
    delete payload.hooks;
    payload.max_active = parseInt(String(form.max_active), 10);
    payload.auto_commit = !!form.auto_commit;
    payload.retain_days = parseInt(String(form.retain_days), 10);
    payload.worktree = { ...(cfg.worktree || {}), enabled: !!form.worktree?.enabled, root: form.worktree?.root || "" };
    payload.web = { ...(cfg.web || {}), serve: !!form.web?.serve, board_open: !!form.web?.board_open };
    payload.spec = { ...(cfg.spec || {}), always_budget: parseInt(String(form.spec?.always_budget || 0), 10) };

    const ma = payload.max_active as number, rd = payload.retain_days as number, sb = (payload.spec as Record<string, unknown>)?.always_budget as number;
    if (!Number.isInteger(ma) || ma < 1) return setErr("并发上限须为 ≥1 的整数");
    if (!Number.isInteger(rd)) return setErr("保留天数须为整数");
    if (!Number.isInteger(sb) || sb < 1) return setErr("spec 全文预算须为 ≥1 的整数");
    if (!(payload.worktree as Record<string, unknown>)?.root) return setErr("worktree 根目录不能为空");

    setSaving(true);
    setErr("");
    try {
      const saved = await api.setConfig(payload) as unknown as Cfg;
      setCfg(saved);
      setForm({ ...saved });
      setErr("已保存");
      setTimeout(() => setErr(""), 2000);
    } catch {
      setErr("保存失败");
    } finally {
      setSaving(false);
    }
  };

  const set = <K extends keyof Cfg>(k: K, v: Cfg[K]) => setForm(f => f ? { ...f, [k]: v } : f);
  const setW = (k: string, v: unknown) => setForm(f => f ? { ...f, worktree: { ...f.worktree, [k]: v } } : f);
  const setWeb = (k: string, v: unknown) => setForm(f => f ? { ...f, web: { ...f.web, [k]: v } } : f);
  const setSpec = (k: string, v: unknown) => setForm(f => f ? { ...f, spec: { ...f.spec, [k]: v } } : f);

  const inputCls = "border border-border bg-background rounded-md px-2 py-1 text-sm text-foreground outline-none focus:border-primary";

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-border bg-card/60 shadow-xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <i className="fa fa-cog text-primary" />设置
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <i className="fa fa-times text-lg" />
          </button>
        </div>

        {/* Body */}
        <div className="space-y-3 p-4">
          <p className="text-xs text-muted-foreground">
            下列为当前生效值 (可能含环境变量覆盖); 保存写入 config.yaml。
          </p>

          <div className="grid grid-cols-2 gap-3">
            <Field label="并发上限" hint="≥1 整数">
              <input type="number" step="1" value={String(form.max_active)} onChange={e => set("max_active", +e.target.value)} className={inputCls} />
            </Field>
            <Field label="保留天数" hint="0=完成即归档">
              <input type="number" step="1" value={String(form.retain_days)} onChange={e => set("retain_days", +e.target.value)} className={inputCls} />
            </Field>
            <Field label="自动提交" hint="仅原地模式生效">
              <input type="checkbox" checked={!!form.auto_commit} onChange={e => set("auto_commit", e.target.checked)} />
            </Field>
            <Field label="spec 全文预算" hint="字符数">
              <input type="number" step="1" value={String(form.spec?.always_budget || 0)} onChange={e => setSpec("always_budget", +e.target.value)} className={inputCls} />
            </Field>
            <Field label="启用 worktree">
              <input type="checkbox" checked={!!form.worktree?.enabled} onChange={e => setW("enabled", e.target.checked)} />
            </Field>
            <Field label="worktree 根目录">
              <input type="text" value={form.worktree?.root || ""} onChange={e => setW("root", e.target.value)} className={inputCls} />
            </Field>
            <Field label="看板服务">
              <input type="checkbox" checked={!!form.web?.serve} onChange={e => setWeb("serve", e.target.checked)} />
            </Field>
            <Field label="自动开浏览器">
              <input type="checkbox" checked={!!form.web?.board_open} onChange={e => setWeb("board_open", e.target.checked)} />
            </Field>
          </div>

          {err && <div className={err === "已保存" ? "text-xs text-primary" : "text-xs text-destructive"}>{err}</div>}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t border-border px-4 py-3">
          <button onClick={onClose} className="rounded-md border border-border px-3 py-1.5 text-xs text-foreground hover:bg-muted/30">取消</button>
          <button onClick={save} disabled={saving} className="rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      {children}
      {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
    </label>
  );
}
