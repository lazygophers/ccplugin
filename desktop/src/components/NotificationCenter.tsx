import { useState } from "react";
import {
	Bell,
	X,
	Check,
	Trash2,
	Info,
	CheckCircle,
	AlertTriangle,
	XCircle,
	Loader,
} from "lucide-react";
import { useNotifications } from "@/hooks/useNotifications";
import { type NotificationType } from "@/types";

/**
 * 通知类型对应的图标
 */
function getNotificationIcon(type: NotificationType) {
	switch (type) {
		case "info":
			return <Info className="w-5 h-5 text-blue-500" />;
		case "success":
			return <CheckCircle className="w-5 h-5 text-green-500" />;
		case "warning":
			return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
		case "error":
			return <XCircle className="w-5 h-5 text-red-500" />;
		case "progress":
			return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
	}
}

/**
 * 通知类型对应的样式类
 */
function getNotificationStyle(type: NotificationType): string {
	switch (type) {
		case "info":
			return "border-l-blue-500 bg-blue-50 dark:bg-blue-950";
		case "success":
			return "border-l-green-500 bg-green-50 dark:bg-green-950";
		case "warning":
			return "border-l-yellow-500 bg-yellow-50 dark:bg-yellow-950";
		case "error":
			return "border-l-red-500 bg-red-50 dark:bg-red-950";
		case "progress":
			return "border-l-blue-500 bg-blue-50 dark:bg-blue-950";
	}
}

/**
 * 格式化时间戳
 */
function formatTime(timestamp: number): string {
	const date = new Date(timestamp * 1000);
	const now = new Date();
	const diff = now.getTime() - date.getTime();

	// 小于 1 分钟
	if (diff < 60000) {
		return "刚刚";
	}
	// 小于 1 小时
	if (diff < 3600000) {
		const minutes = Math.floor(diff / 60000);
		return `${minutes} 分钟前`;
	}
	// 小于 1 天
	if (diff < 86400000) {
		const hours = Math.floor(diff / 3600000);
		return `${hours} 小时前`;
	}
	// 小于 7 天
	if (diff < 604800000) {
		const days = Math.floor(diff / 86400000);
		return `${days} 天前`;
	}
	// 显示日期
	return date.toLocaleDateString("zh-CN");
}

interface NotificationCenterProps {
	onClose?: () => void;
}

export function NotificationCenter({ onClose }: NotificationCenterProps) {
	const {
		notifications,
		unreadCount,
		loading,
		markAsRead,
		markAllAsRead,
		deleteNotification,
		clearAll,
	} = useNotifications();

	return (
		<div className="relative">
			{/* 通知按钮 */}
			<button
				onClick={onClose}
				className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
			>
				<Bell className="w-5 h-5" />
				{unreadCount > 0 && (
					<span className="absolute top-1 right-1 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
						{unreadCount > 99 ? "99+" : unreadCount}
					</span>
				)}
			</button>

			{/* 通知面板 */}
			{onClose && (
				<div className="fixed inset-0 z-50" onClick={onClose}>
					<div
						className="absolute right-4 top-16 w-96 max-h-[600px] bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col"
						onClick={(e) => e.stopPropagation()}
					>
						{/* 头部 */}
						<div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
							<h3 className="text-lg font-semibold">通知中心</h3>
							<div className="flex items-center gap-2">
								{unreadCount > 0 && (
									<button
										onClick={() => markAllAsRead()}
										className="text-sm text-blue-500 hover:text-blue-600"
									>
										全部已读
									</button>
								)}
								{notifications.length > 0 && (
									<button
										onClick={() => clearAll()}
										className="text-sm text-red-500 hover:text-red-600"
									>
										清空
									</button>
								)}
								<button
									onClick={onClose}
									className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
								>
									<X className="w-5 h-5" />
								</button>
							</div>
						</div>

						{/* 通知列表 */}
						<div className="flex-1 overflow-y-auto">
							{loading ? (
								<div className="flex items-center justify-center p-8">
									<Loader className="w-6 h-6 animate-spin text-gray-400" />
								</div>
							) : notifications.length === 0 ? (
								<div className="flex flex-col items-center justify-center p-8 text-gray-400">
									<Bell className="w-12 h-12 mb-2" />
									<p>暂无通知</p>
								</div>
							) : (
								<div className="divide-y divide-gray-200 dark:divide-gray-700">
									{notifications.map((notification) => (
										<NotificationItem
											key={notification.id}
											notification={notification}
											onMarkRead={() => markAsRead(notification.id)}
											onDelete={() => deleteNotification(notification.id)}
										/>
									))}
								</div>
							)}
						</div>
					</div>
				</div>
			)}
		</div>
	);
}

interface NotificationItemProps {
	notification: import("@/types").Notification;
	onMarkRead: () => void;
	onDelete: () => void;
}

function NotificationItem({ notification, onMarkRead, onDelete }: NotificationItemProps) {
	const [isHovered, setIsHovered] = useState(false);

	return (
		<div
			className={`p-4 border-l-4 ${getNotificationStyle(notification.type)} ${
				!notification.read ? "bg-opacity-50" : ""
			}`}
			onMouseEnter={() => setIsHovered(true)}
			onMouseLeave={() => setIsHovered(false)}
		>
			<div className="flex items-start gap-3">
				{/* 图标 */}
				<div className="flex-shrink-0 mt-0.5">
					{getNotificationIcon(notification.type)}
				</div>

				{/* 内容 */}
				<div className="flex-1 min-w-0">
					<div className="flex items-center justify-between gap-2">
						<h4 className="font-semibold text-sm truncate">
							{notification.title}
						</h4>
						<span className="text-xs text-gray-500 flex-shrink-0">
							{formatTime(notification.updated_at)}
						</span>
					</div>
					<p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
						{notification.message}
					</p>
				</div>

				{/* 操作按钮 */}
				{isHovered && (
					<div className="flex items-center gap-1 flex-shrink-0">
						{!notification.read && (
							<button
								onClick={onMarkRead}
								className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
								title="标记为已读"
							>
								<Check className="w-4 h-4 text-gray-500" />
							</button>
						)}
						<button
							onClick={onDelete}
							className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900"
							title="删除"
						>
							<Trash2 className="w-4 h-4 text-red-500" />
						</button>
					</div>
				)}
			</div>
		</div>
	);
}
