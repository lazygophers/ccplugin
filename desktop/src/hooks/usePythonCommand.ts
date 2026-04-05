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

  /**
   * 通用命令执行器，统一处理状态管理和错误处理
   */
  const executeCommand = useCallback(
    async (
      commandFn: () => Promise<CommandResult>,
      defaultErrorMessage: string
    ) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setProgress(null);

      try {
        const res = await commandFn();
        setResult(res);

        if (!res.success) {
          setError(res.stderr || defaultErrorMessage);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const install = useCallback(async (pluginName: string, marketplace: string = "ccplugin-market") => {
    await executeCommand(
      () => PluginService.install(pluginName, marketplace, setProgress),
      "安装失败"
    );
  }, [executeCommand, setProgress]);

  const update = useCallback(async (pluginName: string) => {
    await executeCommand(
      () => PluginService.update(pluginName, setProgress),
      "更新失败"
    );
  }, [executeCommand, setProgress]);

  const uninstall = useCallback(async (pluginName: string) => {
    await executeCommand(
      () => PluginService.uninstall(pluginName, setProgress),
      "卸载失败"
    );
  }, [executeCommand, setProgress]);

  const clean = useCallback(async () => {
    await executeCommand(
      () => PluginService.clean(),
      "清理失败"
    );
  }, [executeCommand]);

  const getInfo = useCallback(async (pluginName: string) => {
    await executeCommand(
      () => PluginService.getInfo(pluginName),
      "获取信息失败"
    );
  }, [executeCommand]);

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
