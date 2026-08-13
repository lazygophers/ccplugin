"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { Sidebar, Topbar } from "@/components/layout";
import { cn } from "@/lib/utils";
import { RotateCcw, ChevronRight, Search, Code2 } from "lucide-react";

type ParamType = "text" | "number" | "boolean" | "select" | "textarea" | "json";

interface ParamDef {
  name: string;
  label: string;
  desc?: string;
  required?: boolean;
  type?: ParamType;
  placeholder?: string;
  defaultValue?: string;
  options?: { value: string; label: string }[];
}

interface EndpointDef {
  id: string;
  method: "POST";
  path: string;
  label: string;
  desc: string;
  category: string;
  params: ParamDef[];
}

const ENDPOINTS: EndpointDef[] = [
  // 系统
  { id: "sys-id", method: "POST", path: "/__skein__/system/id", label: "项目标识", desc: "返回 .skein 目录的绝对路径", category: "系统", params: [] },
  { id: "sys-rev", method: "POST", path: "/__skein__/system/rev", label: "版本戳", desc: "task.json + 资产 mtime 组合版本号", category: "系统", params: [] },
  { id: "config-get", method: "POST", path: "/__skein__/system/config-get", label: "读取配置", desc: "返回 config.yaml 全量配置", category: "系统", params: [] },
  { id: "config-set", method: "POST", path: "/__skein__/system/config-set", label: "写入配置", desc: "写入 config.yaml (hooks 段被安全策略禁写, 会保留盘上原值)", category: "系统",
    params: [
      { name: "auto_commit", label: "自动提交", desc: "改动后自动 git commit (worktree 模式下强制 true)", type: "boolean", defaultValue: "true" },
      { name: "retain_days", label: "保留天数", desc: "完成 task 保留天数, 超期自动归档; -1=永不", type: "number", defaultValue: "7" },
      { name: "pools.work", label: "并发池: work", desc: "exec subtask 最大并发数", type: "number", defaultValue: "2" },
      { name: "pools.gate", label: "并发池: gate", desc: "check+finishing 阶段最大并发数", type: "number", defaultValue: "3" },
      { name: "worktree.enabled", label: "Worktree 隔离", desc: "启用 per-task git worktree 隔离", type: "boolean", defaultValue: "false" },
      { name: "worktree.root", label: "Worktree 目录", desc: "worktree 存放目录 (相对仓库根)", type: "text", defaultValue: ".worktrees" },
      { name: "web.serve", label: "启动看板服务", desc: "启动 http 看板服务", type: "boolean", defaultValue: "true" },
      { name: "web.board_open", label: "自动打开浏览器", desc: "启动时自动打开浏览器 (仅 tty 生效)", type: "boolean", defaultValue: "true" },
      { name: "spec.core_budget", label: "Spec 核心预算", desc: "SessionStart 常驻注入预算 (字符数)", type: "number", defaultValue: "400" },
      { name: "spec.always_budget", label: "Spec 常驻预算", desc: "每轮 prompt 常驻注入预算 (字符数, ≈300 token)", type: "number", defaultValue: "517" },
      { name: "confirm.unattended", label: "无人值守放行", desc: "允许无人值守放行 confirm (cron/CI 场景)", type: "boolean", defaultValue: "false" },
    ] },

  // Task
  { id: "task-list", method: "POST", path: "/__skein__/task/list", label: "看板数据", desc: "全量 task 卡片 + 概览统计 + 资源池占用", category: "Task", params: [] },
  { id: "dashboard", method: "POST", path: "/__skein__/task/dashboard", label: "概览数据", desc: "看板聚合统计 (总数/活跃/完成/待处理)", category: "Task", params: [] },
  { id: "task-get", method: "POST", path: "/__skein__/task/get", label: "Task 详情", desc: "task.json 全文 + docs (prd/design/findings) + research + prd 结构 + 依赖明细", category: "Task",
    params: [
      { name: "id", label: "Task ID", desc: "task 的唯一标识符", required: true, type: "text", placeholder: "perf-final-verification" },
    ] },
  { id: "task-search", method: "POST", path: "/__skein__/task/search", label: "搜索 Task", desc: "按关键词搜索 task 名称和描述", category: "Task",
    params: [
      { name: "q", label: "关键词", desc: "搜索关键词", required: true, type: "text", placeholder: "内存" },
    ] },
  { id: "task-queue", method: "POST", path: "/__skein__/task/queue", label: "执行队列", desc: "当前调度队列中的 subtask 列表", category: "Task", params: [] },
  { id: "task-create", method: "POST", path: "/__skein__/task/create", label: "创建 Task", desc: "新建 task", category: "Task",
    params: [
      { name: "id", label: "Task ID", required: true, type: "text", placeholder: "new-task-id" },
      { name: "name", label: "名称", required: true, type: "text", placeholder: "任务中文名" },
      { name: "desc", label: "描述", required: true, type: "textarea", placeholder: "任务详细描述" },
      { name: "deps", label: "依赖", desc: "前置 task ID (逗号分隔)", type: "text", placeholder: "task-a,task-b" },
    ] },
  { id: "task-confirm", method: "POST", path: "/__skein__/task/confirm", label: "确认规划", desc: "确认 task 规划, 激活执行阶段 (需 PRD/estimate 就绪)", category: "Task",
    params: [
      { name: "id", label: "Task ID", desc: "要确认的 task", required: true, type: "text", placeholder: "task-id" },
      { name: "force", label: "强制", desc: "跳过硬门检查", type: "boolean", defaultValue: "true" },
    ] },
  { id: "task-priority", method: "POST", path: "/__skein__/task/priority", label: "修改优先级", desc: "设置 task 优先级", category: "Task",
    params: [
      { name: "id", label: "Task ID", required: true, type: "text", placeholder: "task-id" },
      { name: "set", label: "优先级", desc: "目标优先级", required: true, type: "select",
        options: [
          { value: "urgent", label: "urgent — 紧急" },
          { value: "high", label: "high — 高" },
          { value: "normal", label: "normal — 中" },
          { value: "low", label: "low — 低" },
        ], defaultValue: "normal" },
    ] },
  { id: "task-delete", method: "POST", path: "/__skein__/task/delete", label: "删除 Task", desc: "删除 task (移入回收站, 可恢复)", category: "Task",
    params: [
      { name: "id", label: "Task ID", required: true, type: "text", placeholder: "task-id" },
      { name: "force", label: "强制", type: "boolean", defaultValue: "true" },
    ] },
  { id: "task-finish", method: "POST", path: "/__skein__/task/finish", label: "完成 Task", desc: "合并 worktree 并标记 task 为已完成", category: "Task",
    params: [
      { name: "id", label: "Task ID", required: true, type: "text", placeholder: "task-id" },
      { name: "force", label: "强制完成", desc: "跳过验收检查强制完成", type: "boolean", defaultValue: "false" },
    ] },
  { id: "task-clean", method: "POST", path: "/__skein__/task/clean", label: "清理已完成", desc: "归档超过指定天数且无未完成关联的已完成 task", category: "Task",
    params: [
      { name: "days", label: "保留天数", desc: "0=立即归档, N=N 天前完成才归档", type: "number", defaultValue: "0" },
    ] },
  { id: "task-prd", method: "POST", path: "/__skein__/task/prd", label: "PRD 操作", desc: "读取/写入/勾选 PRD 章节", category: "Task",
    params: [
      { name: "id", label: "Task ID", required: true, type: "text", placeholder: "task-id" },
      { name: "action", label: "操作", required: true, type: "select",
        options: [
          { value: "read", label: "read — 读取" },
          { value: "write", label: "write — 覆写" },
          { value: "add", label: "add — 追加" },
          { value: "check", label: "check — 勾选" },
          { value: "uncheck", label: "uncheck — 取消勾选" },
        ], defaultValue: "read" },
      { name: "type", label: "章节类型", required: true, type: "select",
        options: [
          { value: "目标", label: "目标" },
          { value: "验收标准", label: "验收标准" },
        ], defaultValue: "目标" },
      { name: "list", label: "条目内容/序号", desc: "read 不填; write/add 填内容; check/uncheck 填序号", type: "textarea", placeholder: "1 或具体内容" },
    ] },

  // Subtask
  { id: "subtask-add", method: "POST", path: "/__skein__/subtask/add", label: "添加子任务", desc: "给已有 task 添加一个 subtask", category: "Subtask",
    params: [
      { name: "id", label: "Task ID", required: true, type: "text", placeholder: "task-id" },
      { name: "sid", label: "子任务 ID", required: true, type: "text", placeholder: "s1-step-name" },
      { name: "name", label: "名称", required: true, type: "text", placeholder: "子任务中文名" },
      { name: "desc", label: "描述", required: true, type: "textarea", placeholder: "子任务做什么" },
      { name: "estimate", label: "预估工时", required: true, type: "number", placeholder: "2" },
      { name: "deps", label: "依赖", desc: "前置子任务 ID (逗号分隔)", type: "text", placeholder: "s0-xxx" },
    ] },

  // Spec
  { id: "spec-list", method: "POST", path: "/__skein__/spec/list", label: "Spec 列表", desc: ".skein/spec 下的规范文件列表", category: "Spec", params: [] },
  { id: "spec-meta", method: "POST", path: "/__skein__/spec/meta", label: "Spec 元信息", desc: "规范文件的元数据 (namespace/inclusion/keywords)", category: "Spec",
    params: [
      { name: "page", label: "页码", desc: "从 1 开始", type: "number", defaultValue: "1" },
      { name: "page_size", label: "每页条数", type: "number", defaultValue: "20" },
      { name: "namespace", label: "命名空间", desc: "按 namespace 筛选", type: "text", placeholder: "rules" },
      { name: "category", label: "类目", desc: "按 category 筛选", type: "text", placeholder: "product" },
      { name: "keyword", label: "关键词", desc: "按 keyword 模糊筛选", type: "text" },
    ] },
  { id: "spec-get", method: "POST", path: "/__skein__/spec/get", label: "读取 Spec 文件", desc: "读取单篇规范文件内容", category: "Spec",
    params: [
      { name: "path", label: "文件路径", desc: "相对于 .skein/spec 的路径", required: true, type: "text", placeholder: "rules/product/example.md" },
    ] },
  { id: "spec-search", method: "POST", path: "/__skein__/spec/search", label: "搜索 Spec", desc: "全文搜索规范文件", category: "Spec",
    params: [
      { name: "q", label: "关键词", required: true, type: "text", placeholder: "验收" },
    ] },
  { id: "spec-save", method: "POST", path: "/__skein__/spec/save", label: "保存 Spec", desc: "覆写已有规范文件", category: "Spec",
    params: [
      { name: "path", label: "文件路径", required: true, type: "text", placeholder: "rules/product/x.md" },
      { name: "content", label: "文件内容", required: true, type: "textarea", placeholder: "# 标题\n正文..." },
    ] },
  { id: "spec-create", method: "POST", path: "/__skein__/spec/create", label: "创建 Spec", desc: "新建规范文件", category: "Spec",
    params: [
      { name: "path", label: "文件路径", required: true, type: "text", placeholder: "rules/product/new.md" },
      { name: "content", label: "初始内容", type: "textarea", placeholder: "(可选)" },
    ] },
  { id: "spec-delete", method: "POST", path: "/__skein__/spec/delete", label: "删除 Spec", desc: "删除规范文件", category: "Spec",
    params: [
      { name: "path", label: "文件路径", required: true, type: "text", placeholder: "rules/product/old.md" },
    ] },

  // 归档
  { id: "archive-list", method: "POST", path: "/__skein__/archive/list", label: "归档列表", desc: "已归档 task 列表", category: "归档", params: [] },
  { id: "archive-del", method: "POST", path: "/__skein__/archive/delete", label: "删除归档项", desc: "永久删除一个已归档的 task (不可恢复)", category: "归档",
    params: [
      { name: "id", label: "Task ID", desc: "要删除的归档 task ID", required: true, type: "text", placeholder: "old-task-id" },
    ] },

  // 回收站
  { id: "trash-list", method: "POST", path: "/__skein__/trash/list", label: "回收站列表", desc: "已删除 task 列表 (可恢复)", category: "回收站", params: [] },
  { id: "trash-purge", method: "POST", path: "/__skein__/trash/purge", label: "清空回收站", desc: "永久清除回收站 (指定 ID 清单个, 留空清全部)", category: "回收站",
    params: [
      { name: "id", label: "Task ID", desc: "留空则清空全部回收站", type: "text", placeholder: "(可选)" },
    ] },
];

const CATEGORIES = ["全部", "系统", "Task", "Subtask", "Spec", "归档", "回收站"];
const METHOD_COLORS: Record<string, string> = { POST: "text-amber-500" };

// ── Param field renderer ──
function ParamField({ p, value, onChange }: { p: ParamDef; value: string; onChange: (v: string) => void }) {
  const labelEl = (
    <label className="mb-1 flex items-center gap-1.5 text-xs font-medium text-foreground">
      {p.label}
      {p.required && <span className="text-destructive text-[10px]">*必填</span>}
      <code className="font-mono text-[10px] text-muted-foreground/70">{p.name}</code>
    </label>
  );
  const descEl = p.desc && <p className="mb-1.5 text-[10px] text-muted-foreground">{p.desc}</p>;

  const fieldType = p.type || "text";

  if (fieldType === "boolean") {
    const checked = value === "true";
    return (
      <div>
        {labelEl}
        {descEl}
        <button
          type="button"
          onClick={() => onChange(!checked ? "true" : "false")}
          className={cn(
            "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
            checked ? "bg-primary" : "bg-muted"
          )}
        >
          <span className={cn("inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform", checked ? "translate-x-5" : "translate-x-1")} />
        </button>
        <span className="ml-2 text-[10px] text-muted-foreground">{checked ? "true" : "false"}</span>
      </div>
    );
  }

  if (fieldType === "select" && p.options) {
    return (
      <div>
        {labelEl}
        {descEl}
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground outline-none focus:border-primary"
        >
          {!p.required && <option value="">(不传)</option>}
          {p.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
    );
  }

  if (fieldType === "textarea") {
    return (
      <div>
        {labelEl}
        {descEl}
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={p.placeholder}
          rows={4}
          className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground outline-none focus:border-primary"
        />
      </div>
    );
  }

  if (fieldType === "json") {
    return (
      <div>
        {labelEl}
        {descEl}
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={p.placeholder}
          rows={8}
          className="w-full rounded-md border border-border bg-background px-2 py-1.5 font-mono text-xs text-foreground outline-none focus:border-primary"
        />
      </div>
    );
  }

  // text / number
  return (
    <div>
      {labelEl}
      {descEl}
      <input
        type={fieldType === "number" ? "number" : "text"}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={p.placeholder}
        className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground outline-none focus:border-primary"
      />
    </div>
  );
}

export default function ApiExplorerPage() {
  const [selectedId, setSelectedId] = useState<string>(ENDPOINTS[0].id);
  const [filter, setFilter] = useState("全部");
  const [search, setSearch] = useState("");
  const [paramValues, setParamValues] = useState<Record<string, Record<string, string>>>({});
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const filtered = ENDPOINTS.filter(e => {
    if (filter !== "全部" && e.category !== filter) return false;
    if (search && !e.label.toLowerCase().includes(search.toLowerCase()) && !e.path.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const selected = ENDPOINTS.find(e => e.id === selectedId) || ENDPOINTS[0];

  const getParamValue = (paramName: string) =>
    paramValues[selected.id]?.[paramName] ?? selected.params.find(p => p.name === paramName)?.defaultValue ?? "";

  const setParamValue = useCallback((paramName: string, value: string) => {
    setParamValues(prev => ({
      ...prev,
      [selected.id]: { ...(prev[selected.id] || {}), [paramName]: value },
    }));
  }, [selected.id]);

  // Build request body (all endpoints are POST)
  const requestPreview = useMemo(() => {
    const body: Record<string, unknown> = {};
    for (const p of selected.params) {
      const v = getParamValue(p.name);
      if (v === "" && !p.required) continue;
      let val: unknown = v;
      if (p.type === "boolean") val = v === "true";
      else if (p.type === "number") val = v ? Number(v) : undefined;
      else if (p.type === "json") { try { val = JSON.parse(v || "{}"); } catch { val = v; } }
      if (val === undefined) continue;
      if (p.name.includes(".")) {
        const parts = p.name.split(".");
        let cur = body;
        for (let i = 0; i < parts.length - 1; i++) {
          if (!cur[parts[i]] || typeof cur[parts[i]] !== "object") cur[parts[i]] = {};
          cur = cur[parts[i]] as Record<string, unknown>;
        }
        cur[parts[parts.length - 1]] = val;
      } else {
        body[p.name] = val;
      }
    }
    return JSON.stringify(body, null, 2);
  }, [selected, paramValues, selected.id]);

  // Reset on endpoint switch
  useEffect(() => {
    setResponse(null);
    setError(null);
  }, [selectedId]);

  const sendRequest = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const opts: RequestInit = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: requestPreview,
      };

      const res = await fetch(selected.path, { ...opts, cache: "no-store" });
      const ct = res.headers.get("content-type") || "";
      let result: string;
      if (ct.includes("application/json")) {
        result = JSON.stringify(await res.json(), null, 2);
      } else {
        result = await res.text();
      }

      if (!res.ok) {
        setError(`HTTP ${res.status} ${res.statusText}\n${result}`);
      } else {
        setResponse(result);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-4">
            <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold text-foreground">
              <Code2 className="h-6 w-6 text-primary" />
              API Explorer
            </h1>
            <p className="text-sm text-muted-foreground">{ENDPOINTS.length} 个端点 · 交互式参数填写 · 实时 JSON 预览</p>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
            {/* Left: endpoint list */}
            <div className="lg:col-span-1">
              <div className="sticky top-0 space-y-2">
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="搜索端点..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full rounded-md border border-border bg-card/60 py-2 pl-7 pr-3 text-xs text-foreground outline-none focus:border-primary"
                  />
                </div>
                <div className="flex flex-wrap gap-1">
                  {CATEGORIES.map(c => (
                    <button
                      key={c}
                      onClick={() => setFilter(c)}
                      className={cn(
                        "rounded-full border px-2 py-0.5 text-[10px] font-medium transition-colors",
                        filter === c ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/50"
                      )}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-2 space-y-0.5">
                {filtered.map(e => (
                  <button
                    key={e.id}
                    onClick={() => setSelectedId(e.id)}
                    className={cn(
                      "flex w-full items-start gap-2 rounded-md p-2 text-left transition-colors",
                      selectedId === e.id ? "bg-primary/10 ring-1 ring-primary/30" : "hover:bg-muted/30"
                    )}
                  >
                    <span className={cn("mt-0.5 w-10 shrink-0 font-mono text-[10px] font-bold", METHOD_COLORS[e.method])}>{e.method}</span>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-xs font-medium text-foreground">{e.label}</div>
                      <div className="truncate font-mono text-[10px] text-muted-foreground">{e.path}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Middle: params form */}
            <div className="lg:col-span-2">
              <div className="rounded-lg border border-border bg-card/60 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <span className={cn("font-mono text-xs font-bold", METHOD_COLORS[selected.method])}>{selected.method}</span>
                  <code className="text-xs text-foreground">{selected.path}</code>
                </div>
                <h3 className="mb-1 text-sm font-semibold text-foreground">{selected.label}</h3>
                <p className="mb-4 text-xs text-muted-foreground">{selected.desc}</p>

                {selected.params.length > 0 ? (
                  <div className="space-y-4">
                    {selected.params.map(p => (
                      <ParamField
                        key={p.name}
                        p={p}
                        value={getParamValue(p.name)}
                        onChange={v => setParamValue(p.name, v)}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="py-4 text-center text-xs text-muted-foreground">此端点无参数</p>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={sendRequest}
                    disabled={loading}
                    className="flex flex-1 items-center justify-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                  >
                    {loading ? "请求中..." : "发送请求"}
                  </button>
                  <button
                    onClick={() => { setResponse(null); setError(null); setParamValues({}); }}
                    className="flex items-center justify-center rounded-md border border-border px-3 py-2 text-xs text-muted-foreground transition-colors hover:bg-muted/30"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {/* Request preview */}
              {selected.params.length > 0 && (
                <div className="mt-3 rounded-lg border border-border bg-card/60 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-muted-foreground">
                      请求体 JSON
                    </span>
                    <button
                      onClick={() => navigator.clipboard?.writeText(requestPreview)}
                      className="text-[10px] text-muted-foreground transition-colors hover:text-primary"
                    >
                      复制
                    </button>
                  </div>
                  <pre className="overflow-auto rounded-md bg-background p-2.5 font-mono text-[11px] text-foreground whitespace-pre-wrap break-all max-h-40">{requestPreview}</pre>
                </div>
              )}
            </div>

            {/* Right: response */}
            <div className="lg:col-span-2">
              <div className="sticky top-0 rounded-lg border border-border bg-card/60 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">响应</h3>
                  {response && (
                    <button
                      onClick={() => navigator.clipboard?.writeText(response)}
                      className="text-[10px] text-muted-foreground transition-colors hover:text-primary"
                    >
                      复制
                    </button>
                  )}
                </div>
                {loading ? (
                  <div className="py-12 text-center text-sm text-muted-foreground">请求中…</div>
                ) : error ? (
                  <pre className="overflow-auto rounded-md bg-destructive/10 p-3 font-mono text-xs text-destructive whitespace-pre-wrap break-all">{error}</pre>
                ) : response ? (
                  <pre className="overflow-auto rounded-md bg-background p-3 font-mono text-xs text-foreground whitespace-pre-wrap break-all max-h-[600px]">{response}</pre>
                ) : (
                  <div className="py-12 text-center text-sm text-muted-foreground">
                    <ChevronRight className="mx-auto mb-2 h-6 w-6 opacity-30" />
                    填写参数后点击「发送请求」
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
