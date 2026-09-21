import { describe, expect, it } from "vitest";

import { hasStoredBaseline, parseBaselineImport } from "./baseline";

describe("parseBaselineImport", () => {
  it("accepts a minimal object with preferred unit", () => {
    expect(parseBaselineImport({ preferred_unit: "kg" })).toEqual({
      preferred_unit: "kg",
      benchmarks: [],
      sessions: [],
    });
  });

  it("rejects unknown root fields", () => {
    expect(() => parseBaselineImport({ extra: true })).toThrow(
      "Unexpected field: extra",
    );
  });
});

describe("hasStoredBaseline", () => {
  it("is false when nothing has been saved", () => {
    expect(hasStoredBaseline(null)).toBe(false);
  });

  it("is false when counts are all zero", () => {
    expect(
      hasStoredBaseline({
        preferred_unit: "lb",
        benchmark_count: 0,
        session_count: 0,
        set_count: 0,
        baseline: { preferred_unit: "lb", benchmarks: [], sessions: [] },
      }),
    ).toBe(false);
  });

  it("is true when any session, benchmark, or set is stored", () => {
    expect(
      hasStoredBaseline({
        preferred_unit: "lb",
        benchmark_count: 0,
        session_count: 1,
        set_count: 0,
        baseline: { preferred_unit: "lb", benchmarks: [], sessions: [] },
      }),
    ).toBe(true);
  });
});
