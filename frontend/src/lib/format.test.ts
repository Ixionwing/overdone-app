import { describe, expect, it } from "vitest";

import { gaugeFillPercent } from "./format";

describe("gaugeFillPercent", () => {
  it("maps a value at the cap to 100", () => {
    expect(gaugeFillPercent(40, 40)).toBe(100);
  });

  it("maps a mid-range value proportionally", () => {
    expect(gaugeFillPercent(20, 40)).toBe(50);
  });

  it("clamps a negative value to 0 instead of filling from abs", () => {
    expect(gaugeFillPercent(-20, 40)).toBe(0);
  });

  it("clamps values above the cap to 100", () => {
    expect(gaugeFillPercent(80, 40)).toBe(100);
  });
});
