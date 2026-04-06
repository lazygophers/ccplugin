import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePlugins } from "@/hooks/usePlugins";
import { usePythonCommand } from "@/hooks/usePythonCommand";
import { PluginCard } from "@/components/PluginCard";
import { PluginDetailDialog } from "@/components/PluginDetailDialog";
import { Search, Filter, RefreshCw, Loader2, Sparkles } from "lucide-react";
import type { PluginInfo } from "@/types";

const installedFilters: Array<{
  value: "all" | "installed" | "uninstalled";
  label: string;
}> = [
  { value: "all", label: "全部" },
  { value: "installed", label: "已安装" },
  { value: "uninstalled", label: "未安装" },
];

export default function Plugins() {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    plugins,
    loading,
    error,
    searchQuery,
    selectedKeyword,
    installedFilter,
    setSearchQuery,
    setSelectedKeyword,
    setInstalledFilter,
    refresh,
    filteredPlugins,
    allKeywords,
  } = usePlugins();

  const { install, update, uninstall, progress } = usePythonCommand();
  const [installingPlugin, setInstallingPlugin] = useState<string | null>(null);
  const [updatingPlugin, setUpdatingPlugin] = useState<string | null>(null);
  const [uninstallingPlugin, setUninstallingPlugin] = useState<string | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginInfo | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [keywordsExpanded, setKeywordsExpanded] = useState(false);

  const qParam = useMemo(() => searchParams.get("q") ?? "", [searchParams]);
  const keywordParam = useMemo(
    () => searchParams.get("keyword") ?? "all",
    [searchParams]
  );

  const updateParams = (next: { q?: string; keyword?: string }) => {
    const params = new URLSearchParams(searchParams);
    if (typeof next.q === "string") {
      const v = next.q.trim();
      if (v) params.set("q", v);
      else params.delete("q");
    }
    if (typeof next.keyword === "string") {
      if (next.keyword && next.keyword !== "all") params.set("keyword", next.keyword);
      else params.delete("keyword");
    }
    setSearchParams(params, { replace: true });
  };

  useEffect(() => {
    if (qParam !== searchQuery) setSearchQuery(qParam);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qParam]);

  useEffect(() => {
    if (keywordParam !== "all") {
      setSelectedKeyword(keywordParam);
    } else {
      setSelectedKeyword(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keywordParam]);

  // 刷新快捷键支持
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // macOS: Cmd+R, Windows/Linux: Ctrl+R 或 F5
      const isRefreshKey =
        (event.metaKey && event.key === "r") || // Cmd+R (macOS)
        (event.ctrlKey && event.key === "r") || // Ctrl+R (Windows/Linux)
        event.key === "F5"; // F5 (所有平台)

      if (isRefreshKey) {
        event.preventDefault();
        refresh();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh]);

  const handleInstall = async (pluginName: string) => {
    setInstallingPlugin(pluginName);
    try {
      await install(pluginName);
      await refresh();
    } finally {
      setInstallingPlugin(null);
    }
  };

  const handleUpdate = async (pluginName: string) => {
    setUpdatingPlugin(pluginName);
    try {
      await update(pluginName);
      await refresh();
    } finally {
      setUpdatingPlugin(null);
    }
  };

  const handleUninstall = async (pluginName: string) => {
    const ok = window.confirm(`确认卸载插件「${pluginName}」？`);
    if (!ok) return;

    setUninstallingPlugin(pluginName);
    try {
      await uninstall(pluginName);
      await refresh();
    } finally {
      setUninstallingPlugin(null);
    }
  };

  const handleViewDetails = (plugin: PluginInfo) => {
    setSelectedPlugin(plugin);
    setDetailDialogOpen(true);
  };

  const installedCount = useMemo(
    () => plugins.filter((p) => p.installed).length,
    [plugins]
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <Sparkles className="w-7 h-7 text-primary" />
            插件
          </h1>
          <p className="text-muted-foreground">
            共 {plugins.length} 个插件，{installedCount} 个已安装
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refresh}
          disabled={loading}
          aria-label="刷新插件列表"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="搜索插件名称、描述或关键词..."
            value={searchQuery}
            onChange={(e) => {
              const v = e.target.value;
              setSearchQuery(v);
              updateParams({ q: v });
            }}
            className="w-full pl-10 pr-4 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="搜索插件"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <div className="flex gap-2 flex-wrap">
            {installedFilters.map((f) => (
              <Badge
                key={f.value}
                variant={installedFilter === f.value ? "default" : "outline"}
                className="cursor-pointer hover:bg-accent"
                onClick={() => setInstalledFilter(f.value)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setInstalledFilter(f.value);
                  }
                }}
              >
                {f.label}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {allKeywords.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <div className="flex gap-2 flex-wrap">
            <Badge
              variant={selectedKeyword === null ? "default" : "outline"}
              className="cursor-pointer hover:bg-accent"
              onClick={() => {
                setSelectedKeyword(null);
                updateParams({ keyword: "all" });
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSelectedKeyword(null);
                  updateParams({ keyword: "all" });
                }
              }}
            >
              全部
            </Badge>
            {(keywordsExpanded ? allKeywords : allKeywords.slice(0, 5)).map(({ keyword, count }) => (
              <Badge
                key={keyword}
                variant={selectedKeyword === keyword ? "default" : "outline"}
                className="cursor-pointer hover:bg-accent"
                onClick={() => {
                  setSelectedKeyword(keyword);
                  updateParams({ keyword });
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelectedKeyword(keyword);
                    updateParams({ keyword });
                  }
                }}
              >
                {keyword} ({count})
              </Badge>
            ))}
            {allKeywords.length > 5 && (
              <Badge
                variant="outline"
                className="cursor-pointer hover:bg-accent text-muted-foreground"
                onClick={() => setKeywordsExpanded(!keywordsExpanded)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setKeywordsExpanded(!keywordsExpanded);
                  }
                }}
              >
                {keywordsExpanded ? "收起" : `+${allKeywords.length - 5}`}
              </Badge>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">加载插件列表...</span>
        </div>
      )}

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
          <p className="font-semibold">加载失败</p>
          <p className="text-sm mt-1">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={refresh}>
            重试
          </Button>
        </div>
      )}

      {!loading && !error && (
        <>
          {filteredPlugins.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>未找到匹配的插件</p>
              {(searchQuery || installedFilter !== "all" || selectedKeyword) && (
                <Button
                  variant="link"
                  size="sm"
                  className="mt-2"
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedKeyword(null);
                    setInstalledFilter("all");
                    updateParams({ q: "", keyword: "all" });
                  }}
                >
                  清除筛选
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPlugins.map((plugin) => (
                <PluginCard
                  key={plugin.name}
                  plugin={plugin}
                  onInstall={handleInstall}
                  onUpdate={handleUpdate}
                  onUninstall={handleUninstall}
                  onViewDetails={handleViewDetails}
                  installing={installingPlugin === plugin.name}
                  updating={updatingPlugin === plugin.name}
                  uninstalling={uninstallingPlugin === plugin.name}
                />
              ))}
            </div>
          )}
        </>
      )}

      {progress && (installingPlugin || uninstallingPlugin) && (
        <div
          className="fixed bottom-6 right-6 w-96 p-4 bg-card border rounded-lg shadow-lg"
          aria-live="polite"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">{progress.plugin_name}</span>
            <span className="text-sm text-muted-foreground">
              {progress.progress}%
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 mb-2">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground">{progress.message}</p>
        </div>
      )}

      <PluginDetailDialog
        plugin={selectedPlugin}
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        onInstall={handleInstall}
        onUpdate={handleUpdate}
        onUninstall={handleUninstall}
        installing={installingPlugin === selectedPlugin?.name}
        updating={updatingPlugin === selectedPlugin?.name}
        uninstalling={uninstallingPlugin === selectedPlugin?.name}
      />
    </div>
  );
}
