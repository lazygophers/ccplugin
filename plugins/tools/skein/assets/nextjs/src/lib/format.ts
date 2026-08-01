// 时间格式化 + 工具函数 (从旧 app.js 移植)

export function fmtRelative(ts: number | null | undefined): string {
  if (!ts) return "";
  const diff = Date.now() - ts;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return "刚刚";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  const mon = Math.floor(day / 30);
  if (mon < 12) return `${mon} 个月前`;
  return `${Math.floor(mon / 12)} 年前`;
}

export function fmtTime(ts: number | null | undefined): string {
  if (!ts) return "";
  const d = new Date(ts);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

export function fmtHours(h: number): string {
  if (h <= 0) return "—";
  if (h < 1) return `${Math.round(h * 60)} 分钟`;
  if (h < 8) return `${h.toFixed(1)} 小时`;
  const days = h / 8;
  if (days < 5) return `${days.toFixed(1)} 人天`;
  return `${Math.round(days)} 人天`;
}

// Priority helpers
export function prioLevel(p: unknown): number {
  return p != null ? Number(p) : 5;
}

export function prioLabel(p: unknown): string {
  const v = prioLevel(p);
  if (v <= 2) return "紧急";
  if (v <= 4) return "高";
  if (v <= 6) return "中";
  if (v <= 8) return "低";
  return "最低";
}

export function prioShortLabel(p: unknown): string {
  const v = prioLevel(p);
  if (v <= 2) return "紧急";
  if (v <= 4) return "高";
  if (v <= 6) return "中";
  return "低";
}
