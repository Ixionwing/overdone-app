import { css } from "@pigment-css/react";

import { lightLabel } from "@/lib/format";
import { tokens } from "@/theme/tokens";
import type { TrafficLight } from "@/lib/types";

const housing = css({
  display: "flex",
  flexDirection: "column",
  gap: 6,
  padding: "10px 8px",
  backgroundColor: tokens.housing,
  borderRadius: 2,
  width: 36,
  flexShrink: 0,
});

const lamp = css({
  width: 18,
  height: 18,
  borderRadius: "50%",
  margin: "0 auto",
  backgroundColor: tokens.lampOff,
  boxShadow: "inset 0 1px 2px rgb(0 0 0 / 0.45)",
});

const lampOn = css({
  boxShadow: "none",
});

const row = css({
  display: "flex",
  alignItems: "center",
  gap: 16,
  minWidth: 0,
});

const title = css({
  fontFamily: "var(--font-display), Tektur, sans-serif",
  fontSize: "1.75rem",
  letterSpacing: "0.04em",
  margin: 0,
  lineHeight: 1.1,
});

function lampColor(slot: TrafficLight, active: TrafficLight | null): string {
  if (slot !== active) {
    return tokens.lampOff;
  }
  if (slot === "green") {
    return tokens.go;
  }
  if (slot === "yellow") {
    return tokens.caution;
  }
  return tokens.halt;
}

type TrafficLampProps = {
  light: TrafficLight | null;
};

export function TrafficLamp({ light }: TrafficLampProps) {
  const label = light ? lightLabel(light) : "No Verdict";
  return (
    <div className={row}>
      <div className={housing} aria-hidden="true">
        {(["red", "yellow", "green"] as const).map((slot) => (
          <span
            key={slot}
            className={`${lamp} ${slot === light ? lampOn : ""}`}
            style={{ backgroundColor: lampColor(slot, light) }}
          />
        ))}
      </div>
      <p className={title}>{label}</p>
    </div>
  );
}
