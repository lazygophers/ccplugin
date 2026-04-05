import { useState, useEffect, useCallback } from "react";
import React from "react";
import { MarketplaceService } from "@/services/marketplace-service";
import { PluginInfo } from "@/types";

interface UsePluginsResult {
  plugins: PluginInfo[];
  loading: boolean;
  error: string | null;
  searchQuery: string;
  selectedKeyword: string | null;
  installedFilter: "all" | "installed" | "uninstalled";
  setSearchQuery: (query: string) => void;
  setSelectedKeyword: (keyword: string | null) => void;
  setInstalledFilter: (filter: "all" | "installed" | "uninstalled") => void;
  refresh: () => Promise<void>;
  filteredPlugins: PluginInfo[];
  allKeywords: Array<{ keyword: string; count: number }>;
}

export function usePlugins(): UsePluginsResult {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [installedFilter, setInstalledFilter] = useState<
    "all" | "installed" | "uninstalled"
  >("all");

  const loadPlugins = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await MarketplaceService.getAllPlugins();
      setPlugins(Array.isArray(data) ? data : []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlugins();
  }, [loadPlugins]);

  // 提取所有唯一的 keywords 并计数
  const allKeywords = React.useMemo(() => {
    const keywordMap = new Map<string, number>();
    plugins.forEach((plugin) => {
      plugin.keywords.forEach((keyword) => {
        keywordMap.set(keyword, (keywordMap.get(keyword) ?? 0) + 1);
      });
    });
    return Array.from(keywordMap.entries())
      .map(([keyword, count]) => ({ keyword, count }))
      .sort((a, b) => b.count - a.count); // 按使用频率降序排序
  }, [plugins]);

  // 客户端过滤
  const filteredPlugins = (plugins ?? []).filter((plugin) => {
    if (installedFilter === "installed" && !plugin.installed) {
      return false;
    }
    if (installedFilter === "uninstalled" && plugin.installed) {
      return false;
    }

    // keyword 过滤
    if (selectedKeyword && !plugin.keywords.includes(selectedKeyword)) {
      return false;
    }

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        (plugin.name ?? "").toLowerCase().includes(query) ||
        (plugin.description ?? "").toLowerCase().includes(query) ||
        (plugin.keywords ?? []).some((k) => (k ?? "").toLowerCase().includes(query))
      );
    }

    return true;
  });

  return {
    plugins,
    loading,
    error,
    searchQuery,
    selectedKeyword,
    installedFilter,
    setSearchQuery,
    setSelectedKeyword,
    setInstalledFilter,
    refresh: loadPlugins,
    filteredPlugins,
    allKeywords,
  };
}
