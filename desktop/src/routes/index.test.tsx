import { describe, it, expect } from "vitest";
import { router } from "./index";

describe("router", () => {
  it("defines root route", () => {
    expect(router).toBeTruthy();
  });
});

