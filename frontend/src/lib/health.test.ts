import { describe, expect, it } from "vitest";

import { healthAlert } from "./health";

describe("healthAlert", () => {
  it("is silent when the API reports ok", () => {
    expect(healthAlert(null, { status: "ok" })).toBeNull();
  });

  it("tells the operator to start Postgres when the database is down", () => {
    expect(healthAlert("database unavailable", null)).toBe(
      "Database unreachable. Start Postgres, then refresh.",
    );
  });

  it("tells the operator to start the API for other failures", () => {
    expect(healthAlert("Failed to fetch", null)).toBe(
      "API unreachable. Start the API on port 8000, then refresh.",
    );
  });
});
