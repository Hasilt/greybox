import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { ms, clockTime } from '../format.js';

const ACCENT = '#4fd0c5';

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div
      className="num"
      style={{
        background: '#10151c',
        border: '1px solid #232c38',
        borderRadius: 5,
        padding: '7px 10px',
        fontSize: 11,
        color: '#d4dce6',
      }}
    >
      <div style={{ color: '#5c6875' }}>#{p.i} · {p.clock}</div>
      <div>{ms(p.ms)} ms</div>
    </div>
  );
}

export default function Latency({ metrics }) {
  const lat = metrics?.latency;
  const recent = Array.isArray(metrics?.recent) ? metrics.recent : [];
  const data = recent
    .slice()
    .sort((a, b) => (a.ts ?? 0) - (b.ts ?? 0))
    .map((r, i) => ({
      i: i + 1,
      ms: Number(r.total_latency_ms),
      clock: r.ts ? clockTime(r.ts * 1000) : '—',
    }));

  return (
    <>
      <div className="section-head">
        <span className="eyebrow">02 · Latency</span>
        <p>End-to-end retrieval latency percentiles and the recent request window.</p>
      </div>

      <div className="grid cols-3">
        {[
          ['p50', lat?.p50],
          ['p95', lat?.p95],
          ['p99', lat?.p99],
        ].map(([k, v]) => (
          <div key={k} className="panel bignum">
            <span className="eyebrow">{k} latency</span>
            <div className="value">
              {ms(v)}
              <span className="unit">ms</span>
            </div>
          </div>
        ))}
      </div>

      <div className="panel pad-lg">
        <span className="eyebrow">Recent requests · total_latency_ms</span>
        <div className="chart-box" style={{ marginTop: 14 }}>
          {data.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 6, right: 12, bottom: 4, left: 0 }}>
                <CartesianGrid stroke="#1b222c" vertical={false} />
                <XAxis
                  dataKey="i"
                  stroke="#232c38"
                  tickLine={false}
                  tick={{ fill: '#5c6875' }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="#232c38"
                  tickLine={false}
                  tick={{ fill: '#5c6875' }}
                  width={44}
                  unit=""
                />
                <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#232c38' }} />
                <Line
                  type="monotone"
                  dataKey="ms"
                  stroke={ACCENT}
                  strokeWidth={1.75}
                  dot={false}
                  activeDot={{ r: 3, fill: ACCENT }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty">no recent requests reported</div>
          )}
        </div>
      </div>
    </>
  );
}
