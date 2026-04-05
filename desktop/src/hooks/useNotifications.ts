import { useState, useEffect, useCallback, useRef } from "react";
import { type Notification, type NotificationType, type AddNotificationParams } from "@/types";
import {
	getNotifications,
	addNotification,
	markNotificationRead,
	markAllNotificationsRead,
	updateNotification,
	deleteNotification,
	clearAllNotifications,
	getUnreadCount,
} from "@/services/tauri-commands";

/**
 * 通知中心 Hook
 */
export function useNotifications(autoRefresh: boolean = true) {
	const [notifications, setNotifications] = useState<Notification[]>([]);
	const [unreadCount, setUnreadCount] = useState<number>(0);
	const [loading, setLoading] = useState<boolean>(false);
	const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

	/**
	 * 加载通知列表
	 */
	const loadNotifications = useCallback(async () => {
		setLoading(true);
		try {
			const [notifs, count] = await Promise.all([
				getNotifications(),
				getUnreadCount(),
			]);
			setNotifications(notifs);
			setUnreadCount(count);
		} catch (error) {
			console.error("Failed to load notifications:", error);
		} finally {
			setLoading(false);
		}
	}, []);

	/**
	 * 添加通知
	 */
	const addNotif = useCallback(async (params: AddNotificationParams) => {
		try {
			const newNotif = await addNotification(params);
			setNotifications((prev) => {
				const updated = [newNotif, ...prev];
				return updated.sort((a, b) => b.updated_at - a.updated_at);
			});
			setUnreadCount((prev) => prev + 1);
			return newNotif;
		} catch (error) {
			console.error("Failed to add notification:", error);
			throw error;
		}
	}, []);

	/**
	 * 标记为已读
	 */
	const markAsRead = useCallback(async (id: string) => {
		try {
			const success = await markNotificationRead(id);
			if (success) {
				setNotifications((prev) =>
					prev.map((n) =>
						n.id === id ? { ...n, read: true } : n
					)
				);
				setUnreadCount((prev) => Math.max(0, prev - 1));
			}
			return success;
		} catch (error) {
			console.error("Failed to mark as read:", error);
			return false;
		}
	}, []);

	/**
	 * 标记所有为已读
	 */
	const markAllAsRead = useCallback(async () => {
		try {
			await markAllNotificationsRead();
			setNotifications((prev) =>
				prev.map((n) => ({ ...n, read: true }))
			);
			setUnreadCount(0);
		} catch (error) {
			console.error("Failed to mark all as read:", error);
		}
	}, []);

	/**
	 * 更新通知（用于进度更新）
	 */
	const updateNotif = useCallback(async (id: string, message: string) => {
		try {
			const success = await updateNotification(id, message);
			if (success) {
				setNotifications((prev) => {
					const updated = prev.map((n) =>
						n.id === id ? { ...n, message, updated_at: Date.now() / 1000 } : n
					);
					return updated.sort((a, b) => b.updated_at - a.updated_at);
				});
			}
			return success;
		} catch (error) {
			console.error("Failed to update notification:", error);
			return false;
		}
	}, []);

	/**
	 * 删除通知
	 */
	const deleteNotif = useCallback(async (id: string) => {
		try {
			const success = await deleteNotification(id);
			if (success) {
				setNotifications((prev) => prev.filter((n) => n.id !== id));
				setUnreadCount((prev) => {
					const notif = notifications.find((n) => n.id === id);
					return notif && !notif.read ? Math.max(0, prev - 1) : prev;
				});
			}
			return success;
		} catch (error) {
			console.error("Failed to delete notification:", error);
			return false;
		}
	}, [notifications]);

	/**
	 * 清空所有通知
	 */
	const clearAll = useCallback(async () => {
		try {
			await clearAllNotifications();
			setNotifications([]);
			setUnreadCount(0);
		} catch (error) {
			console.error("Failed to clear all notifications:", error);
		}
	}, []);

	/**
	 * 快捷方法：添加各种类型的通知
	 */
	const notify = useCallback((
		type: NotificationType,
		title: string,
		message: string,
		metadata?: AddNotificationParams["metadata"]
	) => {
		return addNotif({ type, title, message, metadata });
	}, [addNotif]);

	const info = useCallback((title: string, message: string) => {
		return notify("info", title, message);
	}, [notify]);

	const success = useCallback((title: string, message: string) => {
		return notify("success", title, message);
	}, [notify]);

	const warning = useCallback((title: string, message: string) => {
		return notify("warning", title, message);
	}, [notify]);

	const error = useCallback((title: string, message: string) => {
		return notify("error", title, message);
	}, [notify]);

	// 初始加载
	useEffect(() => {
		loadNotifications();
	}, [loadNotifications]);

	// 自动刷新（每 5 秒）
	useEffect(() => {
		if (!autoRefresh) return;

		refreshTimerRef.current = setInterval(() => {
			loadNotifications();
		}, 5000);

		return () => {
			if (refreshTimerRef.current) {
				clearInterval(refreshTimerRef.current);
			}
		};
	}, [autoRefresh, loadNotifications]);

	return {
		notifications,
		unreadCount,
		loading,
		loadNotifications,
		addNotification: addNotif,
		markAsRead,
		markAllAsRead,
		updateNotification: updateNotif,
		deleteNotification: deleteNotif,
		clearAll,
		// 快捷方法
		notify,
		info,
		success,
		warning,
		error,
	};
}
