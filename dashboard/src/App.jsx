import { useCallback, useEffect, useRef, useState } from 'react';
import * as api from './api.js';
import Rail from './components/Rail.jsx';
import Toolbar from './components/Toolbar.jsx';
import Toasts from './components/Toasts.jsx';
import Overview from './components/Overview.jsx';
import Latency from './components/Latency.jsx';
import RetrievalQuality from './components/RetrievalQuality.jsx';
import Drift from './components/Drift.jsx';
import { clockTime } from './format.js';

const TABS = [
  ['overview', 'Overview'],
  ['latency', 'Latency'],
  ['quality', 'Retrieval Quality'],
  ['drift', 'Drift'],
];

const POLL_MS = 5000;

export default function App() {
  const [tab, setTab] = useState('overview');

  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [drift, setDrift] = useState(null);
  const [reachable, setReachable] = useState(true);
  const [updatedAt, setUpdatedAt] = useState(null);

  const [evalRuns, setEvalRuns] = useState([]);
  const [busyKey, setBusyKey] = useState(null);
  const [lastActionText, setLastActionText] = useState('');

  const [toasts, setToasts] = useState([]);
  const toastSeq = useRef(0);

  const pushToast = useCallback((kind, text) => {
    const id = ++toastSeq.current;
    setToasts((list) => [...list, { id, kind, text }]);
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 6000);
  }, []);

  const refresh = useCallback(async () => {
    const [h, m, d] = await Promise.allSettled([
      api.getHealth(),
      api.getMetrics(),
      api.getDrift(),
    ]);
    const anyOk = [h, m, d].some((r) => r.status === 'fulfilled');
    setReachable(anyOk);
    if (h.status === 'fulfilled') setHealth(h.value);
    if (m.status === 'fulfilled') setMetrics(m.value);
    if (d.status === 'fulfilled') setDrift(d.value);
    if (anyOk) setUpdatedAt(Date.now());
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const hitAt5 = evalRuns.length ? evalRuns[0].hit_at_5 : null;

  const runAction = useCallback(
    async (key, fn, describe) => {
      setBusyKey(key);
      try {
        const res = await fn();
        const text = describe(res);
        pushToast('ok', text);
        setLastActionText(`${clockTime(Date.now())} · ${text}`);
        if (key === 'eval') {
          setEvalRuns((list) => [
            {
              ts: Date.now(),
              hit_at_5: res.hit_at_5,
              hits: res.hits,
              total: res.total_questions,
              results: Array.isArray(res.results) ? res.results : [],
            },
            ...list,
          ]);
        }
        await refresh();
      } catch (e) {
        const text = `${key} request failed (${e.message})`;
        pushToast('err', text);
        setLastActionText(`${clockTime(Date.now())} · ${text}`);
      } finally {
        setBusyKey(null);
      }
    },
    [pushToast, refresh]
  );

  const actions = [
    {
      key: 'eval',
      label: 'Run Evaluation',
      runningLabel: 'Running…',
      primary: true,
      onClick: () =>
        runAction('eval', api.runEvaluation, (r) =>
          `Evaluation complete · Hit@5 ${(r.hit_at_5 * 100).toFixed(1)}% (${r.hits}/${r.total_questions})`
        ),
    },
    {
      key: 'check',
      label: 'Check Drift',
      runningLabel: 'Checking…',
      onClick: () =>
        runAction('check', api.checkDrift, (r) =>
          `Drift check · score ${Number(r.drift_score).toFixed(3)} · ${
            r.action === 'reindex_triggered' ? 'reindex triggered' : 'no action'
          }`
        ),
    },
    {
      key: 'simulate',
      label: 'Simulate Drift',
      runningLabel: 'Simulating…',
      onClick: () =>
        runAction('simulate', api.simulateDrift, (r) =>
          `Simulated drift · +${r.chunks_added} chunks from ${r.file}`
        ),
    },
    {
      key: 'reindex',
      label: 'Re-index',
      runningLabel: 'Indexing…',
      onClick: () =>
        runAction('reindex', api.reindex, (r) =>
          `Re-index complete · ${r.documents_processed} docs · ${r.chunks_created} chunks → ${r.collection}`
        ),
    },
  ];

  const titles = {
    overview: 'Overview',
    latency: 'Latency',
    quality: 'Retrieval Quality',
    drift: 'Drift',
  };

  return (
    <div className="app">
      <Rail
        tabs={TABS}
        active={tab}
        onSelect={setTab}
        health={health}
        reachable={reachable}
      />

      <div className="main">
        <div className="topbar">
          <h1>{titles[tab]}</h1>
          <span className="updated">
            <span className="beat" aria-hidden="true" />
            {updatedAt ? `updated ${clockTime(updatedAt)}` : 'connecting…'}
          </span>
          <Toolbar actions={actions} busyKey={busyKey} />
        </div>

        {!reachable ? (
          <div className="banner" role="alert">
            <span className="dot" />
            Backend unreachable — showing last known values. Retrying every 5s.
          </div>
        ) : null}

        <div className="content">
          {tab === 'overview' && (
            <Overview metrics={metrics} drift={drift} hitAt5={hitAt5} />
          )}
          {tab === 'latency' && <Latency metrics={metrics} />}
          {tab === 'quality' && <RetrievalQuality runs={evalRuns} />}
          {tab === 'drift' && <Drift drift={drift} lastResult={lastActionText} />}
        </div>
      </div>

      <Toasts items={toasts} />
    </div>
  );
}
