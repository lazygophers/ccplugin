import { describe, it, expect, vi } from "vitest";
import { ProxyService } from "./proxy-service";
import { invoke } from "@tauri-apps/api/core";

describe("ProxyService", () => {
  it("save calls save_proxy_config with config", async () => {
    const config = {
      enabled: true,
      http: "http://127.0.0.1:7890",
      https: "http://127.0.0.1:7890",
      noProxy: "localhost,127.0.0.1",
    };
    vi.mocked(invoke).mockResolvedValueOnce(undefined);

    await expect(ProxyService.save(config)).resolves.toBeUndefined();
    expect(invoke).toHaveBeenCalledWith("save_proxy_config", { config });
  });

  it("load calls load_proxy_config and returns config", async () => {
    const config = {
      enabled: false,
      http: "",
      https: "",
      noProxy: "localhost,127.0.0.1",
    };
    vi.mocked(invoke).mockResolvedValueOnce(config);

    await expect(ProxyService.load()).resolves.toEqual(config);
    expect(invoke).toHaveBeenCalledWith("load_proxy_config");
  });

  it("load handles errors", async () => {
    vi.mocked(invoke).mockRejectedValueOnce(new Error("Failed to load"));

    await expect(ProxyService.load()).rejects.toThrow("Failed to load");
  });
});
