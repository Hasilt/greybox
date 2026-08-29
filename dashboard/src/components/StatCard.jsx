export default function StatCard({ label, value, pending, foot }) {
  return (
    <div className="panel stat">
      <span className="eyebrow">{label}</span>
      <div className={`value ${pending ? 'dim' : ''}`}>{value}</div>
      {foot ? <div className="foot">{foot}</div> : null}
    </div>
  );
}
