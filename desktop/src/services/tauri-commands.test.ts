import { describe, it, expect, vi, beforeEach } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import {
  installPlugin,
  updatePlugin,
  uninstallPlugin,
  cleanCache,
  getPluginInfo,
  listenToPluginEvents,
  listenToPluginEventsByName,
  listenToInstallProgress,
  addNotification,
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  updateNotification,
  deleteNotification,
  clearAllNotifications,
} from "./tauri-commands";

describe("tauri-commands", () => {
  beforeEach(() => {
    vi.mocked(invoke).mockReset();
    vi.mocked(listen).mockReset();
  });

  describe("Plugin Commands", () => {
    it("installPlugin calls invoke with correct params", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(installPlugin("python", "ccplugin-market", "user")).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("install_plugin", {
        pluginName: "python",
        marketplace: "ccplugin-market",
        scope: "user",
      });
    });

    it("installPlugin uses default marketplace and scope", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await installPlugin("python");

      expect(invoke).toHaveBeenCalledWith("install_plugin", {
        pluginName: "python",
        marketplace: "ccplugin-market",
        scope: "user",
      });
    });

    it("updatePlugin calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(updatePlugin("python")).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("update_plugin", { pluginName: "python" });
    });

    it("uninstallPlugin calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(uninstallPlugin("python")).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("uninstall_plugin", { pluginName: "python" });
    });

    it("cleanCache calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(cleanCache()).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("clean_cache");
    });

    it("getPluginInfo calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(getPluginInfo("python")).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("get_plugin_info", { pluginName: "python" });
    });

    it("handles errors in plugin commands", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Command failed"));

      await expect(installPlugin("python")).rejects.toThrow("Command failed");
    });
  });

  describe("Event Listening", () => {
    it("listenToPluginEvents calls listen and filters by event type", async () => {
      const unlisten = vi.fn();
      vi.mocked(listen).mockResolvedValueOnce(unlisten);
      const handler = vi.fn();

      const result = await listenToPluginEvents(handler, "plugin-install-progress");

      expect(listen).toHaveBeenCalledWith("plugin-event", expect.any(Function));
      expect(result).toBe(unlisten);
    });

    it("listenToPluginEvents passes all events when no filter", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      const handler = vi.fn();

      await listenToPluginEvents(handler);

      // Simulate Tauri event structure
      if (capturedHandler) {
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "python",
            data: {},
          },
        });
      }

      expect(handler).toHaveBeenCalledWith({
        event_type: "plugin-install-progress",
        plugin_name: "python",
        data: {},
      });
    });

    it("listenToPluginEvents filters events by type", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      const handler = vi.fn();

      await listenToPluginEvents(handler, "plugin-install-progress");

      if (capturedHandler) {
        // Matching event
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "python",
            data: {},
          },
        });
        // Non-matching event
        capturedHandler({
          payload: {
            event_type: "plugin-install-completed",
            plugin_name: "python",
            data: {},
          },
        });
      }

      expect(handler).toHaveBeenCalledTimes(1);
    });

    it("listenToPluginEventsByName filters by plugin name", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      const handler = vi.fn();

      await listenToPluginEventsByName("python", handler);

      if (capturedHandler) {
        // Matching plugin
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "python",
            data: {},
          },
        });
        // Non-matching plugin
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "git",
            data: {},
          },
        });
      }

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith({
        event_type: "plugin-install-progress",
        plugin_name: "python",
        data: {},
      });
    });

    it("listenToPluginEventsByName combines plugin and event filters", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      const handler = vi.fn();

      await listenToPluginEventsByName("python", handler, "plugin-install-progress");

      if (capturedHandler) {
        // Matching both
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "python",
            data: {},
          },
        });
        // Wrong event type
        capturedHandler({
          payload: {
            event_type: "plugin-install-completed",
            plugin_name: "python",
            data: {},
          },
        });
        // Wrong plugin
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "git",
            data: {},
          },
        });
      }

      expect(handler).toHaveBeenCalledTimes(1);
    });

    it("listenToInstallProgress is deprecated but works", async () => {
      const unlisten = vi.fn();
      let capturedHandler: ((event: any) => void) | undefined;
      vi.mocked(listen).mockImplementationOnce((_event, handler) => {
        capturedHandler = handler;
        return Promise.resolve(unlisten);
      });
      const callback = vi.fn();

      await listenToInstallProgress(callback);

      if (capturedHandler) {
        capturedHandler({
          payload: {
            event_type: "plugin-install-progress",
            plugin_name: "python",
            data: { status: "installing", progress: 50, message: "Installing..." },
          },
        });
      }

      expect(callback).toHaveBeenCalledWith({
        plugin_name: "python",
        status: "installing",
        progress: 50,
        message: "Installing...",
      });
    });
  });

  describe("Notification Commands", () => {
    it("addNotification calls invoke", async () => {
      const notification = {
        id: "test-id",
        type: "info" as const,
        title: "Test",
        message: "Test message",
        read: false,
        created_at: 123456,
        updated_at: 123456,
      };
      vi.mocked(invoke).mockResolvedValueOnce(notification);

      await expect(addNotification({
        type: "info",
        title: "Test",
        message: "Test message",
      })).resolves.toEqual(notification);
      expect(invoke).toHaveBeenCalledWith("add_notification", {
        type: "info",
        title: "Test",
        message: "Test message",
      });
    });

    it("getNotifications calls invoke", async () => {
      const notifications = [
        { id: "1", type: "info" as const, title: "Test", message: "Test", read: false, created_at: 1, updated_at: 1 },
      ];
      vi.mocked(invoke).mockResolvedValueOnce(notifications);

      await expect(getNotifications()).resolves.toEqual(notifications);
      expect(invoke).toHaveBeenCalledWith("get_notifications");
    });

    it("getUnreadCount calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(5);

      await expect(getUnreadCount()).resolves.toBe(5);
      expect(invoke).toHaveBeenCalledWith("get_unread_count");
    });

    it("markNotificationRead calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(true);

      await expect(markNotificationRead("test-id")).resolves.toBe(true);
      expect(invoke).toHaveBeenCalledWith("mark_notification_read", { id: "test-id" });
    });

    it("markAllNotificationsRead calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(markAllNotificationsRead()).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("mark_all_notifications_read");
    });

    it("updateNotification calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(true);

      await expect(updateNotification("test-id", "Updated message")).resolves.toBe(true);
      expect(invoke).toHaveBeenCalledWith("update_notification", {
        id: "test-id",
        message: "Updated message",
      });
    });

    it("deleteNotification calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(true);

      await expect(deleteNotification("test-id")).resolves.toBe(true);
      expect(invoke).toHaveBeenCalledWith("delete_notification", { id: "test-id" });
    });

    it("clearAllNotifications calls invoke", async () => {
      vi.mocked(invoke).mockResolvedValueOnce(undefined);

      await expect(clearAllNotifications()).resolves.toBeUndefined();
      expect(invoke).toHaveBeenCalledWith("clear_all_notifications");
    });

    it("handles notification errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Notification error"));

      await expect(getNotifications()).rejects.toThrow("Notification error");
    });
  });

  describe("Event Listen Errors", () => {
    it("handles listen errors", async () => {
      vi.mocked(listen).mockRejectedValueOnce(new Error("Listen failed"));

      await expect(listenToPluginEvents(vi.fn())).rejects.toThrow("Listen failed");
    });
  });
});
