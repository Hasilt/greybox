export default function Toasts({ items }) {
  if (!items.length) return null;
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map((t) => (
        <div key={t.id} className={`toast ${t.kind}`}>
          <span className="t-label">{t.kind === 'err' ? 'failed' : 'done'}</span>
          {t.text}
        </div>
      ))}
    </div>
  );
}
