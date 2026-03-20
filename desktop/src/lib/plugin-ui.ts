export type PluginCategory =
  | "tools"
  | "languages"
  | "office"
  | "novels"
  | "other"
  | "all";

const CATEGORY_META: Record<
  Exclude<PluginCategory, "all">,
  { label: string; badgeClass: string }
> = {
  tools: {
    label: "工具",
    badgeClass:
      "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
  },
  languages: {
    label: "语言",
    badgeClass:
      "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
  },
  office: {
    label: "Office",
    badgeClass:
      "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20",
  },
  novels: {
    label: "小说",
    badgeClass:
      "bg-pink-500/10 text-pink-700 dark:text-pink-400 border-pink-500/20",
  },
  other: {
    label: "其他",
    badgeClass:
      "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20",
  },
};

export function getCategoryLabel(category: string): string {
  const key = category as keyof typeof CATEGORY_META;
  const meta = CATEGORY_META[key] || CATEGORY_META.other;
  return meta.label;
}

export function getCategoryBadgeClass(category: string): string {
  const key = category as keyof typeof CATEGORY_META;
  const meta = CATEGORY_META[key] || CATEGORY_META.other;
  return meta.badgeClass;
}

export function getCategoryOptions(): Array<{ value: PluginCategory; label: string }> {
  return [
    { value: "all", label: "全部" },
    { value: "tools", label: CATEGORY_META.tools.label },
    { value: "languages", label: CATEGORY_META.languages.label },
    { value: "office", label: CATEGORY_META.office.label },
    { value: "novels", label: CATEGORY_META.novels.label },
    { value: "other", label: CATEGORY_META.other.label },
  ];
}
