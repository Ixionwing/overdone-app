import { alert, col, mute, row } from "@/theme/layout";
import { healthAlert } from "@/lib/health";
import type { HealthStatus } from "@/lib/types";

type StatusBarProps = {
  health: HealthStatus | null;
  error: string | null;
};

export function StatusBar({ health, error }: StatusBarProps) {
  const message = healthAlert(error, health);

  if (message) {
    return (
      <p className={alert} role="alert">
        {message}
      </p>
    );
  }

  return (
    <section className={row} aria-label="System Status">
      <div className={col}>
        <p className={mute}>API</p>
        <p style={{ margin: 0 }}>Reachable</p>
      </div>
      <div className={col}>
        <p className={mute}>Database</p>
        <p style={{ margin: 0 }}>Reachable</p>
      </div>
    </section>
  );
}
