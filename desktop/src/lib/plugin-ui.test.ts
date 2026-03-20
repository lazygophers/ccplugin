import { describe, it, expect } from "vitest";
import { getCategoryBadgeClass, getCategoryLabel, getCategoryOptions } from "./plugin-ui";

describe("plugin-ui helpers", () => {
  it("getCategoryLabel returns human labels", () => {
    expect(getCategoryLabel("tools")).toBe("工具");
    expect(getCategoryLabel("languages")).toBe("语言");
    expect(getCategoryLabel("office")).toBe("Office");
    expect(getCategoryLabel("novels")).toBe("小说");
    expect(getCategoryLabel("other")).toBe("其他");
  });

  it("getCategoryLabel falls back to '其他' for unknown", () => {
    expect(getCategoryLabel("unknown")).toBe("其他");
  });

  it("getCategoryBadgeClass returns stable classnames", () => {
    expect(getCategoryBadgeClass("tools")).toContain("blue");
    expect(getCategoryBadgeClass("languages")).toContain("green");
    expect(getCategoryBadgeClass("unknown")).toContain("gray");
  });

  it("getCategoryOptions contains 'all' plus categories", () => {
    const opts = getCategoryOptions();
    expect(opts[0]).toEqual({ value: "all", label: "全部" });
    expect(opts.map((o) => o.value)).toEqual([
      "all",
      "tools",
      "languages",
      "office",
      "novels",
      "other",
    ]);
  });
});

