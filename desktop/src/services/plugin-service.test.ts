import { describe, it, expect, vi } from "vitest";

vi.mock("./tauri-commands", () => ({
  installPlugin: vi.fn(),
  updatePlugin: vi.fn(),
  cleanCache: vi.fn(),
  getPluginInfo: vi.fn(),
  listenToInstallProgress: vi.fn(),
}));

import {
  installPlugin,
  updatePlugin,
  cleanCache,
  getPluginInfo,
  listenToInstallProgress,
} from "./tauri-commands";
import { PluginService } from "./plugin-service";

describe("PluginService", () => {
  it("install does not listen when onProgress missing", async () => {
    vi.mocked(installPlugin).mockResolvedValueOnce({ success: true, stdout: "", stderr: "" });

    await PluginService.install("python");
    expect(listenToInstallProgress).not.toHaveBeenCalled();
  });

  it("install listens and unlistens", async () => {
    const unlisten = vi.fn();
    vi.mocked(listenToInstallProgress).mockResolvedValueOnce(unlisten);
    vi.mocked(installPlugin).mockResolvedValueOnce({ success: true, stdout: "", stderr: "" });

    const onProgress = vi.fn();
    await PluginService.install("python", "ccplugin-market", onProgress);
    expect(listenToInstallProgress).toHaveBeenCalledWith(onProgress);
    expect(unlisten).toHaveBeenCalledTimes(1);
  });

  it("install unlistens even if command throws", async () => {
    const unlisten = vi.fn();
    vi.mocked(listenToInstallProgress).mockResolvedValueOnce(unlisten);
    vi.mocked(installPlugin).mockRejectedValueOnce(new Error("boom"));

    await expect(
      PluginService.install("python", "ccplugin-market", vi.fn())
    ).rejects.toThrow("boom");
    expect(unlisten).toHaveBeenCalledTimes(1);
  });

  it("update listens and unlistens", async () => {
    const unlisten = vi.fn();
    vi.mocked(listenToInstallProgress).mockResolvedValueOnce(unlisten);
    vi.mocked(updatePlugin).mockResolvedValueOnce({ success: true, stdout: "", stderr: "" });

    const onProgress = vi.fn();
    await PluginService.update("python", onProgress);
    expect(listenToInstallProgress).toHaveBeenCalledWith(onProgress);
    expect(unlisten).toHaveBeenCalledTimes(1);
  });

  it("update does not listen when onProgress missing", async () => {
    vi.mocked(updatePlugin).mockResolvedValueOnce({ success: true, stdout: "", stderr: "" });
    await PluginService.update("python");
    expect(listenToInstallProgress).not.toHaveBeenCalled();
  });

  it("clean proxies cleanCache", async () => {
    vi.mocked(cleanCache).mockResolvedValueOnce({ success: true, stdout: "ok", stderr: "" });
    await expect(PluginService.clean()).resolves.toEqual({ success: true, stdout: "ok", stderr: "" });
  });

  it("getInfo proxies getPluginInfo", async () => {
    vi.mocked(getPluginInfo).mockResolvedValueOnce({ success: true, stdout: "info", stderr: "" });
    await expect(PluginService.getInfo("python")).resolves.toEqual({ success: true, stdout: "info", stderr: "" });
  });
});
