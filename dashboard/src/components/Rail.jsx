import HealthPill from './HealthPill.jsx';

export default function Rail({ tabs, active, onSelect, health, reachable }) {
  return (
    <aside className="rail">
      <div className="brand">
        <div className="brand-mark">greybox</div>
        <div className="brand-sub">retrieval reliability</div>
      </div>

      <nav className="rail-nav" aria-label="Sections">
        {tabs.map(([key, label], i) => (
          <button
            key={key}
            className={key === active ? 'active' : ''}
            onClick={() => onSelect(key)}
            aria-current={key === active ? 'page' : undefined}
          >
            <span className="idx num">{String(i + 1).padStart(2, '0')}</span>
            {label}
          </button>
        ))}
      </nav>

      <div className="rail-foot">
        <div className="eyebrow">System vitals</div>
        <HealthPill label="api" value={reachable ? health?.status ?? 'healthy' : 'unavailable'} />
        <HealthPill label="qdrant" value={health?.qdrant} />
        <HealthPill label="redis" value={health?.redis} />
      </div>
    </aside>
  );
}
