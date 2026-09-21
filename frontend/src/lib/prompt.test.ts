import { describe, expect, it } from "vitest";

import { requirePrompt } from "./prompt";

describe("requirePrompt", () => {
  it("rejects whitespace-only prompts with a next step", () => {
    expect(() => requirePrompt("   ")).toThrow(
      "Enter a proposed increment, then try Evaluate Increment again.",
    );
  });

  it("returns the trimmed prompt", () => {
    expect(requirePrompt("  add 20 lb  ")).toBe("add 20 lb");
  });
});
