import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { CommandResult, PluginInstallProgress } from "@/types";

/**
 * 安装插件
 */
export async function installPlugin(
	pluginName: string,
	marketplace: string = "ccplugin-market",
	scope: "user" | "project" | "local" = "user",
): Promise<CommandResult> {
	return await invoke<CommandResult>("install_plugin", {
		pluginName,
		marketplace,
		scope,
	});
}

/**
 * 更新插件
 */
export async function updatePlugin(pluginName: string): Promise<CommandResult> {
	return await invoke<CommandResult>("update_plugin", {
		pluginName,
	});
}

/**
 * 卸载插件
 */
export async function uninstallPlugin(
	pluginName: string,
): Promise<CommandResult> {
	return await invoke<CommandResult>("uninstall_plugin", {
		pluginName,
	});
}

/**
 * 清理缓存
 */
export async function cleanCache(): Promise<CommandResult> {
	return await invoke<CommandResult>("clean_cache");
}

/**
 * 获取插件信息
 */
export async function getPluginInfo(
	pluginName: string,
): Promise<CommandResult> {
	return await invoke<CommandResult>("get_plugin_info", {
		pluginName,
	});
}

/**
 * 监听插件安装进度
 */
export async function listenToInstallProgress(
	callback: (progress: PluginInstallProgress) => void,
): Promise<UnlistenFn> {
	return await listen<PluginInstallProgress>(
		"plugin-install-progress",
		(event) => {
			callback(event.payload);
		},
	);
}
