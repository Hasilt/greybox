// Thin fetch layer for the greybox backend. All endpoints return JSON.
// Requests are relative; Vite proxies /api and /health to the backend.

async function json(res) {
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const get = (path) => fetch(path, { headers: { accept: 'application/json' } }).then(json);
const post = (path) =>
  fetch(path, { method: 'POST', headers: { accept: 'application/json' } }).then(json);

export const getHealth = () => get('/health');
export const getMetrics = () => get('/api/metrics');
export const getDrift = () => get('/api/drift');

export const runEvaluation = () => post('/api/evaluation/run');
export const checkDrift = () => post('/api/drift/check');
export const simulateDrift = () => post('/api/drift/simulate');
export const reindex = () => post('/api/ingest');
