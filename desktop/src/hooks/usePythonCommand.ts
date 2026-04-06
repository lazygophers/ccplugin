import { useState, useCallback, useRef } from "react";
import { PluginService } from "@/services/plugin-service";
import type { PluginEventPayload } from "@/types";

interface UsePythonCommandResult {
	loading: boolean;
	progress: { plugin_name: string; status: string; progress: number; message: string } | null;
	error: string | null;
	install: (pluginName: string, marketplace?: string) => Promise<void>;
	update: (pluginName: string, marketplace?: string, scope?: string, workingDir?: string) => Promise<void>;
	uninstall: (pluginName: string) => Promise<void>;
	clean: () => Promise<void>;
	getInfo: (pluginName: string) => Promise<void>;
}

export function usePythonCommand(): UsePythonCommandResult {
	const [loading, setLoading] = useState(false);
	const [progress, setProgress] = useState<{
		plugin_name: string;
		status: string;
		progress: number;
		message: string;
	} | null>(null);
	const [error, setError] = useState<string | null>(null);

	// 用于跟踪当前操作的插件名称
	const currentPluginRef = useRef<string | null>(null);

	/**
	 * 事件处理器 - 从事件中提取状态并更新
	 */
	const handleEvent = useCallback((event: PluginEventPayload) => {
		const { event_type, plugin_name, data } = event;

		switch (event_type) {
			case "plugin-install-started":
			case "plugin-update-started":
			case "plugin-uninstall-started":
			case "cache-clean-started":
				setLoading(true);
				setError(null);
				setProgress(null);
				break;

			case "plugin-install-progress":
			case "plugin-update-progress":
			case "plugin-uninstall-progress":
				setProgress({
					plugin_name,
					status: (data as { status: string }).status,
					progress: (data as { progress: number }).progress,
					message: (data as { message: string }).message,
				});
				break;

			case "plugin-install-completed":
			case "plugin-update-completed":
			case "plugin-uninstall-completed":
			case "cache-clean-completed":
				setLoading(false);
				setProgress(null);
				setError(null);
				break;

			case "plugin-install-failed":
			case "plugin-update-failed":
			case "plugin-uninstall-failed":
			case "cache-clean-failed":
			case "plugin-info-failed":
				setLoading(false);
				setProgress(null);
				const errorData = data as { error?: string };
				setError(errorData.error || "操作失败");
				break;
		}
	}, []);

	const install = useCallback(
		async (pluginName: string, marketplace: string = "ccplugin-market") => {
			currentPluginRef.current = pluginName;
			await PluginService.install(pluginName, marketplace, handleEvent);
		},
		[handleEvent]
	);

	const update = useCallback(
		async (pluginName: string, marketplace?: string, scope?: string, workingDir?: string) => {
			currentPluginRef.current = pluginName;
			await PluginService.update(pluginName, marketplace, scope, workingDir, handleEvent);
		},
		[handleEvent]
	);

	const uninstall = useCallback(
		async (pluginName: string) => {
			currentPluginRef.current = pluginName;
			await PluginService.uninstall(pluginName, handleEvent);
		},
		[handleEvent]
	);

	const clean = useCallback(async () => {
		setLoading(true);
		setError(null);
		await PluginService.clean(handleEvent);
	}, [handleEvent]);

	const getInfo = useCallback(
		async (pluginName: string) => {
			currentPluginRef.current = pluginName;
			await PluginService.getInfo(pluginName, handleEvent);
		},
		[handleEvent]
	);

	return {
		loading,
		progress,
		error,
		install,
		update,
		uninstall,
		clean,
		getInfo,
	};
}
