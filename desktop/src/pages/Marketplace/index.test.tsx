import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { invoke } from "@tauri-apps/api/core";
import Marketplace from "./index";
import { renderWithRouter } from "@/test/render";
import { pluginFixtures } from "@/test/fixtures";

const installMock = vi.fn();
const uninstallMock = vi.fn();
let progressValue: any = null;

vi.mock("@/hooks/usePythonCommand", () => ({
  usePythonCommand: () => ({
    install: installMock,
    uninstall: uninstallMock,
    progress: progressValue,
  }),
}));

describe("Marketplace page", () => {
  beforeEach(() => {
    installMock.mockReset();
    uninstallMock.mockReset();
    progressValue = null;
    vi.mocked(invoke).mockReset();
  });

  it("renders plugins and supports search params sync", async () => {
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/marketplace", element: <Marketplace /> }], {
      initialEntries: ["/marketplace?q=git&category=tools"],
    });

    const input = await screen.findByRole("textbox", { name: "搜索插件" });
    expect(input).toHaveValue("git");
    expect(screen.getByRole("button", { name: "工具 (1)" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "git" })).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    vi.mocked(invoke).mockImplementationOnce(
      () => new Promise(() => {})
    );
    renderWithRouter([{ path: "/marketplace", element: <Marketplace /> }], {
      initialEntries: ["/marketplace"],
    });
    expect(screen.getByText("加载插件列表...")).toBeInTheDocument();
  });

  it("shows error state and allows retry", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockRejectedValueOnce(new Error("boom")).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/marketplace", element: <Marketplace /> }], {
      initialEntries: ["/marketplace"],
    });

    expect(await screen.findByText("加载失败")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it("handles install and refresh", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    installMock.mockResolvedValueOnce(undefined);

    renderWithRouter([{ path: "/marketplace", element: <Marketplace /> }], {
      initialEntries: ["/marketplace"],
    });

    await screen.findByRole("heading", { name: "git" });
    await user.click(screen.getByRole("button", { name: "安装" }));
    expect(installMock).toHaveBeenCalledWith("git");
    // refresh triggered after install
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it("handles uninstall and refresh", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValueOnce(true);
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    uninstallMock.mockResolvedValueOnce(undefined);

    renderWithRouter([{ path: "/marketplace", element: <Marketplace /> }], {
      initialEntries: ["/marketplace"],
    });

    const heading = await screen.findByRole("heading", { name: "python" });
    const card = heading.closest('[role="article"]');
    expect(card).toBeTruthy();
    await user.click(within(card as HTMLElement).getByRole("button", { name: /卸载/ }));
    expect(confirmSpy).toHaveBeenCalled();
    expect(uninstallMock).toHaveBeenCalledWith("python");
    expect(invoke).toHaveBeenCalledTimes(2);
    confirmSpy.mockRestore();
  });

  it("shows global progress when installing and progress exists", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures);

    installMock.mockImplementationOnce(
      () => new Promise<void>(() => {})
    );
    progressValue = {
      plugin_name: "git",
      progress: 42,
      message: "downloading",
      status: "downloading",
    };

    renderWithRouter([{ path: "/marketplace", element: <Marketplace /> }], {
      initialEntries: ["/marketplace"],
    });

    await screen.findByRole("heading", { name: "git" });
    await user.click(screen.getByRole("button", { name: "安装" }));
    expect(await screen.findByText("42%")).toBeInTheDocument();
  });
});
