import { decimal } from '../format.js';

// Horizontal threshold meter — the console's signature readout.
// Scale runs 0 .. max, where max leaves headroom past both score and threshold.
export default function DriftMeter({ score, threshold, detected }) {
  const s = Number(score) || 0;
  const t = Number(threshold) || 0;
  const max = Math.max(t * 2, s * 1.25, 0.001);
  const fillPct = Math.min(100, (s / max) * 100);
  const thrPct = Math.min(100, (t / max) * 100);

  return (
    <div className="meter">
      <div className="meter-track">
        <div
          className={`meter-fill ${detected ? 'alert' : ''}`}
          style={{ width: `${fillPct}%` }}
        />
        {t > 0 && <div className="meter-threshold" style={{ left: `${thrPct}%` }} />}
      </div>
      <div className="meter-scale">
        <span>0.000</span>
        <span className="thr">thr {decimal(t)}</span>
        <span>{decimal(max)}</span>
      </div>
    </div>
  );
}
