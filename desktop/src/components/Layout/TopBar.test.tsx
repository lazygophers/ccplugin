import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import TopBar from "./TopBar";

function renderTopBar(pathname = "/") {
  const router = createMemoryRouter(
    [
      {
        path: "*",
        element: <TopBar />,
      },
      {
        path: "/marketplace",
        element: <TopBar />,
      },
    ],
    { initialEntries: [pathname] }
  );
  return { router, ...render(<RouterProvider router={router} />) };
}

describe("TopBar", () => {
  it("shows title based on route", () => {
    renderTopBar("/settings");
    expect(screen.getByText("设置")).toBeInTheDocument();
  });

  it("shows default title for unknown route", () => {
    renderTopBar("/unknown");
    expect(screen.getByText("CCPlugin Desktop")).toBeInTheDocument();
  });

  it("navigates to marketplace on Enter", async () => {
    const user = userEvent.setup();
    const { router } = renderTopBar("/");

    const input = screen.getByRole("textbox", { name: "搜索插件" });
    await user.type(input, "python{enter}");
    expect(router.state.location.pathname).toBe("/marketplace");
    expect(router.state.location.search).toBe("?q=python");
  });

  it("shows clear button and clears query", async () => {
    const user = userEvent.setup();
    renderTopBar("/marketplace?q=git");
    expect(screen.getByRole("button", { name: "清空搜索" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "清空搜索" }));
    expect(screen.getByRole("textbox", { name: "搜索插件" })).toHaveValue("");
  });

  it("clear button does not navigate when not on marketplace", async () => {
    const user = userEvent.setup();
    const { router } = renderTopBar("/");
    const input = screen.getByRole("textbox", { name: "搜索插件" });
    await user.type(input, "git");
    await user.click(screen.getByRole("button", { name: "清空搜索" }));
    expect(router.state.location.pathname).toBe("/");
  });
});
