import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import {
	PluginEventPayload,
	PluginEventHandler,
	PluginEventType,
	Notification,
	AddNotificationParams,
	Task,
	TaskQueueStatus,
} from "@/types";

// 导出类型供其他模块使用
export type { PluginEventHandler, PluginEventPayload };

// ==================== 插件操作命令 ====================

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

// ==================== 通知中心命令 ====================

/**
 * 添加通知
 */
export async function addNotification(params: AddNotificationParams): Promise<Notification> {
	return await invoke("add_notification", params);
}

/**
 * 获取所有通知（按更新时间倒序）
 */
export async function getNotifications(): Promise<Notification[]> {
	return await invoke("get_notifications");
}

/**
 * 获取未读通知数量
 */
export async function getUnreadCount(): Promise<number> {
	return await invoke("get_unread_count");
}

/**
 * 标记通知为已读
 */
export async function markNotificationRead(id: string): Promise<boolean> {
	return await invoke("mark_notification_read", { id });
}

/**
 * 标记所有通知为已读
 */
export async function markAllNotificationsRead(): Promise<void> {
	return await invoke("mark_all_notifications_read");
}

/**
 * 更新通知消息（用于进度更新）
 */
export async function updateNotification(id: string, message: string): Promise<boolean> {
	return await invoke("update_notification", { id, message });
}

/**
 * 删除通知
 */
export async function deleteNotification(id: string): Promise<boolean> {
	return await invoke("delete_notification", { id });
}

/**
 * 清空所有通知
 */
export async function clearAllNotifications(): Promise<void> {
	return await invoke("clear_all_notifications");
}

// ==================== 任务队列命令 ====================

/**
 * 获取所有任务（包括队列中、运行中、已完成的）
 */
export async function getTasks(): Promise<Task[]> {
	return await invoke("get_tasks");
}

/**
 * 获取任务队列状态
 */
export async function getTaskStatus(): Promise<TaskQueueStatus> {
	return await invoke("get_task_status");
}

/**
 * 监听任务更新事件
 */
export async function listenToTaskUpdates(
	handler: (task: Task) => void,
): Promise<UnlistenFn> {
	return await listen<Task>("task-updated", (event) => {
		handler(event.payload);
	});
}

