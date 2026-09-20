import type { EvaluationResult, FactorScores, TrafficLight } from "@/lib/types";

type VerdictPanelProps = {
  result: EvaluationResult;
};

function lightClass(light: TrafficLight): string {
  return `light light-${light}`;
}

function barWidth(value: number, cap: number): string {
  const pct = Math.min(100, Math.max(0, (Math.abs(value) / cap) * 100));
  return `${pct}%`;
}

function Gauges({ factors }: { factors: FactorScores }) {
  const joints = Object.entries(factors.joint_vectors);
  return (
    <div className="gauges">
      <div className="gauge">
        <p>Volume jump {factors.volume_jump_pct.toFixed(1)}%</p>
        <div className="gauge-track">
          <div
            className="gauge-fill"
            style={{ width: barWidth(factors.volume_jump_pct, 40) }}
          />
        </div>
      </div>
      <div className="gauge">
        <p>Axial compression {factors.axial_compression.toFixed(1)}</p>
        <div className="gauge-track">
          <div
            className="gauge-fill"
            style={{ width: barWidth(factors.axial_compression, 2000) }}
          />
        </div>
      </div>
      <div className="gauge">
        <p>CNS index {factors.cns_index.toFixed(1)}</p>
        <div className="gauge-track">
          <div
            className="gauge-fill"
            style={{ width: barWidth(factors.cns_index, 2000) }}
          />
        </div>
      </div>
      {joints.map(([name, value]) => (
        <div className="gauge" key={name}>
          <p>
            Joint {name} {value.toFixed(1)}
          </p>
          <div className="gauge-track">
            <div
              className="gauge-fill"
              style={{ width: barWidth(value, 2000) }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function VerdictPanel({ result }: VerdictPanelProps) {
  if (result.halted) {
    return (
      <div className="verdict" aria-live="polite">
        <h3>Needs clarification</h3>
        <p role="status">{result.halted.message}</p>
        <p>Reason: {result.halted.reason}</p>
      </div>
    );
  }

  const light = result.overall_light;
  return (
    <div className="verdict" aria-live="polite">
      <h3>Verdict</h3>
      {light ? (
        <p>
          Overall: <span className={lightClass(light)}>{light}</span>
        </p>
      ) : null}
      {result.narrative ? <p>{result.narrative}</p> : null}
      <ul className="item-verdicts">
        {result.items.map((item) => (
          <li key={item.exercise_id}>
            <span className={lightClass(item.light)}>{item.light}</span>{" "}
            {item.exercise_name}
            {item.catalog_source_id ? (
              <span className="citation"> {item.catalog_source_id}</span>
            ) : null}
          </li>
        ))}
      </ul>
      {result.session_factors ? (
        <Gauges factors={result.session_factors} />
      ) : null}
      {result.warnings.map((flag) => (
        <p className="banner" key={`${flag.kind}:${flag.message}`} role="note">
          {flag.message}
        </p>
      ))}
    </div>
  );
}
