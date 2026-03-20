import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "./badge";

describe("Badge", () => {
  it("renders content", () => {
    render(<Badge>Hi</Badge>);
    expect(screen.getByText("Hi")).toBeInTheDocument();
  });
});

