import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithRouter } from "@/test/render";
import Layout from ".";

function Child() {
  return <div>Child Page</div>;
}

describe("Layout", () => {
  it("renders sidebar/topbar and outlet", () => {
    renderWithRouter([
      {
        path: "/",
        element: <Layout />,
        children: [{ index: true, element: <Child /> }],
      },
    ]);

    expect(screen.getByText("Child Page")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "插件市场" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "清空搜索" })).not.toBeInTheDocument();
  });
});
