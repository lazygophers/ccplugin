import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button, buttonVariants } from "./button";

describe("Button", () => {
  it("renders a button by default", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();

    render(<Button onClick={onClick}>Click</Button>);
    await user.click(screen.getByRole("button", { name: "Click" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("supports asChild rendering", () => {
    render(
      <Button asChild>
        <a href="#x">Link</a>
      </Button>
    );
    expect(screen.getByRole("link", { name: "Link" })).toBeInTheDocument();
  });

  it("buttonVariants returns classes for variants/sizes", () => {
    expect(buttonVariants({ variant: "default", size: "default" })).toContain("bg-primary");
    expect(buttonVariants({ variant: "outline", size: "sm" })).toContain("border");
    expect(buttonVariants({ variant: "ghost", size: "icon" })).toContain("h-9");
  });
});
