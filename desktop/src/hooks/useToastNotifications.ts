import { useEffect } from "react";
import { toast } from "sonner";
import { listenToPluginEvents } from "@/services/tauri-commands";

/**
 * Toast 通知 Hook
 * 监听插件事件并自动显示应用内 Toast 通知（右下角）
 * 显示开始、进度、完成、失败等各种状态
 */
export function useToastNotifications() {
	useEffect(() => {
		let unlisten: (() => void) | null = null;

		const setupListener = async () => {
			unlisten = await listenToPluginEvents((event) => {
				handlePluginEvent(event);
			});
		};

		setupListener();

		return () => {
			unlisten?.();
		};
	}, []);
}

/**
 * 处理插件事件并显示对应的 Toast
 */
function handlePluginEvent(event: {
	event_type: string;
	plugin_name: string;
	data: unknown;
}) {
	const { event_type, plugin_name, data } = event;

	// 使用统一的 Toast ID，用于更新同一操作的 Toast
	const toastId = `${plugin_name}`;

	// 开始事件 - 显示加载中 Toast
	if (event_type.endsWith("-started")) {
		const action = getActionLabel(event_type);
		toast.loading(`${action} ${plugin_name}...`, {
			id: toastId,
		});
		return;
	}

	// 进度事件 - 更新进度
	if (event_type.endsWith("-progress")) {
		const progress = (data as { progress?: number })?.progress || 0;
		const message = (data as { message?: string })?.message || "处理中...";
		toast.loading(`${message} (${progress}%)`, {
			id: toastId,
		});
		return;
	}

	// 完成事件 - 显示成功 Toast
	if (event_type.endsWith("-completed")) {
		const action = getActionLabel(event_type);
		toast.success(`${plugin_name} ${action}成功`, {
			id: toastId,
		});
		return;
	}

	// 失败事件 - 显示错误 Toast
	if (event_type.endsWith("-failed")) {
		const error = (data as { error?: string })?.error || "未知错误";
		toast.error(`${plugin_name} 操作失败: ${error}`, {
			id: toastId,
		});
		return;
	}
}

/**
 * 从事件类型获取操作标签
 */
function getActionLabel(eventType: string): string {
	if (eventType.includes("install")) return "安装";
	if (eventType.includes("update")) return "更新";
	if (eventType.includes("uninstall")) return "卸载";
	if (eventType.includes("marketplace")) return "更新市场";
	if (eventType.includes("cache")) return "清理缓存";
	return "处理";
}
