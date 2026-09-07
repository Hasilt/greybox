import { pct, clockTime } from '../format.js';

export default function RetrievalQuality({ runs }) {
  const current = runs.length ? runs[0] : null;
  const latest = current?.results ?? [];

  return (
    <>
      <div className="section-head">
        <span className="eyebrow">03 · Retrieval Quality</span>
        <p>
          Hit@5, MRR, Recall@5 and nDCG@5 from the golden question set. Run history is kept for
          this session only.
        </p>
      </div>

      <div className="grid cols-4">
        <div className="panel bignum">
          <span className="eyebrow">Hit@5</span>
          <div className={`value ${current ? '' : 'dim'}`}>
            {current ? pct(current.hit_at_5) : '—'}
          </div>
          <div className="foot num" style={{ color: 'var(--text-dim)' }}>
            {current ? `${current.hits} / ${current.total} questions` : 'no run yet'}
          </div>
        </div>
        <div className="panel bignum">
          <span className="eyebrow">MRR</span>
          <div className={`value ${current ? '' : 'dim'}`}>
            {current ? Number(current.mrr ?? 0).toFixed(3) : '—'}
          </div>
          <div className="foot num" style={{ color: 'var(--text-dim)' }}>
            mean reciprocal rank
          </div>
        </div>
        <div className="panel bignum">
          <span className="eyebrow">Recall@5</span>
          <div className={`value ${current ? '' : 'dim'}`}>
            {current ? pct(current.recall_at_5 ?? 0) : '—'}
          </div>
          <div className="foot num" style={{ color: 'var(--text-dim)' }}>
            relevant sources covered
          </div>
        </div>
        <div className="panel bignum">
          <span className="eyebrow">nDCG@5</span>
          <div className={`value ${current ? '' : 'dim'}`}>
            {current ? Number(current.ndcg_at_5 ?? 0).toFixed(3) : '—'}
          </div>
          <div className="foot num" style={{ color: 'var(--text-dim)' }}>
            ranking quality
          </div>
        </div>
      </div>

      <div className="panel">
        <span className="eyebrow">Evaluation runs · this session</span>
        <div className="table-wrap" style={{ marginTop: 12 }}>
          <table className="data">
            <thead>
              <tr>
                <th>Time</th>
                <th>Hit@5</th>
                <th>MRR</th>
                <th>Recall@5</th>
                <th>nDCG@5</th>
                <th>Hits / Total</th>
              </tr>
            </thead>
            <tbody>
              {runs.length ? (
                runs.map((r) => (
                  <tr key={r.ts}>
                    <td className="mono">{clockTime(r.ts)}</td>
                    <td className="mono">{pct(r.hit_at_5)}</td>
                    <td className="mono">{r.mrr != null ? Number(r.mrr).toFixed(3) : '—'}</td>
                    <td className="mono">
                      {r.recall_at_5 != null ? pct(r.recall_at_5) : '—'}
                    </td>
                    <td className="mono">
                      {r.ndcg_at_5 != null ? Number(r.ndcg_at_5).toFixed(3) : '—'}
                    </td>
                    <td className="mono">
                      {r.hits} / {r.total}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>
                    <div className="empty">run an evaluation to populate history</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {latest.length ? (
        <div className="panel">
          <span className="eyebrow">Latest run · per-question</span>
          <div className="table-wrap" style={{ marginTop: 12 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Result</th>
                  <th>RR</th>
                  <th>Recall</th>
                  <th>nDCG</th>
                  <th>Retrieved sources</th>
                </tr>
              </thead>
              <tbody>
                {latest.map((q, i) => (
                  <tr key={i}>
                    <td style={{ maxWidth: 420 }}>{q.question}</td>
                    <td>
                      <span className={q.hit ? 'tag-hit' : 'tag-miss'}>
                        {q.hit ? 'hit' : 'miss'}
                      </span>
                    </td>
                    <td className="mono">{(q.rr ?? 0).toFixed(2)}</td>
                    <td className="mono">{pct(q.recall ?? 0)}</td>
                    <td className="mono">{(q.ndcg ?? 0).toFixed(2)}</td>
                    <td>
                      <div className="src-list">
                        {(q.retrieved_sources ?? []).map((s, j) => (
                          <span key={j}>{s}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </>
  );
}
