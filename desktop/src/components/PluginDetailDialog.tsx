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
import type { PluginInfo } from "@/hooks/usePlugins";

interface PluginDetailDialogProps {
  plugin: PluginInfo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInstall?: (pluginName: string) => void;
  installing?: boolean;
}

export function PluginDetailDialog({
  plugin,
  open,
  onOpenChange,
  onInstall,
  installing,
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

    // TODO: 实现从插件源读取README的逻辑
    // 当前暂时显示占位内容
    setLoadingReadme(true);
    setTimeout(() => {
      setReadme(`# ${plugin.name}

${plugin.description}

## 版本信息
- **当前版本**: ${plugin.version}
- **作者**: ${plugin.author}

## 功能特性

此插件提供了丰富的功能特性，详细文档即将提供...

## 安装说明

使用以下命令安装此插件：

\`\`\`bash
claude plugin install ${plugin.name}
\`\`\`

## 更多信息

关键词: ${plugin.keywords.join(", ")}
`);
      setLoadingReadme(false);
    }, 500);
  }, [plugin, open]);

  if (!plugin) return null;

  const categoryColor = {
    tools: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
    languages: "bg-green-500/10 text-green-700 dark:text-green-400",
    office: "bg-purple-500/10 text-purple-700 dark:text-purple-400",
    novels: "bg-pink-500/10 text-pink-700 dark:text-pink-400",
    other: "bg-gray-500/10 text-gray-700 dark:text-gray-400",
  }[plugin.category] || "bg-gray-500/10 text-gray-700 dark:text-gray-400";

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
              <Badge className={categoryColor}>{plugin.category}</Badge>
              {plugin.installed ? (
                <Badge variant="secondary" className="bg-green-500/10 text-green-700">
                  已安装 v{plugin.installed_version}
                </Badge>
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
          ) : readmeError ? (
            <div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
              <p className="font-semibold">无法加载文档</p>
              <p className="text-sm mt-1">{readmeError}</p>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {readme}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
