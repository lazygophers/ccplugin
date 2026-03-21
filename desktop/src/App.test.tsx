import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

describe("App", () => {
  it("renders routes via RouterProvider", async () => {
    window.location.hash = "#/logs";
    const { default: App } = await import("./App");
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: "日志", level: 1 })
    ).toBeInTheDocument();
  });
});
