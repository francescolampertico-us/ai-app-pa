export default function ResearchPrototypeNote({ category, message, secondaryLabel = 'Review Required' }) {
  return (
    <div
      className="mb-8 rounded-2xl border border-white/10 p-5"
      style={{ background: 'rgba(255,255,255,0.03)' }}
    >
      <div className="flex flex-wrap gap-2 mb-3">
        <span
          className="px-3 py-1 rounded-full text-[11px] uppercase tracking-[0.18em]"
          style={{ color: '#c4b5fd', background: 'rgba(109,40,217,0.18)', border: '1px solid rgba(109,40,217,0.28)' }}
        >
          {category}
        </span>
        <span
          className="px-3 py-1 rounded-full text-[11px] uppercase tracking-[0.18em]"
          style={{ color: '#f8fafc', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)' }}
        >
          {secondaryLabel}
        </span>
      </div>
      <p style={{ fontFamily: 'Inter', fontSize: 13.5, color: '#a1a1aa', lineHeight: 1.7, fontWeight: 300 }}>
        {message}
      </p>
    </div>
  );
}
