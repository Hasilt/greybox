import DriftMeter from './DriftMeter.jsx';
import { decimal } from '../format.js';

export default function Drift({ drift, lastResult }) {
  const detected = !!drift?.drift_detected;

  return (
    <>
      <div className="section-head">
        <span className="eyebrow">04 · Drift</span>
        <p>Embedding drift of live traffic against the indexed baseline distribution.</p>
      </div>

      <div className="panel pad-lg">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div className="bignum">
            <span className="eyebrow">Drift score</span>
            <div className={`value ${drift ? '' : 'dim'}`}>{decimal(drift?.drift_score)}</div>
          </div>
          {drift ? (
            <span className={`badge ${detected ? 'alert' : 'ok'}`}>
              <span className="dot" />
              {detected ? 'drift detected' : 'ok'}
            </span>
          ) : null}
        </div>

        {drift ? (
          <div style={{ marginTop: 18 }}>
            <DriftMeter
              score={drift.drift_score}
              threshold={drift.threshold}
              detected={detected}
            />
          </div>
        ) : null}

        <div className="kv" style={{ marginTop: 18 }}>
          <div>
            <span className="k">Threshold</span>
            <span className="v">{decimal(drift?.threshold)}</span>
          </div>
          <div>
            <span className="k">Baseline</span>
            <span className="v">{drift ? (drift.baseline ? 'present' : 'missing') : '—'}</span>
          </div>
          <div>
            <span className="k">Status</span>
            <span className="v">{drift ? (detected ? 'ALERT' : 'NOMINAL') : '—'}</span>
          </div>
        </div>
      </div>

      <div className="panel">
        <span className="eyebrow">Last action</span>
        <div
          className="num"
          style={{ marginTop: 10, fontSize: 12.5, color: 'var(--text-dim)' }}
        >
          {lastResult || 'No action run yet. Use the toolbar above to run an evaluation, check or simulate drift, or re-index.'}
        </div>
      </div>
    </>
  );
}
