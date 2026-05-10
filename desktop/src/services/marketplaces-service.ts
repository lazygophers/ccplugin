import { invoke } from "@tauri-apps/api/core";
import type { UnlistenFn } from "@tauri-apps/api/event";
import {
	listenToPluginEvents,
	type PluginEventPayload,
} from "@/services/tauri-commands";

export interface MarketplaceInfo {
	name: string;
	source?: string;
	url?: string;
	installLocation?: string;
	update_command?: string | null; // 后端提供的更新命令
}

/** Marketplace 更新事件类型集合 */
const MARKETPLACE_UPDATE_EVENTS = new Set([
	"marketplace-update-started",
	"marketplace-update-progress",
	"marketplace-update-completed",
	"marketplace-update-failed",
]);

export class MarketplacesService {
	static async list(): Promise<MarketplaceInfo[]> {
		return await invoke<MarketplaceInfo[]>("get_marketplaces");
	}

	/**
	 * 触发 marketplace 更新（fire-and-forget）。
	 *
	 * 立即返回 task_id；实际执行在后台进行，进度/完成/失败通过
	 * `marketplace-update-*` 事件通知。订阅事件请使用 `onUpdateEvent`。
	 */
	static async update(marketplaceName: string): Promise<string> {
		return await invoke<string>("update_marketplace", { marketplaceName });
	}

	/**
	 * 订阅所有 marketplace 更新事件。
	 *
	 * @param handler 事件回调，event_type 在 `MARKETPLACE_UPDATE_EVENTS` 之中
	 * @returns 取消订阅函数
	 */
	static async onUpdateEvent(
		handler: (event: PluginEventPayload) => void,
	): Promise<UnlistenFn> {
		return await listenToPluginEvents((event) => {
			if (MARKETPLACE_UPDATE_EVENTS.has(event.event_type)) {
				handler(event);
			}
		});
	}
}
