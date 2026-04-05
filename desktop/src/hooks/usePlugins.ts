import { useState, useEffect, useCallback } from "react";
import { MarketplaceService } from "@/services/marketplace-service";
import { PluginInfo } from "@/types";

interface UsePluginsResult {
  plugins: PluginInfo[];
  loading: boolean;
  error: string | null;
  searchQuery: string;
  selectedCategory: string;
  selectedKeyword: string | null;
  installedFilter: "all" | "installed" | "uninstalled";
  setSearchQuery: (query: string) => void;
  setSelectedCategory: (category: string) => void;
  setSelectedKeyword: (keyword: string | null) => void;
  setInstalledFilter: (filter: "all" | "installed" | "uninstalled") => void;
  refresh: () => Promise<void>;
  filteredPlugins: PluginInfo[];
}

export function usePlugins(): UsePluginsResult {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
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

  // 客户端过滤（也可以调用后端API）
  const filteredPlugins = (plugins ?? []).filter((plugin) => {
    if (installedFilter === "installed" && !plugin.installed) {
      return false;
    }
    if (installedFilter === "uninstalled" && plugin.installed) {
      return false;
    }

    // 分类过滤（保留兼容性）
    if (selectedCategory !== "all" && plugin.category !== selectedCategory) {
      return false;
    }

    // keyword 过滤（优先于 category）
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
    selectedCategory,
    selectedKeyword,
    installedFilter,
    setSearchQuery,
    setSelectedCategory,
    setSelectedKeyword,
    setInstalledFilter,
    refresh: loadPlugins,
    filteredPlugins,
  };
}
