import { describe, it, expect, vi, beforeEach } from "vitest";
import { PluginService } from "./plugin-service";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

describe("PluginService", () => {
  beforeEach(() => {
    vi.mocked(invoke).mockReset();
    vi.mocked(listen).mockReset();
  });

  describe("install", () => {
    it("installs plugin with default marketplace", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.install("python", undefined, handler);

      expect(invoke).toHaveBeenCalledWith("install_plugin", {
        pluginName: "python",
        marketplace: "ccplugin-market",
        scope: "user",
      });
      expect(typeof cleanup).toBe("function");
    });

    it("installs plugin with custom marketplace", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await PluginService.install("python", "custom-market");

      expect(invoke).toHaveBeenCalledWith("install_plugin", {
        pluginName: "python",
        marketplace: "custom-market",
        scope: "user",
      });
    });

    it("sets up event listener when handler provided", async () => {
      const unlisten = vi.fn();
      vi.mocked(listen).mockResolvedValueOnce(unlisten);
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.install("python", "ccplugin-market", handler);

      expect(listen).toHaveBeenCalled();
      await cleanup();
      expect(unlisten).toHaveBeenCalled();
    });

    it("cleanup function works without handler", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      const cleanup = await PluginService.install("python");

      await expect(cleanup()).resolves.toBeUndefined();
    });
  });

  describe("update", () => {
    it("updates plugin", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.update("python", handler);

      expect(invoke).toHaveBeenCalledWith("update_plugin", { pluginName: "python", scope: undefined });
      expect(typeof cleanup).toBe("function");
    });

    it("sets up event listener when handler provided", async () => {
      const unlisten = vi.fn();
      vi.mocked(listen).mockResolvedValueOnce(unlisten);
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.update("python", handler);

      expect(listen).toHaveBeenCalled();
      await cleanup();
      expect(unlisten).toHaveBeenCalled();
    });

    it("works without handler", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      const cleanup = await PluginService.update("python");

      await expect(cleanup()).resolves.toBeUndefined();
    });
  });

  describe("uninstall", () => {
    it("uninstalls plugin", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.uninstall("python", handler);

      expect(invoke).toHaveBeenCalledWith("uninstall_plugin", { pluginName: "python" });
      expect(typeof cleanup).toBe("function");
    });

    it("sets up event listener when handler provided", async () => {
      const unlisten = vi.fn();
      vi.mocked(listen).mockResolvedValueOnce(unlisten);
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.uninstall("python", handler);

      expect(listen).toHaveBeenCalled();
      await cleanup();
      expect(unlisten).toHaveBeenCalled();
    });

    it("works without handler", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      const cleanup = await PluginService.uninstall("python");

      await expect(cleanup()).resolves.toBeUndefined();
    });
  });

  describe("clean", () => {
    it("cleans cache", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.clean(handler);

      expect(invoke).toHaveBeenCalledWith("clean_cache");
      expect(typeof cleanup).toBe("function");
    });

    it("sets up event listener for cache events", async () => {
      const unlisten = vi.fn();
      vi.mocked(listen).mockResolvedValueOnce(unlisten);
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.clean(handler);

      expect(listen).toHaveBeenCalledWith("plugin-event", expect.any(Function));
      await cleanup();
      expect(unlisten).toHaveBeenCalled();
    });

    it("works without handler", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      const cleanup = await PluginService.clean();

      await expect(cleanup()).resolves.toBeUndefined();
    });
  });

  describe("getInfo", () => {
    it("gets plugin info with handler", async () => {
      const unlisten = vi.fn();
      vi.mocked(listen).mockResolvedValueOnce(unlisten);
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      const cleanup = await PluginService.getInfo("python", handler);

      expect(invoke).toHaveBeenCalledWith("get_plugin_info", { pluginName: "python" });
      expect(listen).toHaveBeenCalled();
      expect(typeof cleanup).toBe("function");

      await cleanup();
      expect(unlisten).toHaveBeenCalled();
    });
  });

  describe("Error Handling", () => {
    it("handles install errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Install failed"));

      await expect(PluginService.install("python")).rejects.toThrow("Install failed");
    });

    it("handles update errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Update failed"));

      await expect(PluginService.update("python")).rejects.toThrow("Update failed");
    });

    it("handles uninstall errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Uninstall failed"));

      await expect(PluginService.uninstall("python")).rejects.toThrow("Uninstall failed");
    });

    it("handles clean errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Clean failed"));

      await expect(PluginService.clean()).rejects.toThrow("Clean failed");
    });

    it("handles getInfo errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Get info failed"));

      await expect(PluginService.getInfo("python", vi.fn())).rejects.toThrow("Get info failed");
    });

    it("handles listen errors", async () => {
      vi.mocked(listen).mockRejectedValueOnce(new Error("Listen failed"));
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(PluginService.install("python", "ccplugin-market", vi.fn())).rejects.toThrow("Listen failed");
    });
  });

  describe("Event Handler Integration", () => {
    it("passes events to handler for install", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      await PluginService.install("python", "ccplugin-market", handler);

      if (capturedHandler) {
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "python",
            data: { progress: 50 },
          },
        });
      }

      expect(handler).toHaveBeenCalledWith({
        event_type: "plugin-install-progress",
        plugin_name: "python",
        data: { progress: 50 },
      });
    });

    it("passes events to handler for update", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      await PluginService.update("python", handler);

      if (capturedHandler) {
        capturedHandler({
          payload: {
            event_type: "plugin-update-progress",
            plugin_name: "python",
            data: { progress: 75 },
          },
        });
      }

      expect(handler).toHaveBeenCalledWith({
        event_type: "plugin-update-progress",
        plugin_name: "python",
        data: { progress: 75 },
      });
    });

    it("passes events to handler for uninstall", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      await PluginService.uninstall("python", handler);

      if (capturedHandler) {
        capturedHandler({
          payload: {
            event_type: "plugin-uninstall-progress",
            plugin_name: "python",
            data: { progress: 100 },
          },
        });
      }

      expect(handler).toHaveBeenCalledWith({
        event_type: "plugin-uninstall-progress",
        plugin_name: "python",
        data: { progress: 100 },
      });
    });

    it("passes cache events to handler", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      vi.mocked(invoke).mockResolvedValueOnce(undefined);
      const handler = vi.fn();

      await PluginService.clean(handler);

      if (capturedHandler) {
        capturedHandler({
          payload: {
            event_type: "cache-clean-progress",
            plugin_name: "cache",
            data: { message: "Cleaning..." },
          },
        });
      }

      expect(handler).toHaveBeenCalledWith({
        event_type: "cache-clean-progress",
        plugin_name: "cache",
        data: { message: "Cleaning..." },
      });
    });
  });
});
