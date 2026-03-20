import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./dialog";

function ControlledDialog() {
  const [open, setOpen] = useState(true);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Title</DialogTitle>
          <DialogDescription>Desc</DialogDescription>
        </DialogHeader>
        <div>Body</div>
        <DialogFooter>
          <button type="button">Footer</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

describe("Dialog", () => {
  it("renders content when open and closes via close button", async () => {
    const user = userEvent.setup();
    render(<ControlledDialog />);

    expect(screen.getByText("Body")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByText("Body")).not.toBeInTheDocument();
  });

  it("overlay exists", () => {
    render(<ControlledDialog />);
    // Overlay has no role; assert via fixed class
    const overlay = document.querySelector(".fixed.inset-0");
    expect(overlay).toBeTruthy();
  });
});
