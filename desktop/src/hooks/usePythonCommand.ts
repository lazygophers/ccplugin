import { useState, useCallback } from "react";
import { PluginService } from "@/services/plugin-service";
import { CommandResult, PluginInstallProgress } from "@/types";

interface UsePythonCommandResult {
  loading: boolean;
  progress: PluginInstallProgress | null;
  result: CommandResult | null;
  error: string | null;
  install: (pluginName: string, marketplace?: string) => Promise<void>;
  update: (pluginName: string) => Promise<void>;
  uninstall: (pluginName: string) => Promise<void>;
  clean: () => Promise<void>;
  getInfo: (pluginName: string) => Promise<void>;
}

export function usePythonCommand(): UsePythonCommandResult {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<PluginInstallProgress | null>(null);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const install = useCallback(async (pluginName: string, marketplace: string = "ccplugin-market") => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      const res = await PluginService.install(pluginName, marketplace, (prog) => {
        setProgress(prog);
      });

      setResult(res);

      if (!res.success) {
        setError(res.stderr || "安装失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const update = useCallback(async (pluginName: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      const res = await PluginService.update(pluginName, (prog) => {
        setProgress(prog);
      });

      setResult(res);

      if (!res.success) {
        setError(res.stderr || "更新失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const uninstall = useCallback(async (pluginName: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      const res = await PluginService.uninstall(pluginName, (prog) => {
        setProgress(prog);
      });

      setResult(res);

      if (!res.success) {
        setError(res.stderr || "卸载失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const clean = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      const res = await PluginService.clean();
      setResult(res);

      if (!res.success) {
        setError(res.stderr || "清理失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const getInfo = useCallback(async (pluginName: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(null);

    try {
      const res = await PluginService.getInfo(pluginName);
      setResult(res);

      if (!res.success) {
        setError(res.stderr || "获取信息失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    progress,
    result,
    error,
    install,
    update,
    uninstall,
    clean,
    getInfo,
  };
}
