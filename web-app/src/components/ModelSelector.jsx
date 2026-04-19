const MODELS = [
  { value: 'ChangeAgent', label: 'ChangeAgent' },
];

export default function ModelSelector({ value, onChange }) {
  return (
    <select
      data-testid="model-selector"
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        fontFamily: 'Inter', fontSize: 12,
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 8, color: '#A78BFA',
        padding: '4px 10px', cursor: 'pointer',
      }}
    >
      {MODELS.map(m => (
        <option key={m.value} value={m.value}>{m.label}</option>
      ))}
    </select>
  );
}
