import { describe, expect, it } from "vitest";

import { parseEvaluationResult } from "./evaluate";

const factors = {
  volume_jump_pct: 10.8,
  axial_compression: 100,
  cns_index: 50,
  joint_vectors: { shoulder: 12 },
};

describe("parseEvaluationResult", () => {
  it("parses a halted payload", () => {
    expect(
      parseEvaluationResult({
        halted: {
          reason: "missing_exercise",
          message: "No history for Overhead Press.",
          exercise_name: "Overhead Press",
        },
        overall_light: null,
        items: [],
        session_factors: null,
        narrative: null,
        warnings: [],
      }),
    ).toMatchObject({
      halted: { reason: "missing_exercise" },
      overall_light: null,
      items: [],
      warnings: [],
    });
  });

  it("parses a scored payload", () => {
    const result = parseEvaluationResult({
      halted: null,
      overall_light: "yellow",
      items: [
        {
          exercise_id: "bench",
          exercise_name: "Bench Press",
          light: "yellow",
          factors,
          narrative: "Jump is noticeable.",
          catalog_source_id: "Barbell_Bench_Press_-_Medium_Grip",
        },
      ],
      session_factors: factors,
      narrative: "Session risk is yellow.",
      warnings: [
        {
          kind: "qualitative_note",
          message: "Note from log.",
          source_id: null,
        },
      ],
    });
    expect(result.overall_light).toBe("yellow");
    expect(result.items).toHaveLength(1);
    expect(result.warnings).toHaveLength(1);
    expect(result.session_factors?.volume_jump_pct).toBe(10.8);
  });

  it("defaults missing collections instead of throwing on render", () => {
    const result = parseEvaluationResult({
      halted: null,
      overall_light: "green",
    });
    expect(result.items).toEqual([]);
    expect(result.warnings).toEqual([]);
    expect(result.session_factors).toBeNull();
  });
});
