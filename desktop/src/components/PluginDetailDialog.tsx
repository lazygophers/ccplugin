import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
	DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Loader2, Download, Package, User, Tag, RefreshCw, CheckCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { PluginInfo } from "@/types";
import { getCategoryBadgeClass, getCategoryLabel } from "@/lib/plugin-ui";

interface PluginDetailDialogProps {
  plugin: PluginInfo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInstall?: (pluginName: string) => void;
  onUpdate?: (pluginName: string) => void;
  onUninstall?: (pluginName: string) => void;
  installing?: boolean;
  updating?: boolean;
  uninstalling?: boolean;
}

export function PluginDetailDialog({
  plugin,
  open,
  onOpenChange,
  onInstall,
  onUpdate,
  onUninstall,
  installing,
  updating,
  uninstalling,
}: PluginDetailDialogProps) {
  const [readme, setReadme] = useState<string>("");
  const [loadingReadme, setLoadingReadme] = useState(false);
  const [readmeError, setReadmeError] = useState<string | null>(null);

  useEffect(() => {
    if (!plugin || !open) {
      setReadme("");
      setReadmeError(null);
      return;
    }

    const currentPlugin = plugin;
    setLoadingReadme(true);
    const controller = new AbortController();

    async function load() {
      try {
        setReadmeError(null);

        // 优先用 GitHub raw README（仓库字段通常是 tree 链接）
        const readmeUrl = buildGithubRawReadmeUrl(currentPlugin.repository);
        if (readmeUrl) {
          const res = await fetch(readmeUrl, { signal: controller.signal });
          if (!res.ok) {
            throw new Error(`README 请求失败: ${res.status}`);
          }
          const text = await res.text();
          setReadme(text);
          return;
        }

        // fallback：生成基础说明
        setReadme(buildFallbackReadme(currentPlugin));
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        const msg = e instanceof Error ? e.message : String(e);
        setReadme(buildFallbackReadme(currentPlugin));
        setReadmeError(msg);
      } finally {
        setLoadingReadme(false);
      }
    }

    load();
    return () => controller.abort();
  }, [plugin, open]);

  if (!plugin) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-2xl flex items-center gap-2 whitespace-nowrap">
                <Package className="w-6 h-6 flex-shrink-0" />
                <span className="truncate">{plugin.name}</span>
              </DialogTitle>
              <DialogDescription className="mt-2">
                {plugin.description}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={getCategoryBadgeClass(plugin.category)}>
                {getCategoryLabel(plugin.category)}
              </Badge>
              {plugin.installed ? (
                <>
                  <Badge variant="secondary" className="bg-green-500/10 text-green-700">
                    已安装 v{plugin.installed_version}
                  </Badge>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm">
                        <CheckCircle className="w-4 h-4 mr-2" />
                        已安装
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {onUpdate && (
                        <DropdownMenuItem
                          onClick={() => onUpdate(plugin.name)}
                          disabled={updating}
                          title={`claude plugin update ${plugin.name}`}
                        >
                          <RefreshCw className={`w-4 h-4 mr-2 ${updating ? "animate-spin" : ""}`} />
                          {updating ? "更新中..." : "更新"}
                        </DropdownMenuItem>
                      )}
                      {onUninstall && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => onUninstall(plugin.name)}
                            disabled={uninstalling || updating}
                            className="text-destructive focus:text-destructive"
                          >
                            {uninstalling ? "卸载中..." : "卸载"}
                          </DropdownMenuItem>
                        </>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
              ) : (
                <Button
                  onClick={() => onInstall?.(plugin.name)}
                  disabled={installing}
                  size="sm"
                >
                  {installing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      安装中...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      安装插件
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        {/* Metadata */}
        <div className="py-4 border-y space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2 text-sm">
              <Package className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">版本:</span>
              <span className="text-muted-foreground">v{plugin.version}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <User className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">市场:</span>
              <span className="text-muted-foreground">{plugin.marketplace}</span>
            </div>
          </div>

          {/* 安装范围 */}
          {plugin.installed && plugin.installed_info && plugin.installed_info.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm font-medium">安装范围</div>
              {plugin.installed_info.map((info) => (
                <div key={info.scope} className="pl-4 text-sm space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">
                      {info.scope === "user"
                        ? "用户"
                        : info.scope === "project"
                          ? "项目"
                          : info.scope}
                    </span>
                    <span className="text-muted-foreground">v{info.version}</span>
                  </div>
                  {info.scope === "project" && info.path && (
                    <div className="text-xs text-muted-foreground pl-4">{info.path}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {plugin.keywords.length > 0 && (
            <div className="flex items-start gap-2 text-sm">
              <Tag className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <span className="font-medium whitespace-nowrap">关键词:</span>
              <div className="flex flex-wrap gap-1">
                {plugin.keywords.map((keyword) => (
                  <Badge key={keyword} variant="outline" className="text-xs">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* README Content */}
        <div className="mt-4">
          {loadingReadme ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <span className="ml-3 text-muted-foreground">加载文档...</span>
            </div>
          ) : (
            <>
              {readmeError && (
                <div className="mb-4 p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
                  <p className="font-semibold">无法加载远程文档</p>
                  <p className="text-sm mt-1">{readmeError}</p>
                </div>
              )}
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{readme}</ReactMarkdown>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function buildFallbackReadme(plugin: PluginInfo): string {
  const repoLine = plugin.repository ? `- **仓库**: ${plugin.repository}` : "";
  const homeLine = plugin.homepage ? `- **主页**: ${plugin.homepage}` : "";
  const licenseLine = plugin.license ? `- **许可证**: ${plugin.license}` : "";
  const metaLines = [repoLine, homeLine, licenseLine].filter(Boolean).join("\n");

  return `# ${plugin.name}

${plugin.description}

## 版本信息
- **当前版本**: ${plugin.version}
- **作者**: ${plugin.author}
${metaLines ? `\n${metaLines}` : ""}

## 安装

\`\`\`bash
claude plugin install ${plugin.name}
\`\`\`

## 关键词

${plugin.keywords.length ? plugin.keywords.join(", ") : "（无）"}
`;
}

export function buildGithubRawReadmeUrl(repositoryUrl: string): string | null {
  // 期望格式：https://github.com/<owner>/<repo>/tree/<branch>/<path>
  try {
    const url = new URL(repositoryUrl);
    if (url.hostname !== "github.com") return null;
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length < 5) return null;
    if (parts[2] !== "tree") return null;

    const owner = parts[0];
    const repo = parts[1];
    const branch = parts[3];
    const path = parts.slice(4).join("/");

    if (!owner || !repo || !branch || !path) return null;
    const encodedPath = path
      .split("/")
      .map((seg) => encodeURIComponent(seg))
      .join("/");
    return `https://raw.githubusercontent.com/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/${encodeURIComponent(branch)}/${encodedPath}/README.md`;
  } catch {
    return null;
  }
}
