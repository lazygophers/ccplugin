import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { PluginEventPayload, PluginEventHandler, PluginEventType } from "@/types";

// 导出类型供其他模块使用
export type { PluginEventHandler, PluginEventPayload };

/**
 * 安装插件（立即返回，通过事件获取进度）
 */
export async function installPlugin(
	pluginName: string,
	marketplace: string = "ccplugin-market",
	scope: "user" | "project" | "local" = "user",
): Promise<void> {
	return await invoke("install_plugin", {
		pluginName,
		marketplace,
		scope,
	});
}

/**
 * 更新插件（立即返回，通过事件获取进度）
 */
export async function updatePlugin(pluginName: string): Promise<void> {
	return await invoke("update_plugin", {
		pluginName,
	});
}

/**
 * 卸载插件（立即返回，通过事件获取进度）
 */
export async function uninstallPlugin(
	pluginName: string,
): Promise<void> {
	return await invoke("uninstall_plugin", {
		pluginName,
	});
}

/**
 * 清理缓存（立即返回，通过事件获取完成状态）
 */
export async function cleanCache(): Promise<void> {
	return await invoke("clean_cache");
}

/**
 * 获取插件信息（立即返回，通过事件获取结果）
 */
export async function getPluginInfo(
	pluginName: string,
): Promise<void> {
	return await invoke("get_plugin_info", {
		pluginName,
	});
}

/**
 * 监听所有插件事件
 * @param eventFilter - 可选的事件类型过滤器
 * @param handler - 事件处理器
 * @returns 取消监听的函数
 */
export async function listenToPluginEvents(
	handler: PluginEventHandler,
	eventFilter?: PluginEventType,
): Promise<UnlistenFn> {
	const unlisten = await listen<PluginEventPayload>("plugin-event", (event) => {
		// 如果指定了事件过滤器，只处理匹配的事件
		if (eventFilter && event.payload.event_type !== eventFilter) {
			return;
		}
		handler(event.payload);
	});

	return unlisten;
}

/**
 * 监听特定插件的事件
 * @param pluginName - 插件名称
 * @param handler - 事件处理器
 * @param eventFilter - 可选的事件类型过滤器
 * @returns 取消监听的函数
 */
export async function listenToPluginEventsByName(
	pluginName: string,
	handler: PluginEventHandler,
	eventFilter?: PluginEventType,
): Promise<UnlistenFn> {
	const unlisten = await listenToPluginEvents((event) => {
		// 只处理指定插件的事件
		if (event.plugin_name === pluginName) {
			handler(event);
		}
	}, eventFilter);

	return unlisten;
}

/**
 * 监听插件安装进度（兼容旧代码）
 * @deprecated 使用 listenToPluginEvents 代替
 */
export async function listenToInstallProgress(
	callback: (progress: { plugin_name: string; status: string; progress: number; message: string }) => void,
): Promise<UnlistenFn> {
	return await listenToPluginEvents((event) => {
		if (event.event_type === "plugin-install-progress") {
			const data = event.data as {
				status: string;
				progress: number;
				message: string;
			};
			callback({
				plugin_name: event.plugin_name,
				...data,
			});
		}
	});
}
