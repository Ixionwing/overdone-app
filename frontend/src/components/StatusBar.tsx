import type { HealthStatus } from "@/lib/types";

type StatusBarProps = {
  health: HealthStatus | null;
  error: string | null;
};

export function StatusBar({ health, error }: StatusBarProps) {
  const apiOk = health?.status === "ok";

  return (
    <section aria-label="System status">
      <p>
        <strong>API:</strong> {apiOk ? "reachable" : "unreachable"}
      </p>
      <p>
        <strong>Health payload:</strong>{" "}
        {error ? error : JSON.stringify(health)}
      </p>
      <p>
        <strong>Database:</strong> {apiOk ? "reachable" : "unreachable"}
      </p>
    </section>
  );
}
