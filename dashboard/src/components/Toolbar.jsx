export default function Toolbar({ actions, busyKey }) {
  return (
    <div className="toolbar">
      {actions.map((a) => {
        const loading = busyKey === a.key;
        return (
          <button
            key={a.key}
            className={`btn ${a.primary ? 'primary' : ''}`}
            onClick={a.onClick}
            disabled={busyKey != null}
          >
            {loading ? <span className="spin" aria-hidden="true" /> : null}
            {loading ? a.runningLabel : a.label}
          </button>
        );
      })}
    </div>
  );
}
