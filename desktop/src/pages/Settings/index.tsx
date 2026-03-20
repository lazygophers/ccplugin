import { useEffect, useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Settings as SettingsIcon, Moon, Sun, Monitor } from "lucide-react";

type ThemeMode = "light" | "dark" | "system";

export default function Settings() {
  const [theme, setTheme] = useState<ThemeMode>("system");

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
      return;
    }
    root.setAttribute("data-theme", theme);
  }, [theme]);

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
    </div>
  );
}
