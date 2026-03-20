import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Settings from "./index";

const showMock = vi.fn(() => Promise.resolve());
const setFocusMock = vi.fn(() => Promise.resolve());

vi.mock("@tauri-apps/api/window", () => ({
  getCurrentWindow: vi.fn(() => ({
    show: showMock,
    setFocus: setFocusMock,
  })),
}));

describe("Settings page", () => {
  it("toggles theme via data-theme attribute", async () => {
    const user = userEvent.setup();
    render(<Settings />);

    await user.click(screen.getByRole("button", { name: "深色" }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    await user.click(screen.getByRole("button", { name: "浅色" }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");

    await user.click(screen.getByRole("button", { name: "跟随系统" }));
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("focus button calls window show and setFocus", async () => {
    const user = userEvent.setup();
    render(<Settings />);

    await user.click(screen.getByRole("button", { name: "显示并聚焦主窗口" }));
    expect(showMock).toHaveBeenCalledTimes(1);
    expect(setFocusMock).toHaveBeenCalledTimes(1);
  });
});

