import StatCard from './StatCard.jsx';
import DriftMeter from './DriftMeter.jsx';
import { int, pct, decimal } from '../format.js';

export default function Overview({ metrics, drift, hitAt5 }) {
  const evalPending = hitAt5 == null;
  const driftPending = drift == null;

  return (
    <>
      <div className="section-head">
        <span className="eyebrow">01 · Overview</span>
        <p>Retrieval health at a glance. Metrics and drift refresh every 5 seconds.</p>
      </div>

      <div className="grid cols-4">
        <StatCard
          label="Total Queries"
          value={int(metrics?.total_queries)}
          pending={metrics == null}
          foot={
            metrics ? (
              <>
                <span className="accent">{int(metrics.cache_hits)}</span> cached ·{' '}
                {int(metrics.cache_misses)} miss
              </>
            ) : null
          }
        />
        <StatCard
          label="Hit@5"
          value={evalPending ? '—' : pct(hitAt5)}
          pending={evalPending}
          foot={evalPending ? 'run an evaluation' : 'last session run'}
        />
        <StatCard
          label="Cache Hit Rate"
          value={pct(metrics?.cache_hit_rate)}
          pending={metrics == null}
          foot={metrics ? 'hits / total lookups' : null}
        />
        <StatCard
          label="Drift Score"
          value={decimal(drift?.drift_score)}
          pending={driftPending}
          foot={
            drift ? (
              <span className={drift.drift_detected ? 'bad' : 'accent'}>
                {drift.drift_detected ? 'over threshold' : 'within threshold'} · thr{' '}
                {decimal(drift.threshold)}
              </span>
            ) : null
          }
        />
      </div>

      {drift ? (
        <div className="panel pad-lg">
          <span className="eyebrow">Embedding drift vs. baseline</span>
          <div style={{ marginTop: 14 }}>
            <DriftMeter
              score={drift.drift_score}
              threshold={drift.threshold}
              detected={drift.drift_detected}
            />
          </div>
        </div>
      ) : null}
    </>
  );
}
