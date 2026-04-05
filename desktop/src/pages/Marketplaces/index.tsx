import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
	Loader2,
	RefreshCw,
	Store,
	Plus,
	Trash2,
	ChevronDown,
	ChevronUp,
	Package,
} from "lucide-react";
import {
	MarketplacesService,
	type MarketplaceInfo,
} from "@/services/marketplaces-service";
import { MarketplaceService } from "@/services/marketplace-service";
import { PluginCardMemo as PluginCard } from "@/components/PluginCard";
import { PluginDetailDialog } from "@/components/PluginDetailDialog";
import { installPlugin, uninstallPlugin } from "@/services/tauri-commands";
import type { PluginInfo } from "@/types";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Marketplaces() {
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [marketplaces, setMarketplaces] = useState<MarketplaceInfo[]>([]);
	const [plugins, setPlugins] = useState<PluginInfo[]>([]);
	const [expandedMarketplace, setExpandedMarketplace] = useState<
		string | null
	>(null);

	// 插件操作状态
	const [installingPlugin, setInstallingPlugin] = useState<string | null>(
		null,
	);
	const [uninstallingPlugin, setUninstallingPlugin] = useState<string | null>(
		null,
	);

	// 详情对话框
	const [detailPlugin, setDetailPlugin] = useState<PluginInfo | null>(null);
	const [detailOpen, setDetailOpen] = useState(false);

	// 添加市场对话框
	const [addDialogOpen, setAddDialogOpen] = useState(false);
	const [newMarketName, setNewMarketName] = useState("");
	const [newMarketUrl, setNewMarketUrl] = useState("");
	const [addingMarket, setAddingMarket] = useState(false);

	// 安装 scope 选择对话框
	const [installDialogOpen, setInstallDialogOpen] = useState(false);
	const [pendingInstallPlugin, setPendingInstallPlugin] = useState<
		string | null
	>(null);
	const [selectedScope, setSelectedScope] = useState<
		"user" | "project" | "local"
	>("user");

	// 市场更新状态
	const [updatingMarketplace, setUpdatingMarketplace] = useState<
		string | null
	>(null);

	const loadPlugins = useCallback(async () => {
		try {
			const data = await MarketplaceService.getAllPlugins();
			setPlugins(data);
		} catch (e) {
			console.error("Failed to load plugins:", e);
		}
	}, []); // 空依赖：这个函数不依赖任何外部变量

	const loadMarketplaces = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await MarketplacesService.list();
			setMarketplaces(Array.isArray(data) ? data : []);
		} catch (e) {
			const msg = e instanceof Error ? e.message : String(e);
			setError(msg);
		} finally {
			setLoading(false);
		}
	}, []); // 空依赖：这个函数不依赖任何外部变量

	// 初始化时加载数据
	useEffect(() => {
		loadMarketplaces();
		loadPlugins();
	}, []); // 空依赖：只在组件挂载时执行一次

	const handleMarketplaceClick = useCallback(
		(marketName: string) => {
			if (expandedMarketplace === marketName) {
				setExpandedMarketplace(null);
			} else {
				setExpandedMarketplace(marketName);
			}
		},
		[expandedMarketplace],
	);

	// 点击安装按钮时打开 scope 选择对话框
	const handleInstallClick = useCallback((pluginName: string) => {
		setPendingInstallPlugin(pluginName);
		setInstallDialogOpen(true);
	}, []);

	// 确认安装（执行实际安装）
	const handleConfirmInstall = useCallback(async () => {
		if (!pendingInstallPlugin) return;

		setInstallingPlugin(pendingInstallPlugin);
		setInstallDialogOpen(false);

		try {
			await installPlugin(
				pendingInstallPlugin,
				expandedMarketplace || "ccplugin-market",
				selectedScope,
			);
			// 使用函数式更新，避免依赖 loadPlugins
			setPlugins(await MarketplaceService.getAllPlugins());
		} catch (e) {
			console.error("Install failed:", e);
			alert(e instanceof Error ? e.message : "安装失败");
		} finally {
			setInstallingPlugin(null);
			setPendingInstallPlugin(null);
		}
	}, [pendingInstallPlugin, expandedMarketplace, selectedScope]);

	const handleUninstall = useCallback(async (pluginName: string) => {
		if (!confirm(`确定要卸载插件 "${pluginName}" 吗？`)) return;

		setUninstallingPlugin(pluginName);
		try {
			await uninstallPlugin(pluginName);
			// 使用函数式更新，避免依赖 loadPlugins
			setPlugins(await MarketplaceService.getAllPlugins());
		} catch (e) {
			console.error("Uninstall failed:", e);
			alert(e instanceof Error ? e.message : "卸载失败");
		} finally {
			setUninstallingPlugin(null);
		}
	}, []); // 空依赖：不需要任何外部变量

	const handleViewDetails = useCallback((plugin: PluginInfo) => {
		setDetailPlugin(plugin);
		setDetailOpen(true);
	}, []);

	const handleAddMarketplace = useCallback(async () => {
		if (!newMarketName.trim() || !newMarketUrl.trim()) {
			alert("请填写市场名称和 URL");
			return;
		}

		setAddingMarket(true);
		try {
			// TODO: 后端需要实现 add_marketplace 命令
			// 暂时使用提示告知用户使用 CLI
			alert(
				`添加市场功能待实现\n\n请使用 Claude CLI:\nclaude plugin marketplace add ${newMarketName} ${newMarketUrl}`,
			);
			setAddDialogOpen(false);
			setNewMarketName("");
			setNewMarketUrl("");
		} catch (e) {
			console.error("Add marketplace failed:", e);
			alert(e instanceof Error ? e.message : "添加市场失败");
		} finally {
			setAddingMarket(false);
		}
	}, [newMarketName, newMarketUrl]);

	const handleRemoveMarketplace = useCallback(async (marketName: string) => {
		if (
			!confirm(
				`确定要删除市场 "${marketName}" 吗？\n\n请使用 Claude CLI:\nclaude plugin marketplace remove ${marketName}`,
			)
		)
			return;
		// TODO: 后端需要实现 remove_marketplace 命令
		alert(
			`删除市场功能待实现\n\n请使用 Claude CLI:\nclaude plugin marketplace remove ${marketName}`,
		);
	}, []);

	const handleUpdateMarketplace = useCallback(
		async (marketName: string) => {
			setUpdatingMarketplace(marketName);
			try {
				const result = await MarketplacesService.update(marketName);
				alert(`市场 "${marketName}" 更新成功！\n\n${result}`);
				// 重新加载数据
				await loadMarketplaces();
				await loadPlugins();
			} catch (e) {
				console.error("Update marketplace failed:", e);
				alert(
					`更新市场失败: ${e instanceof Error ? e.message : String(e)}`,
				);
			} finally {
				setUpdatingMarketplace(null);
			}
		},
		[loadMarketplaces, loadPlugins],
	);

	return (
		<div className="p-6 space-y-6">
			<div className="flex items-center justify-between gap-3">
				<div>
					<h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
						<Store className="w-7 h-7 text-primary" />
						插件市场
					</h1>
					<p className="text-muted-foreground">
						共 {marketplaces.length} 个市场已配置
						{expandedMarketplace &&
							` • ${expandedMarketplace} 的插件`}
					</p>
				</div>
				<div className="flex items-center gap-2">
					<Link to="/marketplaces/plugins">
						<Button
							variant="outline"
							size="sm"
							aria-label="查看所有插件"
						>
							<Package className="w-4 h-4 mr-2" />
							查看所有插件
						</Button>
					</Link>
					<Button
						variant="outline"
						size="sm"
						onClick={() => setAddDialogOpen(true)}
						aria-label="添加市场"
					>
						<Plus className="w-4 h-4 mr-2" />
						添加市场
					</Button>
					<Button
						variant="outline"
						size="sm"
						onClick={() => {
							loadMarketplaces();
							loadPlugins();
						}}
						disabled={loading}
						aria-label="刷新"
					>
						<RefreshCw
							className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
						/>
						刷新
					</Button>
				</div>
			</div>

			{loading && (
				<div className="flex items-center justify-center py-12">
					<Loader2 className="w-8 h-8 animate-spin text-primary" />
					<span className="ml-3 text-muted-foreground">
						加载中...
					</span>
				</div>
			)}

			{error && (
				<div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
					<p className="font-semibold">加载失败</p>
					<p className="text-sm mt-1">{error}</p>
					<Button
						variant="outline"
						size="sm"
						className="mt-3"
						onClick={() => loadMarketplaces()}
					>
						重试
					</Button>
				</div>
			)}

			{!loading && !error && (
				<>
					{marketplaces.length === 0 ? (
						<div className="text-center py-16 text-muted-foreground">
							<p className="text-sm">暂无已配置市场</p>
							<p className="text-xs mt-2">
								你可以通过 Claude CLI 添加 marketplace
							</p>
						</div>
					) : (
						<div className="space-y-2">
							{/* 各个市场及其插件列表 */}
							{marketplaces.map((m) => {
								const marketPlugins = plugins.filter(
									(p) => p.marketplace === m.name,
								);

								return (
									<div key={m.name}>
										{/* 市场项 */}
										<div
											className="p-4 border rounded-lg bg-card hover:bg-accent cursor-pointer"
											onClick={() =>
												handleMarketplaceClick(m.name)
											}
										>
											<div className="flex items-center justify-between">
												<div className="flex items-center gap-3 flex-1">
													<Store className="w-5 h-5 text-primary" />
													<div className="flex-1">
														<div className="flex items-center gap-2">
															<h3 className="font-semibold">
																{m.name}
															</h3>
															<span className="text-xs text-muted-foreground">
																(
																{
																	marketPlugins.length
																}{" "}
																个插件)
															</span>
															<Button
																variant="ghost"
																size="sm"
																className="h-6 px-2"
																onClick={(e) => {
																	e.stopPropagation();
																	handleUpdateMarketplace(
																		m.name,
																	);
																}}
																disabled={
																	updatingMarketplace ===
																	m.name
																}
																title="更新市场"
															>
																{updatingMarketplace ===
																m.name ? (
																	<Loader2 className="w-3 h-3 animate-spin" />
																) : (
																	<RefreshCw className="w-3 h-3" />
																)}
															</Button>
															<Button
																variant="ghost"
																size="sm"
																className="h-6 px-2 text-destructive hover:text-destructive"
																onClick={(
																	e,
																) => {
																	e.stopPropagation();
																	handleRemoveMarketplace(
																		m.name,
																	);
																}}
															>
																<Trash2 className="w-3 h-3" />
															</Button>
														</div>
														<p className="text-xs text-muted-foreground break-all">
															{m.url ||
																m.source ||
																"—"}
														</p>
														{m.installLocation && (
															<p className="text-xs text-muted-foreground">
																安装位置：
																{
																	m.installLocation
																}
															</p>
														)}
													</div>
												</div>
												{expandedMarketplace ===
												m.name ? (
													<ChevronUp className="w-5 h-5 text-muted-foreground" />
												) : (
													<ChevronDown className="w-5 h-5 text-muted-foreground" />
												)}
											</div>
										</div>

										{/* 该市场的插件列表 - 紧贴在下方 */}
										{expandedMarketplace === m.name && (
											<div className="mt-2 p-4 border border-t-0 rounded-b-lg bg-muted/30">
												{marketPlugins.length === 0 ? (
													<div className="text-center py-8 text-muted-foreground">
														该市场暂无插件
													</div>
												) : (
													<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
														{marketPlugins.map(
															(plugin) => (
																<PluginCard
																	key={
																		plugin.name
																	}
																	plugin={
																		plugin
																	}
																	onInstall={
																		handleInstallClick
																	}
																	onUninstall={
																		handleUninstall
																	}
																	onViewDetails={
																		handleViewDetails
																	}
																	installing={
																		installingPlugin ===
																		plugin.name
																	}
																	uninstalling={
																		uninstallingPlugin ===
																		plugin.name
																	}
																/>
															),
														)}
													</div>
												)}
											</div>
										)}
									</div>
								);
							})}
						</div>
					)}
				</>
			)}

			{/* 插件详情对话框 */}
			<PluginDetailDialog
				plugin={detailPlugin}
				open={detailOpen}
				onOpenChange={setDetailOpen}
				onInstall={handleInstallClick}
				onUninstall={handleUninstall}
				installing={
					installingPlugin === detailPlugin?.name ? true : false
				}
				uninstalling={
					uninstallingPlugin === detailPlugin?.name ? true : false
				}
			/>

			{/* 添加市场对话框 */}
			<Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>添加插件市场</DialogTitle>
						<DialogDescription>
							添加一个新的插件市场源
						</DialogDescription>
					</DialogHeader>
					<div className="space-y-4 py-4">
						<div className="space-y-2">
							<Label htmlFor="market-name">市场名称</Label>
							<Input
								id="market-name"
								placeholder="例如: my-market"
								value={newMarketName}
								onChange={(e) =>
									setNewMarketName(e.target.value)
								}
							/>
						</div>
						<div className="space-y-2">
							<Label htmlFor="market-url">市场 URL</Label>
							<Input
								id="market-url"
								placeholder="例如: https://github.com/user/repo"
								value={newMarketUrl}
								onChange={(e) =>
									setNewMarketUrl(e.target.value)
								}
							/>
						</div>
					</div>
					<DialogFooter>
						<Button
							variant="outline"
							onClick={() => setAddDialogOpen(false)}
							disabled={addingMarket}
						>
							取消
						</Button>
						<Button
							onClick={handleAddMarketplace}
							disabled={addingMarket}
						>
							{addingMarket ? (
								<>
									<Loader2 className="w-4 h-4 mr-2 animate-spin" />
									添加中...
								</>
							) : (
								"添加"
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* 安装 scope 选择对话框 */}
			<Dialog
				open={installDialogOpen}
				onOpenChange={setInstallDialogOpen}
			>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>选择安装范围</DialogTitle>
						<DialogDescription>
							选择插件的安装范围：用户级（全局可用）或项目级（仅当前项目）
						</DialogDescription>
					</DialogHeader>
					<div className="space-y-4 py-4">
						<div className="space-y-2">
							<Label>安装范围</Label>
							<div className="flex flex-col gap-2">
								<button
									type="button"
									className={`p-4 border rounded-lg text-left transition-colors ${
										selectedScope === "user"
											? "bg-primary text-primary-foreground border-primary"
											: "hover:bg-accent"
									}`}
									onClick={() => setSelectedScope("user")}
								>
									<div className="flex items-center gap-3">
										<div className="w-4 h-4 rounded-full border-2 border-current flex items-center justify-center">
											{selectedScope === "user" && (
												<div className="w-2.5 h-2.5 rounded-full bg-current" />
											)}
										</div>
										<div>
											<div className="font-semibold">
												用户级（User）
											</div>
											<div className="text-sm text-muted-foreground">
												全局可用，所有项目共享
											</div>
										</div>
									</div>
								</button>
								<button
									type="button"
									className={`p-4 border rounded-lg text-left transition-colors ${
										selectedScope === "project"
											? "bg-primary text-primary-foreground border-primary"
											: "hover:bg-accent"
									}`}
									onClick={() => setSelectedScope("project")}
								>
									<div className="flex items-center gap-3">
										<div className="w-4 h-4 rounded-full border-2 border-current flex items-center justify-center">
											{selectedScope === "project" && (
												<div className="w-2.5 h-2.5 rounded-full bg-current" />
											)}
										</div>
										<div>
											<div className="font-semibold">
												项目级（Project）
											</div>
											<div className="text-sm text-muted-foreground">
												仅当前项目可用
											</div>
										</div>
									</div>
								</button>
							</div>
						</div>
					</div>
					<DialogFooter>
						<Button
							variant="outline"
							onClick={() => setInstallDialogOpen(false)}
							disabled={installingPlugin !== null}
						>
							取消
						</Button>
						<Button
							onClick={handleConfirmInstall}
							disabled={installingPlugin !== null}
						>
							{installingPlugin ? (
								<>
									<Loader2 className="w-4 h-4 mr-2 animate-spin" />
									安装中...
								</>
							) : (
								"确认安装"
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
		</div>
	);
}
