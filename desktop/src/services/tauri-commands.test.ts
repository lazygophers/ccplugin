import { describe, it, expect, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import {
  installPlugin,
  updatePlugin,
  uninstallPlugin,
  cleanCache,
  getPluginInfo,
  listenToInstallProgress,
} from "./tauri-commands";

describe("tauri-commands", () => {
  it("installPlugin invokes tauri command", async () => {
    const mockResult = { success: true, stdout: "ok", stderr: "" };
    vi.mocked(invoke).mockResolvedValueOnce(mockResult);

    await expect(installPlugin("python", "ccplugin-market")).resolves.toEqual(mockResult);
    expect(invoke).toHaveBeenCalledWith("install_plugin", {
      pluginName: "python",
      marketplace: "ccplugin-market",
    });
  });

  it("updatePlugin invokes tauri command", async () => {
    const mockResult = { success: true, stdout: "updated", stderr: "" };
    vi.mocked(invoke).mockResolvedValueOnce(mockResult);

    await expect(updatePlugin("python")).resolves.toEqual(mockResult);
    expect(invoke).toHaveBeenCalledWith("update_plugin", { pluginName: "python" });
  });

  it("uninstallPlugin invokes tauri command", async () => {
    const mockResult = { success: true, stdout: "removed", stderr: "" };
    vi.mocked(invoke).mockResolvedValueOnce(mockResult);

    await expect(uninstallPlugin("python")).resolves.toEqual(mockResult);
    expect(invoke).toHaveBeenCalledWith("uninstall_plugin", { pluginName: "python" });
  });

  it("cleanCache invokes tauri command", async () => {
    const mockResult = { success: true, stdout: "clean", stderr: "" };
    vi.mocked(invoke).mockResolvedValueOnce(mockResult);

    await expect(cleanCache()).resolves.toEqual(mockResult);
    expect(invoke).toHaveBeenCalledWith("clean_cache");
  });

  it("getPluginInfo invokes tauri command", async () => {
    const mockResult = { success: true, stdout: "info", stderr: "" };
    vi.mocked(invoke).mockResolvedValueOnce(mockResult);

    await expect(getPluginInfo("python")).resolves.toEqual(mockResult);
    expect(invoke).toHaveBeenCalledWith("get_plugin_info", { pluginName: "python" });
  });

  it("listenToInstallProgress proxies event payload", async () => {
    const callback = vi.fn();
    const unlisten = vi.fn();
    vi.mocked(listen).mockImplementationOnce(async (_eventName, handler) => {
      handler({ payload: { plugin_name: "python", progress: 10 } } as never);
      return unlisten;
    });

    const returnedUnlisten = await listenToInstallProgress(callback);
    expect(callback).toHaveBeenCalledWith({ plugin_name: "python", progress: 10 });
    expect(returnedUnlisten).toBe(unlisten);
  });
});
