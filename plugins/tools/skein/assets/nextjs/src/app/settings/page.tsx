"use client";

import { useEffect, useState } from "react";
import { Sidebar, Topbar } from "@/components/layout";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Cfg {
  pools: { work: number; gate: number };
  auto_commit: boolean;
  retain_days: number;
  worktree?: { enabled?: boolean; root?: string };
  web?: { serve?: boolean; board_open?: boolean };
  spec?: { always_budget?: number };
  [key: string]: unknown;
}

export default function SettingsPage() {
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
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex min-h-0 flex-1 flex-col lg:ml-[220px]">
          <Topbar />
          <main className="flex-1 overflow-y-auto p-6">
            <p className="text-sm text-muted-foreground">{err || "加载配置中…"}</p>
          </main>
        </div>
      </div>
    );
  }

  const save = async () => {
    if (!cfg) return;
    const payload = JSON.parse(JSON.stringify(cfg)) as Record<string, unknown>;
    delete payload.hooks;
    payload.pools = { work: parseInt(String(form.pools?.work), 10), gate: parseInt(String(form.pools?.gate), 10) };
    payload.auto_commit = !!form.auto_commit;
    payload.retain_days = parseInt(String(form.retain_days), 10);
    payload.worktree = { ...(cfg.worktree || {}), enabled: !!form.worktree?.enabled, root: form.worktree?.root || "" };
    payload.web = { ...(cfg.web || {}), serve: !!form.web?.serve, board_open: !!form.web?.board_open };
    payload.spec = { ...(cfg.spec || {}), always_budget: parseInt(String(form.spec?.always_budget || 0), 10) };

    const pw = (payload.pools as Cfg["pools"]).work, pg = (payload.pools as Cfg["pools"]).gate;
    const rd = payload.retain_days as number, sb = (payload.spec as Record<string, unknown>)?.always_budget as number;
    if (!Number.isInteger(pw) || pw < 1) return setErr("work 池上限须为 ≥1 的整数");
    if (!Number.isInteger(pg) || pg < 1) return setErr("gate 池上限须为 ≥1 的整数");
    if (!Number.isInteger(rd)) return setErr("保留天数须为整数");
    if (!Number.isInteger(sb) || sb < 1) return setErr("spec 全文预算须为 ≥1 的整数");
    if (!(payload.worktree as Record<string, unknown>)?.root) return setErr("worktree 根目录不能为空");

    setSaving(true);
    setErr("");
    try {
      await api.setConfig(payload);
      // 重新拉取生效配置 (后端 pydantic 校验可能兜底修改值, 以盘上为准)
      const fresh = await api.getConfig() as unknown as Cfg;
      setCfg(fresh);
      setForm({ ...fresh });
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
  const setPools = (k: "work" | "gate", v: number) => setForm(f => f ? { ...f, pools: { ...f.pools, [k]: v } } : f);

  const inputCls = "border border-border bg-background rounded-md px-2 py-1 text-sm text-foreground outline-none focus:border-primary";

  const Toggle = ({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) => (
    <button type="button" onClick={() => onChange(!checked)}
      className={cn("relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
        checked ? "bg-primary" : "bg-muted")}>
      <span className={cn("inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform",
        checked ? "translate-x-5" : "translate-x-1")} />
    </button>
  );

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-h-0 flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          <h1 className="mb-1 text-2xl font-bold text-foreground">设置</h1>
          <p className="mb-6 text-sm text-muted-foreground">
            下列为当前生效值 (可能含环境变量覆盖); 保存写入 config.yaml。
          </p>

          <div className="max-w-lg space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="work 池上限" hint="≥1 整数, 并发执行 subtask 数">
                <input type="number" step="1" value={String(form.pools?.work)} onChange={e => setPools("work", +e.target.value)} className={inputCls} />
              </Field>
              <Field label="gate 池上限" hint="≥1 整数, 并发检查中+收尾中 task 数">
                <input type="number" step="1" value={String(form.pools?.gate)} onChange={e => setPools("gate", +e.target.value)} className={inputCls} />
              </Field>
              <Field label="保留天数" hint="0=完成即归档">
                <input type="number" step="1" value={String(form.retain_days)} onChange={e => set("retain_days", +e.target.value)} className={inputCls} />
              </Field>
              <Field label="自动提交" hint="仅原地模式生效">
                <Toggle checked={!!form.auto_commit} onChange={v => set("auto_commit", v)} />
              </Field>
              <Field label="spec 全文预算" hint="字符数">
                <input type="number" step="1" value={String(form.spec?.always_budget || 0)} onChange={e => setSpec("always_budget", +e.target.value)} className={inputCls} />
              </Field>
              <Field label="启用 worktree">
                <Toggle checked={!!form.worktree?.enabled} onChange={v => setW("enabled", v)} />
              </Field>
              <Field label="worktree 根目录">
                <input type="text" value={form.worktree?.root || ""} onChange={e => setW("root", e.target.value)} className={inputCls} />
              </Field>
              <Field label="看板服务">
                <Toggle checked={!!form.web?.serve} onChange={v => setWeb("serve", v)} />
              </Field>
              <Field label="自动开浏览器">
                <Toggle checked={!!form.web?.board_open} onChange={v => setWeb("board_open", v)} />
              </Field>
            </div>

            {err && <div className={err === "已保存" ? "text-xs text-primary" : "text-xs text-destructive"}>{err}</div>}

            <div className="flex justify-end gap-2 border-t border-border pt-3">
              <button onClick={save} disabled={saving} className="rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                {saving ? "保存中…" : "保存"}
              </button>
            </div>
          </div>
        </main>
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
