import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import DevTools from "./index";

describe("DevTools page", () => {
  it("renders content", () => {
    render(<DevTools />);
    expect(screen.getByText("开发工具")).toBeInTheDocument();
  });
});

