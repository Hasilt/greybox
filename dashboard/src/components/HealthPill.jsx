const OK_VALUES = new Set(['healthy', 'ok', 'up']);

export default function HealthPill({ label, value }) {
  const known = value != null;
  const good = known && OK_VALUES.has(String(value).toLowerCase());
  const cls = !known ? '' : good ? 'ok' : 'bad';
  return (
    <div className={`pill ${cls}`}>
      <span className="dot" />
      <span className="label">{label}</span>
      <span className="state">{known ? value : 'unknown'}</span>
    </div>
  );
}
