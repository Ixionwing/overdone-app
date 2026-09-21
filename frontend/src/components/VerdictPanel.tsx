import { css } from "@pigment-css/react";

import { TrafficLamp } from "@/components/TrafficLamp";
import { gaugeFillPercent, lightLabel, numberFormat } from "@/lib/format";
import { col, displayHeading, mute, warning } from "@/theme/layout";
import { tokens } from "@/theme/tokens";
import type { EvaluationResult, FactorScores, TrafficLight } from "@/lib/types";

const track = css({
  height: 8,
  backgroundColor: tokens.track,
  overflow: "hidden",
});

const fill = css({
  height: "100%",
  backgroundColor: tokens.bar,
});

type VerdictPanelProps = {
  result: EvaluationResult | null;
};

function Gauges({ factors }: { factors: FactorScores }) {
  const joints = Object.entries(factors.joint_vectors);
  const rows: { label: string; value: number; cap: number; suffix?: string }[] =
    [
      {
        label: "Volume Jump",
        value: factors.volume_jump_pct,
        cap: 40,
        suffix: "%",
      },
      {
        label: "Axial Compression",
        value: factors.axial_compression,
        cap: 2000,
      },
      { label: "CNS Index", value: factors.cns_index, cap: 2000 },
      ...joints.map(([name, value]) => ({
        label: `Joint ${name}`,
        value,
        cap: 2000,
      })),
    ];

  return (
    <div className={col}>
      {rows.map((row) => {
        const shown = `${numberFormat.format(row.value)}${row.suffix ?? ""}`;
        const width = `${gaugeFillPercent(row.value, row.cap)}%`;
        return (
          <div key={row.label}>
            <p style={{ margin: "0 0 4px" }}>
              {row.label} <span className="tabular">{shown}</span>
            </p>
            <div
              className={track}
              role="meter"
              aria-label={row.label}
              aria-valuemin={0}
              aria-valuemax={row.cap}
              aria-valuenow={Math.max(0, row.value)}
              aria-valuetext={shown}
            >
              <div className={fill} style={{ width }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ItemLight({ light }: { light: TrafficLight }) {
  const color =
    light === "green"
      ? tokens.go
      : light === "yellow"
        ? tokens.caution
        : tokens.halt;
  return (
    <span
      style={{
        display: "inline-block",
        width: 10,
        height: 10,
        borderRadius: "50%",
        backgroundColor: color,
        marginRight: 8,
        verticalAlign: "middle",
      }}
      aria-hidden="true"
    />
  );
}

export function VerdictPanel({ result }: VerdictPanelProps) {
  if (!result) {
    return (
      <section className={col} aria-label="Verdict">
        <h2 className={displayHeading}>Verdict</h2>
        <TrafficLamp light={null} />
        <p className={mute}>
          Evaluate a proposed increment to see whether it is overdone.
        </p>
      </section>
    );
  }

  if (result.halted) {
    return (
      <section className={col} aria-label="Verdict" aria-live="polite">
        <h2 className={displayHeading}>Needs Clarification</h2>
        <p className={warning} role="status">
          {result.halted.message} Add the missing detail, then try Evaluate
          Increment again.
        </p>
        <p className={mute} translate="no">
          Reason: {result.halted.reason}
        </p>
      </section>
    );
  }

  const light = result.overall_light;
  return (
    <section className={col} aria-label="Verdict" aria-live="polite">
      <h2 className={displayHeading}>Verdict</h2>
      <TrafficLamp light={light} />
      {result.narrative ? (
        <p style={{ margin: 0 }}>{result.narrative}</p>
      ) : null}
      {result.items.length > 0 ? (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, minWidth: 0 }}>
          {result.items.map((item) => (
            <li
              key={item.exercise_id}
              style={{
                padding: "6px 0",
                minWidth: 0,
                overflowWrap: "anywhere",
              }}
            >
              <ItemLight light={item.light} />
              {lightLabel(item.light)} {item.exercise_name}
              {item.catalog_source_id ? (
                <span
                  className={mute}
                  style={{ display: "block" }}
                  translate="no"
                >
                  {item.catalog_source_id}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      {result.session_factors ? (
        <Gauges factors={result.session_factors} />
      ) : null}
      {result.warnings.map((flag) => (
        <p className={warning} key={`${flag.kind}:${flag.message}`} role="note">
          {flag.message}
        </p>
      ))}
    </section>
  );
}
