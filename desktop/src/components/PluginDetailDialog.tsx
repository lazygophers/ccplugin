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
import { Loader2, Download, Package, User, Tag } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { PluginInfo } from "@/types";
import { getCategoryBadgeClass, getCategoryLabel } from "@/lib/plugin-ui";

interface PluginDetailDialogProps {
  plugin: PluginInfo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInstall?: (pluginName: string) => void;
  onUninstall?: (pluginName: string) => void;
  installing?: boolean;
  uninstalling?: boolean;
}

export function PluginDetailDialog({
  plugin,
  open,
  onOpenChange,
  onInstall,
  onUninstall,
  installing,
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
              <DialogTitle className="text-2xl flex items-center gap-2">
                <Package className="w-6 h-6" />
                {plugin.name}
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
                  {onUninstall && (
                    <Button
                      variant="destructive"
                      onClick={() => onUninstall(plugin.name)}
                      disabled={uninstalling}
                      size="sm"
                      aria-label={`卸载 ${plugin.name}`}
                    >
                      {uninstalling ? "卸载中..." : "卸载"}
                    </Button>
                  )}
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
        <div className="grid grid-cols-2 gap-4 py-4 border-y">
          <div className="flex items-center gap-2 text-sm">
            <User className="w-4 h-4 text-muted-foreground" />
            <span className="font-medium">作者:</span>
            <span className="text-muted-foreground">{plugin.author}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Package className="w-4 h-4 text-muted-foreground" />
            <span className="font-medium">版本:</span>
            <span className="text-muted-foreground">{plugin.version}</span>
          </div>
          {plugin.installed && plugin.installed_scope && (
            <>
              <div className="flex items-center gap-2 text-sm">
                <Badge variant="outline" className="bg-blue-500/10 text-blue-700 border-blue-500/20">
                  {plugin.installed_scope === "user" ? "用户安装" : "项目安装"}
                </Badge>
              </div>
              {plugin.installed_scope === "project" && plugin.installed_path && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium">项目路径:</span>
                  <span className="text-muted-foreground font-mono text-xs">{plugin.installed_path}</span>
                </div>
              )}
              {plugin.installed_version && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium">已安装版本:</span>
                  <span className="text-muted-foreground">{plugin.installed_version}</span>
                </div>
              )}
            </>
          )}
          {plugin.keywords.length > 0 && (
            <div className="col-span-2 flex items-start gap-2 text-sm">
              <Tag className="w-4 h-4 text-muted-foreground mt-0.5" />
              <span className="font-medium">关键词:</span>
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
