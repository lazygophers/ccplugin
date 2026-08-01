"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Sidebar, Topbar } from "@/components/layout";
import { api, type SpecItem, type SpecSearchResult, type SpecMetaItem } from "@/lib/api";
import { renderMd } from "@/lib/md";
import { cn } from "@/lib/utils";

export default function SpecPage() {
  const [specs, setSpecs] = useState<SpecItem[]>([]);
  const [metaMap, setMetaMap] = useState<Record<string, SpecMetaItem>>({});
  const [selected, setSelected] = useState<SpecItem | null>(null);
  const [content, setContent] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [editText, setEditText] = useState("");
  const [saveMsg, setSaveMsg] = useState("");

  // 搜索
  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState<SpecSearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 筛选
  const [filterType, setFilterType] = useState<string | null>(null);
  const [filterTag, setFilterTag] = useState<string | null>(null);

  // 树状展开
  const [expandedNs, setExpandedNs] = useState<Set<string>>(new Set());
  const [expandedCat, setExpandedCat] = useState<Set<string>>(new Set());

  // 新建
  const [showCreate, setShowCreate] = useState(false);
  const [newNs, setNewNs] = useState("");
  const [newCat, setNewCat] = useState("");
  const [newName, setNewName] = useState("");
  const [createMsg, setCreateMsg] = useState("");

  const refreshList = useCallback(() => {
    api.spec().then((r) => {
      const tree = r as unknown as Record<string, Record<string, string[]>>;
      const items: SpecItem[] = [];
      for (const [ns, cats] of Object.entries(tree)) {
        for (const [cat, files] of Object.entries(cats)) {
          for (const f of files) {
            items.push({ id: `${ns}/${cat}/${f}`, title: f.replace(/\.md$/, ""), namespace: ns, category: cat, inclusion: `${ns}/${cat}/${f}` });
          }
        }
      }
      setSpecs(items);
    }).catch(() => {});
    api.specMeta().then((r) => {
      const list = r as unknown as SpecMetaItem[];
      const map: Record<string, SpecMetaItem> = {};
      for (const m of list) map[m.path] = m;
      setMetaMap(map);
    }).catch(() => {});
  }, []);

  useEffect(() => { refreshList(); }, [refreshList]);

  // 防抖搜索
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = searchQ.trim();
    if (!q) { setSearchResults(null); setSearching(false); return; }
    setSearching(true);
    debounceRef.current = setTimeout(() => {
      api.specSearch(q).then((r) => {
        setSearchResults((r as unknown as SpecSearchResult[]) || []);
        setSearching(false);
      }).catch(() => setSearching(false));
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchQ]);

  function openSpec(s: SpecItem) {
    setSelected(s);
    setContent("");
    setEditMode(false);
    api.specFile(s.inclusion).then((r) => {
      const c = ((r as Record<string, unknown>).content as string) || "";
      setContent(c);
      setEditText(c);
    }).catch(() => setContent("加载失败"));
  }

  function openSearchResult(r: SpecSearchResult) {
    const parts = r.path.split("/");
    const f = parts[parts.length - 1];
    openSpec({
      id: r.path,
      title: r.title || f.replace(/\.md$/, ""),
      namespace: parts[0] || "",
      category: parts[1] || "",
      inclusion: r.path,
    });
  }

  async function saveSpec() {
    if (!selected) return;
    setSaveMsg("保存中…");
    try {
      await api.specSave(selected.inclusion, editText);
      setContent(editText);
      setEditMode(false);
      setSaveMsg("已保存");
      refreshList();
      setTimeout(() => setSaveMsg(""), 2000);
    } catch {
      setSaveMsg("保存失败");
    }
  }

  async function deleteSpec() {
    if (!selected) return;
    if (!confirm(`确认删除 "${selected.inclusion}"？`)) return;
    setSaveMsg("删除中…");
    try {
      await api.specDelete(selected.inclusion);
      setSelected(null);
      setContent("");
      setSaveMsg("");
      refreshList();
    } catch {
      setSaveMsg("删除失败");
    }
  }

  async function createSpec() {
    const ns = newNs.trim();
    const cat = newCat.trim();
    const name = newName.trim();
    if (!ns || !cat || !name) { setCreateMsg("类型、分类、名称均必填"); return; }
    const fname = name.endsWith(".md") ? name : `${name}.md`;
    const p = `${ns}/${cat}/${fname}`;
    setCreateMsg("创建中…");
    try {
      await api.specCreate(p);
      setShowCreate(false);
      setNewNs(""); setNewCat(""); setNewName("");
      setCreateMsg("");
      refreshList();
      openSpec({ id: p, title: fname.replace(/\.md$/, ""), namespace: ns, category: cat, inclusion: p });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "创建失败";
      setCreateMsg(msg.includes("已存在") ? "文件已存在" : "创建失败");
    }
  }

  function highlight(text: string, q: string) {
    if (!q) return text;
    const ql = q.toLowerCase();
    const idx = text.toLowerCase().indexOf(ql);
    if (idx < 0) return text;
    return text.slice(0, idx) + '<mark class="rounded bg-primary/20 px-0.5 text-foreground">' + text.slice(idx, idx + q.length) + '</mark>' + text.slice(idx + q.length);
  }

  // 从 metaMap 提取 distinct types (namespace) 和 keywords (tags)
  const allTypes = [...new Set(Object.values(metaMap).map(m => m.namespace).filter(Boolean))].sort();
  const allTags = [...new Set(Object.values(metaMap).flatMap(m => m.keywords))].sort();

  // 新建: 从现有 tree 提取可选 namespace 和 category
  const treeData = specs.reduce<{ ns: Set<string>; cat: Set<string> }>((acc, s) => {
    if (s.namespace) acc.ns.add(s.namespace);
    if (s.category) acc.cat.add(s.category);
    return acc;
  }, { ns: new Set(), cat: new Set() });
  const nsOptions = [...treeData.ns].sort();
  const catOptions = [...treeData.cat].sort();

  // 筛选 specs
  const filteredSpecs = specs.filter(s => {
    const m = metaMap[s.inclusion];
    if (filterType && (!m || m.namespace !== filterType)) return false;
    if (filterTag && (!m || !m.keywords.includes(filterTag))) return false;
    return true;
  });

  // 树状分组: namespace → category → [specs]
  const specTree = filteredSpecs.reduce<Record<string, Record<string, SpecItem[]>>>((acc, s) => {
    if (!acc[s.namespace]) acc[s.namespace] = {};
    if (!acc[s.namespace][s.category]) acc[s.namespace][s.category] = [];
    acc[s.namespace][s.category].push(s);
    return acc;
  }, {});

  function toggleNs(ns: string) {
    setExpandedNs(prev => { const n = new Set(prev); n.has(ns) ? n.delete(ns) : n.add(ns); return n; });
  }
  function toggleCat(key: string) {
    setExpandedCat(prev => { const n = new Set(prev); n.has(key) ? n.delete(key) : n.add(key); return n; });
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-h-0 flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex min-h-0 flex-1 flex-col p-6">
          <div className="mb-4 flex flex-shrink-0 items-center justify-between">
            <div>
              <h1 className="mb-1 text-2xl font-bold text-foreground">规范</h1>
              <p className="text-sm text-muted-foreground">{specs.length} 条规范 · 来自 .skein/spec/</p>
            </div>
            <button
              onClick={() => { setShowCreate(true); setNewNs(""); setNewCat(""); setNewName(""); setCreateMsg(""); }}
              className="rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90"
            >
              <i className="fa fa-plus mr-1" />新建
            </button>
          </div>

          {/* 新建表单 */}
          {showCreate && (
            <div className="mb-4 flex-shrink-0 rounded-lg border border-primary/30 bg-card/60 p-3">
              <div className="mb-2 text-xs font-medium text-foreground">新建规范文件</div>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={newNs}
                  onChange={e => setNewNs(e.target.value)}
                  className="rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground outline-none focus:border-primary"
                >
                  <option value="">选择类型…</option>
                  {nsOptions.map(ns => <option key={ns} value={ns}>{ns}</option>)}
                </select>
                <span className="text-muted-foreground">/</span>
                <select
                  value={newCat}
                  onChange={e => setNewCat(e.target.value)}
                  className="rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground outline-none focus:border-primary"
                >
                  <option value="">选择分类…</option>
                  {catOptions.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <span className="text-muted-foreground">/</span>
                <input
                  type="text"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter") createSpec(); if (e.key === "Escape") setShowCreate(false); }}
                  placeholder="文件名"
                  className="w-40 rounded-md border border-border bg-background px-2 py-1.5 font-mono text-xs text-foreground outline-none focus:border-primary"
                  autoFocus
                />
                <span className="text-xs text-muted-foreground">.md</span>
                <button onClick={createSpec} className="rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90">创建</button>
                <button onClick={() => setShowCreate(false)} className="rounded-md border border-border px-3 py-1.5 text-xs text-foreground hover:bg-muted/30">取消</button>
              </div>
              {createMsg && <div className="mt-1.5 text-xs text-destructive">{createMsg}</div>}
            </div>
          )}

          {/* 搜索框 */}
          <div className="relative mb-4 flex-shrink-0">
            <i className="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground" />
            <input
              type="text"
              value={searchQ}
              onChange={e => setSearchQ(e.target.value)}
              placeholder="搜索规范内容…"
              className="w-full rounded-lg border border-border/30 bg-card/40 py-2 pl-9 pr-8 text-sm text-foreground outline-none focus:border-primary/50"
            />
            {searchQ && (
              <button onClick={() => setSearchQ("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                <i className="fa fa-times" />
              </button>
            )}
          </div>

          {/* 类型/标签筛选 */}
          {(allTypes.length > 0 || allTags.length > 0) && !searchQ && (
            <div className="mb-4 flex flex-shrink-0 flex-wrap items-center gap-1.5">
              <span className="text-xs text-muted-foreground mr-1">类型:</span>
              <button
                onClick={() => setFilterType(null)}
                className={cn("rounded-full border px-2.5 py-0.5 text-[11px] transition-colors", !filterType ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/40")}
              >
                全部
              </button>
              {allTypes.map(t => (
                <button
                  key={t}
                  onClick={() => setFilterType(filterType === t ? null : t)}
                  className={cn("rounded-full border px-2.5 py-0.5 text-[11px] transition-colors", filterType === t ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/40")}
                >
                  {t}
                </button>
              ))}
              {allTags.length > 0 && (
                <>
                  <span className="text-xs text-muted-foreground ml-3 mr-1">标签:</span>
                  {allTags.slice(0, 15).map(t => (
                    <button
                      key={t}
                      onClick={() => setFilterTag(filterTag === t ? null : t)}
                      className={cn("rounded-full border px-2.5 py-0.5 text-[11px] transition-colors", filterTag === t ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/40")}
                    >
                      {t}
                    </button>
                  ))}
                  {allTags.length > 15 && <span className="text-[11px] text-muted-foreground">+{allTags.length - 15}</span>}
                </>
              )}
              {(filterType || filterTag) && (
                <button onClick={() => { setFilterType(null); setFilterTag(null); }} className="ml-2 text-[11px] text-destructive hover:underline">
                  清除筛选
                </button>
              )}
            </div>
          )}

          <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Spec list / search results */}
            <div className="min-h-0 overflow-y-auto space-y-2 rounded-lg border border-border/30 bg-card/40 p-2">
              {searchResults ? (
                <>
                  {searching && (
                    <div className="py-6 text-center text-sm text-muted-foreground">
                      <i className="fa fa-spinner fa-spin mr-2" />搜索中…
                    </div>
                  )}
                  {!searching && searchResults.length === 0 && (
                    <div className="py-6 text-center text-sm text-muted-foreground">
                      <i className="fa fa-search mb-2 text-2xl opacity-40" />
                      <div>无匹配结果</div>
                    </div>
                  )}
                  {!searching && searchResults.map((r) => (
                    <button
                      key={r.path}
                      onClick={() => openSearchResult(r)}
                      className={cn(
                        "w-full rounded-lg border p-3 text-left transition-all",
                        selected?.inclusion === r.path
                          ? "border-primary/40 bg-primary/5 shadow-sm"
                          : "border-border bg-card/60 hover:border-primary/30"
                      )}
                    >
                      <div className="text-xs text-muted-foreground mb-1">{r.path}</div>
                      <div className="text-sm font-medium text-foreground mb-1">{r.title}</div>
                      {r.snippet && (
                        <div className="text-xs text-muted-foreground line-clamp-2">
                          <span dangerouslySetInnerHTML={{ __html: highlight(r.snippet, searchQ.trim()) }} />
                        </div>
                      )}
                    </button>
                  ))}
                </>
              ) : (
                <>
                  {/* 树状分级列表 */}
                  {Object.entries(specTree).map(([ns, cats]) => {
                    const nsCount = Object.values(cats).reduce((a, b) => a + b.length, 0);
                    const nsKey = ns;
                    const nsOpen = expandedNs.has(nsKey);
                    return (
                      <div key={nsKey} className="mb-1">
                        {/* 一级: namespace */}
                        <button
                          onClick={() => toggleNs(nsKey)}
                          className="flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-muted/30"
                        >
                          <i className={cn("fa fa-chevron-right text-[10px] text-muted-foreground transition-transform", nsOpen && "rotate-90")} />
                          <span className="text-sm font-bold text-foreground">{ns}</span>
                          <span className="text-[10px] text-muted-foreground">({nsCount})</span>
                        </button>
                        {nsOpen && (
                          <div className="ml-3 border-l border-border/40 pl-1">
                            {Object.entries(cats).map(([cat, files]) => {
                              const catKey = `${ns}/${cat}`;
                              const catOpen = expandedCat.has(catKey);
                              return (
                                <div key={catKey} className="mb-0.5">
                                  {/* 二级: category */}
                                  <button
                                    onClick={() => toggleCat(catKey)}
                                    className="flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left transition-colors hover:bg-muted/30"
                                  >
                                    <i className={cn("fa fa-chevron-right text-[9px] text-muted-foreground transition-transform", catOpen && "rotate-90")} />
                                    <span className="text-xs font-semibold text-muted-foreground">{cat}</span>
                                    <span className="text-[10px] text-muted-foreground/60">({files.length})</span>
                                  </button>
                                  {catOpen && (
                                    <div className="ml-3 border-l border-border/30 pl-1">
                                      {files.map((s) => {
                                        const m = metaMap[s.inclusion];
                                        return (
                                          <button
                                            key={s.id}
                                            onClick={() => openSpec(s)}
                                            className={cn(
                                              "flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left transition-colors",
                                              selected?.id === s.id
                                                ? "bg-primary/10 text-primary"
                                                : "text-foreground/80 hover:bg-muted/30"
                                            )}
                                          >
                                            <i className="fa fa-file-text-o text-[9px] text-muted-foreground/60" />
                                            <span className="truncate text-xs">{m?.title || s.title}</span>
                                            {m?.keywords?.[0] && (
                                              <span className="ml-auto rounded bg-muted/40 px-1 py-0.5 text-[8px] text-muted-foreground/80">{m.keywords[0]}</span>
                                            )}
                                          </button>
                                        );
                                      })}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {filteredSpecs.length === 0 && (
                    <div className="py-10 text-center">
                      <i className="fa fa-file-text-o mb-2 text-3xl text-muted-foreground opacity-40" />
                      <div className="text-muted-foreground text-sm">{specs.length === 0 ? "暂无规范" : "无匹配筛选"}</div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Detail view */}
            <div className="flex min-h-0 flex-col lg:col-span-2">
              {selected ? (
                <div className="flex min-h-0 flex-1 flex-col rounded-lg border border-border bg-card/60 p-4">
                  <div className="mb-3 flex flex-shrink-0 items-center justify-between">
                    <div className="min-w-0">
                      <h2 className="text-sm font-semibold text-foreground">{selected.title}</h2>
                      <div className="truncate text-xs text-muted-foreground">{selected.inclusion}</div>
                    </div>
                    <div className="flex flex-shrink-0 items-center gap-2">
                      {saveMsg && <span className="text-xs text-muted-foreground">{saveMsg}</span>}
                      {!editMode ? (
                        <>
                          <button onClick={() => setEditMode(true)} className="rounded-md border border-border px-2 py-1 text-xs text-foreground hover:bg-muted/30">
                            <i className="fa fa-pencil mr-1" />编辑
                          </button>
                          <button onClick={deleteSpec} className="rounded-md border border-destructive/40 px-2 py-1 text-xs text-destructive hover:bg-destructive/10">
                            <i className="fa fa-trash mr-1" />删除
                          </button>
                        </>
                      ) : (
                        <>
                          <button onClick={() => { setEditText(content); setEditMode(false); }} className="rounded-md border border-border px-2 py-1 text-xs text-foreground hover:bg-muted/30">
                            取消
                          </button>
                          <button onClick={saveSpec} className="rounded-md bg-primary px-2 py-1 text-xs text-primary-foreground hover:bg-primary/90">
                            保存
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  {editMode ? (
                    <textarea
                      value={editText}
                      onChange={e => setEditText(e.target.value)}
                      className="min-h-0 w-full flex-1 resize-none rounded-md border border-border bg-background p-3 font-mono text-xs text-foreground outline-none focus:border-primary"
                    />
                  ) : (
                    <div className="md-body min-h-0 flex-1 overflow-y-auto text-xs leading-relaxed text-foreground" dangerouslySetInnerHTML={{ __html: renderMd(content) }} />
                  )}
                </div>
              ) : (
                <div className="flex min-h-0 flex-1 items-center justify-center rounded-lg border border-dashed border-border/50 text-muted-foreground">
                  <div className="text-center">
                    <i className="fa fa-file-o mb-2 text-3xl opacity-40" />
                    <div className="text-sm">选择左侧规范查看</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
