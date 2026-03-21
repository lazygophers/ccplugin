import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";

vi.mock("@/services/plugin-service", () => ({
  PluginService: {
    install: vi.fn(),
    update: vi.fn(),
    uninstall: vi.fn(),
    clean: vi.fn(),
    getInfo: vi.fn(),
  },
}));

import { PluginService } from "@/services/plugin-service";
import { usePythonCommand } from "./usePythonCommand";

describe("usePythonCommand", () => {
  it("install updates progress/result on success", async () => {
    vi.mocked(PluginService.install).mockImplementationOnce(async (_name, _market, onProgress) => {
      onProgress?.({ plugin_name: "python", status: "downloading", progress: 10, message: "x" });
      return { success: true, stdout: "ok", stderr: "" };
    });

    const { result } = renderHook(() => usePythonCommand());

    await act(async () => {
      await result.current.install("python");
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.progress?.progress).toBe(10);
    expect(result.current.result).toEqual({ success: true, stdout: "ok", stderr: "" });
    expect(result.current.error).toBeNull();
  });

  it("install sets error when result unsuccessful", async () => {
    vi.mocked(PluginService.install).mockResolvedValueOnce({ success: false, stdout: "", stderr: "bad" });

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.install("python");
    });

    expect(result.current.result?.success).toBe(false);
    expect(result.current.error).toBe("bad");
  });

  it("install sets error when throws", async () => {
    vi.mocked(PluginService.install).mockRejectedValueOnce(new Error("boom"));

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.install("python");
    });

    expect(result.current.error).toBe("boom");
    expect(result.current.loading).toBe(false);
  });

  it("update sets error on unsuccessful result", async () => {
    vi.mocked(PluginService.update).mockResolvedValueOnce({ success: false, stdout: "", stderr: "" });

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.update("python");
    });

    expect(result.current.error).toBe("更新失败");
  });

  it("update sets result on success and captures progress", async () => {
    vi.mocked(PluginService.update).mockImplementationOnce(async (_name, onProgress) => {
      onProgress?.({ plugin_name: "python", status: "installing", progress: 50, message: "y" });
      return { success: true, stdout: "ok", stderr: "" };
    });

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.update("python");
    });

    expect(result.current.result?.success).toBe(true);
    expect(result.current.progress?.progress).toBe(50);
    expect(result.current.error).toBeNull();
  });

  it("update sets error on throw", async () => {
    vi.mocked(PluginService.update).mockRejectedValueOnce("nope");
    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.update("python");
    });
    expect(result.current.error).toBe("nope");
  });

  it("clean sets error on unsuccessful result", async () => {
    vi.mocked(PluginService.clean).mockResolvedValueOnce({ success: false, stdout: "", stderr: "" });

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.clean();
    });

    expect(result.current.error).toBe("清理失败");
  });

  it("clean sets result on success", async () => {
    vi.mocked(PluginService.clean).mockResolvedValueOnce({ success: true, stdout: "ok", stderr: "" });
    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.clean();
    });
    expect(result.current.result).toEqual({ success: true, stdout: "ok", stderr: "" });
    expect(result.current.error).toBeNull();
  });

  it("clean sets error on throw", async () => {
    vi.mocked(PluginService.clean).mockRejectedValueOnce(new Error("x"));
    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.clean();
    });
    expect(result.current.error).toBe("x");
  });

  it("getInfo sets error on throw", async () => {
    vi.mocked(PluginService.getInfo).mockRejectedValueOnce("nope");

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.getInfo("python");
    });

    expect(result.current.error).toBe("nope");
  });

  it("getInfo sets error on unsuccessful result", async () => {
    vi.mocked(PluginService.getInfo).mockResolvedValueOnce({ success: false, stdout: "", stderr: "" });
    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.getInfo("python");
    });
    expect(result.current.error).toBe("获取信息失败");
  });

  it("getInfo sets result on success", async () => {
    vi.mocked(PluginService.getInfo).mockResolvedValueOnce({ success: true, stdout: "info", stderr: "" });
    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.getInfo("python");
    });
    expect(result.current.result?.stdout).toBe("info");
    expect(result.current.error).toBeNull();
  });

  it("uninstall sets error on unsuccessful result", async () => {
    vi.mocked(PluginService.uninstall).mockResolvedValueOnce({ success: false, stdout: "", stderr: "" });

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.uninstall("python");
    });

    expect(result.current.error).toBe("卸载失败");
  });

  it("uninstall sets progress/result on success", async () => {
    vi.mocked(PluginService.uninstall).mockImplementationOnce(async (_name, onProgress) => {
      onProgress?.({ plugin_name: "python", status: "installing", progress: 33, message: "removing" });
      return { success: true, stdout: "ok", stderr: "" };
    });

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.uninstall("python");
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.progress?.progress).toBe(33);
    expect(result.current.result?.success).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("uninstall sets error on throw", async () => {
    vi.mocked(PluginService.uninstall).mockRejectedValueOnce("nope");

    const { result } = renderHook(() => usePythonCommand());
    await act(async () => {
      await result.current.uninstall("python");
    });

    expect(result.current.error).toBe("nope");
    expect(result.current.loading).toBe(false);
  });
});
