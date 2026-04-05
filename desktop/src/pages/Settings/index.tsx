import { useEffect, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Settings as SettingsIcon, Moon, Sun, Monitor, Globe, Save } from "lucide-react";
import { ProxyService } from "@/services/proxy-service";
import type { ProxyConfig } from "@/services/proxy-service";

type ThemeMode = "light" | "dark" | "system";

export default function Settings() {
  const [theme, setTheme] = useState<ThemeMode>("system");
  const [proxyConfig, setProxyConfig] = useState<ProxyConfig>({
    enabled: false,
    http: "",
    https: "",
    noProxy: "localhost,127.0.0.1",
  });
  const [loadingProxy, setLoadingProxy] = useState(false);
  const [proxyError, setProxyError] = useState<string | null>(null);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
      return;
    }
    root.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    // 加载代理配置
    ProxyService.load()
      .then(setProxyConfig)
      .catch(() => {
        // 忽略加载失败，使用默认值
      });
  }, []);

  const handleSaveProxy = async () => {
    setLoadingProxy(true);
    setProxyError(null);
    try {
      await ProxyService.save(proxyConfig);
      alert("代理配置已保存！请重启应用以使设置生效。");
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setProxyError(msg);
      alert(`保存失败: ${msg}`);
    } finally {
      setLoadingProxy(false);
    }
  };

  const focusMainWindow = async () => {
    const win = getCurrentWindow();
    await win.show();
    await win.setFocus();
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <SettingsIcon className="w-7 h-7 text-primary" />
          设置
        </h1>
        <p className="text-muted-foreground">
          调整应用视觉风格与行为偏好
        </p>
      </div>

      <section className="rounded-lg border bg-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">主题</h2>
          <Badge variant="outline">实时生效</Badge>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={theme === "light" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("light")}
          >
            <Sun className="w-4 h-4 mr-2" />
            浅色
          </Button>
          <Button
            variant={theme === "dark" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("dark")}
          >
            <Moon className="w-4 h-4 mr-2" />
            深色
          </Button>
          <Button
            variant={theme === "system" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("system")}
          >
            <Monitor className="w-4 h-4 mr-2" />
            跟随系统
          </Button>
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5 space-y-4">
        <h2 className="text-lg font-semibold">行为</h2>
        <p className="text-sm text-muted-foreground">
          通知、自动更新、开机自启等能力将在后续版本中提供更完整的可视化配置。
        </p>
      </section>

      <section className="rounded-lg border bg-card p-5 space-y-3">
        <h2 className="text-lg font-semibold">窗口</h2>
        <Button variant="outline" onClick={focusMainWindow}>
          显示并聚焦主窗口
        </Button>
      </section>

      <section className="rounded-lg border bg-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            <h2 className="text-lg font-semibold">系统代理</h2>
          </div>
          <Badge variant="outline">需要重启</Badge>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="proxy-enabled"
              checked={proxyConfig.enabled}
              onChange={(e) => setProxyConfig({ ...proxyConfig, enabled: e.target.checked })}
              className="w-4 h-4"
            />
            <Label htmlFor="proxy-enabled" className="cursor-pointer">
              启用系统代理
            </Label>
          </div>

          {proxyConfig.enabled && (
            <>
              <div className="space-y-2">
                <Label htmlFor="proxy-http">HTTP 代理</Label>
                <Input
                  id="proxy-http"
                  placeholder="http://127.0.0.1:7890"
                  value={proxyConfig.http}
                  onChange={(e) => setProxyConfig({ ...proxyConfig, http: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  格式：http://host:port 或 socks5://host:port
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="proxy-https">HTTPS 代理</Label>
                <Input
                  id="proxy-https"
                  placeholder="http://127.0.0.1:7890"
                  value={proxyConfig.https}
                  onChange={(e) => setProxyConfig({ ...proxyConfig, https: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  如果不填写，将使用 HTTP 代理配置
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="proxy-no-proxy">不使用代理的地址</Label>
                <Input
                  id="proxy-no-proxy"
                  placeholder="localhost,127.0.0.1,*.local"
                  value={proxyConfig.noProxy}
                  onChange={(e) => setProxyConfig({ ...proxyConfig, noProxy: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  多个地址用逗号分隔，支持通配符
                </p>
              </div>

              <Button onClick={handleSaveProxy} disabled={loadingProxy} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                {loadingProxy ? "保存中..." : "保存代理配置"}
              </Button>
            </>
          )}
        </div>

        <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
          <p className="font-medium mb-1">说明：</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>代理配置将用于网络请求（如插件市场同步）</li>
            <li>保存后需要重启应用才能生效</li>
            <li>支持 HTTP/HTTPS/SOCKS5 代理协议</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
