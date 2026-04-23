/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap, XIcon as X } from '@phosphor-icons/react';
import { API, useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';
import ToolTourButton from '../components/tour/ToolTourButton';
import ToolOutputPreview from '../components/tour/ToolOutputPreview';
import { TOOL_TOUR_IDS } from '../components/tour/tourDefinitions';

const ACTOR_TYPES = ['Legislators', 'Lobbyists', 'Corporations', 'Nonprofits'];
const METRIC_HELP = {
  bridgeRole: 'How much this actor connects otherwise separate parts of the current stakeholder map.',
  connectionReach: 'How many direct links this actor has inside the current stakeholder map.',
  strategicRelevance: 'A blended prioritization signal based on map position, estimated influence tier, and available evidence.',
  estimatedInfluenceTier: 'A qualitative estimate of likely influence on this issue based on the current map and available evidence.',
};

function formatMoney(value) {
  if (!value) return '—';
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? `$${parsed.toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—';
}

function formatTitle(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function Table({ columns, rows, emptyMessage = 'No rows to display.' }) {
  if (!rows.length) return <p className="text-slate-400">{emptyMessage}</p>;
  return (
    <div className="overflow-x-auto rounded-xl border border-white/10">
      <table className="w-full text-sm text-left text-slate-300">
        <thead className="text-slate-500 uppercase tracking-wider text-xs border-b border-white/10 bg-black/20">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="py-3 px-4 whitespace-nowrap">{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={row.id || row.key || rowIndex} className="border-b border-white/5 align-top">
              {columns.map((column) => (
                <td key={column.key} className="py-3 px-4 whitespace-pre-wrap">
                  {column.render ? column.render(row) : (row[column.key] || '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SummaryMetric({ label, value }) {
  return (
    <div className="rounded-xl bg-black/20 border border-white/10 px-4 py-4 min-h-[112px] flex flex-col justify-between">
      <div
        style={{
          color: '#64748b',
          fontSize: 12,
          lineHeight: 1.35,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          whiteSpace: 'normal',
          wordBreak: 'break-word',
        }}
      >
        {label}
      </div>
      <div style={{ color: '#fff', fontSize: 38, lineHeight: 1, marginTop: 14, fontWeight: 500 }}>
        {value}
      </div>
    </div>
  );
}

function InfoLabel({ label, help }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, position: 'relative', minWidth: 110 }}>
      <span>{label}</span>
      {help && (
        <>
          <button
            type="button"
            aria-label={`Explain ${label}`}
            onClick={() => setOpen((value) => !value)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 16,
              height: 16,
              borderRadius: '50%',
              border: '1px solid rgba(255,255,255,0.2)',
              color: '#94a3b8',
              background: open ? 'rgba(255,255,255,0.08)' : 'transparent',
              fontSize: 10,
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            i
          </button>
          {open && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 6px)',
                left: 0,
                zIndex: 20,
                width: 220,
                padding: '8px 10px',
                borderRadius: 8,
                border: '1px solid rgba(255,255,255,0.12)',
                background: '#11111b',
                color: '#cbd5e1',
                fontSize: 11,
                lineHeight: 1.45,
                textTransform: 'none',
                letterSpacing: 0,
                whiteSpace: 'normal',
                fontWeight: 400,
                boxShadow: '0 12px 30px rgba(0,0,0,0.35)',
              }}
            >
              {help}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function formatMetricValue(value) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed.toFixed(2) : '—';
}

function normalizeSourceTypeLabel(label) {
  const value = String(label || '').toLowerCase();
  if (value === 'structured source') return 'Structured source';
  if (value === 'web source') return 'Web source';
  if (value === 'inferred') return 'Inferred';
  if (value === 'seeded') return 'Seeded';
  return label || '—';
}

function SourceTypeBadges({ actor }) {
  const labels = (actor?.source_labels || actor?.source_types || []).map(normalizeSourceTypeLabel);
  if (!labels.length) return <span style={{ color: '#71717a', fontFamily: 'monospace', fontSize: 11 }}>—</span>;
  const palette = {
    'Structured source': { color: '#86efac', border: 'rgba(134,239,172,0.2)', bg: 'rgba(134,239,172,0.08)' },
    'Web source': { color: '#93c5fd', border: 'rgba(147,197,253,0.25)', bg: 'rgba(147,197,253,0.08)' },
    Inferred: { color: '#cbd5e1', border: 'rgba(203,213,225,0.2)', bg: 'rgba(203,213,225,0.08)' },
    Seeded: { color: '#fcd34d', border: 'rgba(252,211,77,0.25)', bg: 'rgba(252,211,77,0.08)' },
  };
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {labels.map((label) => {
        const token = palette[label] || palette.Inferred;
        return (
          <span key={label} style={{ fontFamily: 'monospace', fontSize: 11, color: token.color, background: token.bg, border: `1px solid ${token.border}`, borderRadius: 999, padding: '2px 8px' }}>
            {label}
          </span>
        );
      })}
    </div>
  );
}

function ScoreBar({ score }) {
  const pct = Math.min(100, Math.max(0, Number(score) || 0));
  const color = pct >= 60 ? '#f87171' : pct >= 35 ? '#fbbf24' : '#60a5fa';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: 74 }}>
      <div style={{ width: 50, height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 999, overflow: 'hidden', flexShrink: 0 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 10, color: '#94a3b8', minWidth: 18, textAlign: 'right' }}>{pct}</span>
    </div>
  );
}

function StanceDot({ stance }) {
  const colors = { proponent: '#4ade80', opponent: '#f87171', neutral: '#94a3b8', unknown: '#64748b' };
  return <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: colors[stance] || '#64748b', marginRight: 6, flexShrink: 0 }} />;
}

function ConfidenceBadge({ confidence }) {
  const palette = {
    confirmed: { color: '#86efac', border: 'rgba(134,239,172,0.25)', bg: 'rgba(134,239,172,0.08)' },
    likely: { color: '#93c5fd', border: 'rgba(147,197,253,0.25)', bg: 'rgba(147,197,253,0.08)' },
    possible: { color: '#fcd34d', border: 'rgba(252,211,77,0.25)', bg: 'rgba(252,211,77,0.08)' },
    unknown: { color: '#a1a1aa', border: 'rgba(161,161,170,0.25)', bg: 'rgba(161,161,170,0.08)' },
  };
  const token = palette[confidence] || palette.unknown;
  return (
    <span style={{ fontFamily: 'monospace', fontSize: 11, color: token.color, background: token.bg, border: `1px solid ${token.border}`, borderRadius: 999, padding: '2px 8px' }}>
      {confidence || 'unknown'}
    </span>
  );
}

function ActorModal({ actor, onClose }) {
  if (!actor) return null;
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          style={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16, padding: 28, maxWidth: 560, width: '100%', maxHeight: '80vh', overflowY: 'auto' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <StanceDot stance={actor.stance} />
                <h2 style={{ color: '#fff', fontWeight: 700, fontSize: 18 }}>{actor.name}</h2>
              </div>
              {actor.organization && actor.organization !== actor.name && (
                <div style={{ color: '#64748b', fontSize: 13 }}>{actor.organization}</div>
              )}
            </div>
            <button onClick={onClose} style={{ color: '#64748b', background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}><X size={20} /></button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 16 }}>
            {[
              ['Type', formatTitle(actor.stakeholder_type)],
              ['Stance', formatTitle(actor.stance)],
              ['Confidence', actor.confidence_label || 'unknown'],
              ['Estimated Influence Tier', formatTitle(actor.influence_tier)],
              ['Source Type', actor.source_summary || '—'],
              ['Source Backbone', actor.source || '—'],
              ['Strategic Relevance', actor.composite_score ?? '—'],
              ['LDA Spend', formatMoney(actor.lda_amount)],
            ].map(([lbl, val]) => (
              <div key={lbl} style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '8px 12px' }}>
                <div style={{ color: '#64748b', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>{lbl}</div>
                <div style={{ color: '#e2e8f0', fontSize: 13 }}>{val}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 16 }}>
            {[
              ['Bridge Role', formatMetricValue(actor.betweenness_centrality)],
              ['Connection Reach', formatMetricValue(actor.degree_centrality)],
              ['Community', `C${(actor.community_id ?? 0) + 1}`],
            ].map(([lbl, val]) => (
              <div key={lbl} style={{ background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.15)', borderRadius: 8, padding: '8px 12px' }}>
                <div style={{ color: '#a78bfa', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>{lbl}</div>
                <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>{val}</div>
              </div>
            ))}
          </div>

          {(actor.observed_evidence || actor.inferred_rationale || actor.evidence) && (
            <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '10px 14px', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 6 }}>
                <div style={{ color: '#64748b', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Evidence</div>
                <ConfidenceBadge confidence={actor.confidence_label} />
              </div>
              <div style={{ marginBottom: 8 }}>
                <SourceTypeBadges actor={actor} />
              </div>
              {actor.observed_evidence && <p style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Observed:</strong> {actor.observed_evidence}</p>}
              {actor.inferred_rationale && <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Inferred:</strong> {actor.inferred_rationale}</p>}
              {!actor.observed_evidence && !actor.inferred_rationale && <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6 }}>{actor.evidence}</p>}
            </div>
          )}

          {actor.bill_numbers?.length > 0 && (
            <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '10px 14px' }}>
              <div style={{ color: '#64748b', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Sponsored Bills</div>
              <p style={{ color: '#93c5fd', fontSize: 13 }}>{actor.bill_numbers.join(', ')}</p>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default function StakeholderMap() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('stakeholder_map');

  const [policyIssue, setPolicyIssue] = useState('');
  const [includeTypes, setIncludeTypes] = useState([...ACTOR_TYPES]);
  const [activeTab, setActiveTab] = useState('Network Analysis');
  const [llmModel, setLlmModel] = useState('ChangeAgent');
  const [selectedActor, setSelectedActor] = useState(null);

  const rd = job?.result_data;
  const analytics = rd?.analytics;
  const strategicAnalysis = rd?.strategic_analysis || {};
  const actors = rd?.actors || [];
  const relationships = rd?.relationships || [];
  const proponents = actors.filter((actor) => actor.stance === 'proponent');
  const opponents = actors.filter((actor) => actor.stance === 'opponent');
  const neutral = actors.filter((actor) => !['proponent', 'opponent'].includes(actor.stance));
  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  const ClickableName = ({ row }) => (
    <button
      onClick={() => setSelectedActor(row)}
      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', textAlign: 'left', color: '#c4b5fd', textDecoration: 'none' }}
      onMouseEnter={(e) => { e.currentTarget.style.textDecoration = 'underline'; }}
      onMouseLeave={(e) => { e.currentTarget.style.textDecoration = 'none'; }}
    >
      {row.name}
      {row.source === 'seeded' && <span title="Seeded actor added to fill likely gaps not captured in structured sources." style={{ marginLeft: 6, fontFamily: 'monospace', fontSize: 10, color: '#fbbf24', background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.25)', borderRadius: 4, padding: '1px 5px' }}>seeded</span>}
    </button>
  );

  const actorColumns = [
    { key: 'name', label: 'Name', render: (row) => <ClickableName row={row} /> },
    { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
    { key: 'confidence_label', label: 'Confidence', render: (row) => <ConfidenceBadge confidence={row.confidence_label} /> },
    { key: 'organization', label: 'Organization', render: (row) => row.organization || '—' },
    { key: 'influence_tier', label: <InfoLabel label="Estimated Influence Tier" help={METRIC_HELP.estimatedInfluenceTier} />, render: (row) => formatTitle(row.influence_tier) },
    { key: 'composite_score', label: <InfoLabel label="Strategic Relevance" help={METRIC_HELP.strategicRelevance} />, render: (row) => <ScoreBar score={row.composite_score} /> },
    { key: 'betweenness_centrality', label: <InfoLabel label="Bridge Role" help={METRIC_HELP.bridgeRole} />, render: (row) => formatMetricValue(row.betweenness_centrality) },
    { key: 'evidence', label: 'Evidence', render: (row) => row.observed_evidence || row.evidence || '—' },
    { key: 'lda_amount', label: 'LDA Amount ($)', render: (row) => formatMoney(row.lda_amount) },
  ];

  const allActorColumns = [
    { key: 'name', label: 'Name', render: (row) => <ClickableName row={row} /> },
    { key: 'source_summary', label: 'Source Type', render: (row) => <SourceTypeBadges actor={row} /> },
    { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
    { key: 'stance', label: 'Stance', render: (row) => <span style={{ display: 'flex', alignItems: 'center' }}><StanceDot stance={row.stance} />{formatTitle(row.stance)}</span> },
    { key: 'confidence_label', label: 'Confidence', render: (row) => <ConfidenceBadge confidence={row.confidence_label} /> },
    { key: 'influence_tier', label: <InfoLabel label="Estimated Influence Tier" help={METRIC_HELP.estimatedInfluenceTier} />, render: (row) => formatTitle(row.influence_tier) },
    { key: 'composite_score', label: <InfoLabel label="Strategic Relevance" help={METRIC_HELP.strategicRelevance} />, render: (row) => <ScoreBar score={row.composite_score} /> },
    { key: 'betweenness_centrality', label: <InfoLabel label="Bridge Role" help={METRIC_HELP.bridgeRole} />, render: (row) => formatMetricValue(row.betweenness_centrality) },
    { key: 'degree_centrality', label: <InfoLabel label="Connection Reach" help={METRIC_HELP.connectionReach} />, render: (row) => formatMetricValue(row.degree_centrality) },
    { key: 'community_id', label: 'Community', render: (row) => `C${(row.community_id ?? 0) + 1}` },
    { key: 'organization', label: 'Organization', render: (row) => row.organization || '—' },
    { key: 'lda_amount', label: 'LDA Amount ($)', render: (row) => formatMoney(row.lda_amount) },
  ];

  const toggleType = (type) => {
    setIncludeTypes((prev) => (
      prev.includes(type) ? prev.filter((item) => item !== type) : [...prev, type]
    ));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('policy_issue', policyIssue);
    payload.append('scope', 'federal');
    payload.append('state', 'US');
    payload.append('include_types', includeTypes.map((item) => item.toLowerCase()).join(','));
    payload.append('llm_model', llmModel);
    submitJob(payload);
  };

  const tabs = ['Network Analysis', 'Strategic Analysis', 'Proponents', 'Opponents', 'All Actors'];

  return (
    <motion.div data-testid="tool-page-stakeholder-map" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="app-page-shell app-page-shell-wide">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <h1 data-testid="page-title-stakeholder-map" className="app-page-title">Stakeholder Map</h1>
        <p className="app-page-intro">
          Discovers and classifies policy actors from lobbying filings, bill sponsorships, and supplemental web evidence, then returns an interactive graph and directional network analysis.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <ModelSelector value={llmModel} onChange={setLlmModel} />
          <div data-tour="tour-button-stakeholder-map"><ToolTourButton tourId={TOOL_TOUR_IDS.stakeholderMap} /></div>
        </div>
      </header>

      <ResearchPrototypeNote
        category="Stakeholder Mapping and Network Analysis"
        refs={['varone2017', 'digiacomo2025', 'bitonti2023']}
        message="This tool demonstrates how AI can support actor discovery, classification, and strategic interpretation around a policy issue. Network structure and stance inference help organize the landscape, but they do not replace human judgment about salience, coalition dynamics, or political context."
      />

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div>
            <label className="field-label">Policy Issue</label>
            <input data-testid="input-stakeholder-map-policy-issue" data-tour="stakeholder-map-issue" value={policyIssue} onChange={(event) => setPolicyIssue(event.target.value)}
              className="field" placeholder="e.g. artificial intelligence regulation" required />
          </div>
          <div data-tour="stakeholder-map-types">
            <label className="field-label">Actor Types To Include</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {ACTOR_TYPES.map((type) => (
                <label key={type} className="flex items-center gap-2 text-sm text-slate-300">
                  <input data-testid={`toggle-stakeholder-map-type-${type.toLowerCase()}`} type="checkbox" checked={includeTypes.includes(type)} onChange={() => toggleType(type)} className="accent-violet-500" />
                  <span>{type}</span>
                </label>
              ))}
            </div>
          </div>
          <button data-testid="submit-stakeholder-map" data-tour="stakeholder-map-submit" type="submit" disabled={loading || !policyIssue.trim()} className="btn-primary mt-auto">
            {loading ? <><SpinnerGap size={18} className="animate-spin" /> Building…</> : <>Build Stakeholder Map <ArrowRight size={18} /></>}
          </button>
        </div>

        <div data-tour="stakeholder-map-output" className="glass-card p-8 flex flex-col gap-5">
          {job ? (
            <div data-testid="status-stakeholder-map" className="rounded-xl border border-white/10 bg-black/20 p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs text-purple-300">{job.id.slice(0, 8).toUpperCase()}</span>
                <span className={job.status === 'completed' ? 'badge-complete' : job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>{job.status}</span>
              </div>
              <p className="text-slate-300 text-sm mb-4">{job.message}</p>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${job.progress || 0}%` }} />
              </div>
            </div>
          ) : (
            <ToolOutputPreview
              title="Output Preview"
              summary="This panel becomes the status and summary area for the map, then the full network analysis renders below."
              items={[
                { title: 'Status', copy: 'Build progress appears first so you know the network job is active.' },
                { title: 'Map summary', copy: 'Totals for actors, opponents, proponents, and relationships appear after completion.' },
                { title: 'Analysis views', copy: 'Tabs expose the network, strategic analysis, actor tables, and downloads.' },
              ]}
              downloads={['Graph artifact', 'JSON', 'Report files']}
            />
          )}

          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
            Additional verification needed. Check stakeholder positions, network relationships, and engagement priorities against source evidence before use.
          </div>

          {job?.status === 'completed' && rd && (
            <div className="grid grid-cols-2 xl:grid-cols-5 gap-4">
              <SummaryMetric label="Total Actors" value={actors.length} />
              <SummaryMetric label="Proponents" value={proponents.length} />
              <SummaryMetric label="Opponents" value={opponents.length} />
              <SummaryMetric label="Neutral / Unknown" value={neutral.length} />
              <SummaryMetric label="Relationships" value={relationships.length} />
            </div>
          )}
        </div>
      </form>

      {job?.status === 'completed' && rd && (
        <div data-tour="stakeholder-map-output" className="mt-10 space-y-6">
          <div className="flex flex-wrap gap-3">
            {tabs.map((tab) => (
              <button data-testid={`tab-stakeholder-map-${tab.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`} key={tab} onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg border text-sm ${activeTab === tab ? 'bg-violet-500/20 border-violet-400/40 text-violet-200' : 'bg-white/5 border-white/10 text-slate-300'}`}>
                {tab}
              </button>
            ))}
          </div>

          <div className="glass-card p-8">
            <div className="app-output-header">Stakeholder Map</div>
            {activeTab === 'Network Analysis' && (
              <div className="space-y-8 text-slate-300">
                {analytics ? (
                  <>
                    {rd?.methodology_note && (
                      <div className="rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-sm text-slate-300">
                        <strong className="text-slate-100">Methodology and limitations:</strong> {rd.methodology_note}
                      </div>
                    )}
                    {analytics.strategic_summary && (
                      <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">
                        {analytics.strategic_summary}
                      </div>
                    )}

                    {/* ── Engagement Priority ──────────────────────────────── */}
                    <section className="space-y-4">
                      <div>
                        <h3 className="app-subsection-title">Engagement Priority</h3>
                        <p className="text-sm text-slate-400 mt-1">
                          Ranked by influence tier then LDA spend. Focuses outreach on the actors who matter most.
                        </p>
                      </div>
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {[
                          { label: 'Top Opponents', color: '#f87171', rows: analytics.top_opponents, empty: 'No opponents identified.' },
                          { label: 'Top Proponents', color: '#4ade80', rows: analytics.top_proponents, empty: 'No proponents identified.' },
                          { label: 'Persuadables', color: '#94a3b8', rows: analytics.top_persuadables, empty: 'No persuadable actors identified.', note: 'Neutral/unknown actors with meaningful network position.' },
                        ].map(({ label, color, rows, empty, note }) => (
                          <div key={label} className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                              <h4 className="text-white text-sm font-semibold">{label}</h4>
                            </div>
                            {note && <p className="text-xs text-slate-500">{note}</p>}
                            <Table
                              columns={[
                                { key: 'name', label: 'Name', render: (row) => <ClickableName row={row} /> },
                                { key: 'composite_score', label: <InfoLabel label="Strategic Relevance" help={METRIC_HELP.strategicRelevance} />, render: (row) => <ScoreBar score={row.composite_score} /> },
                                { key: 'lda_amount', label: 'LDA', render: (row) => formatMoney(row.lda_amount) },
                              ]}
                              rows={rows || []}
                              emptyMessage={empty}
                            />
                          </div>
                        ))}
                      </div>
                    </section>

                    {/* ── Bridge Actors ────────────────────────────────────── */}
                    <section className="space-y-3">
                      <h3 className="app-subsection-title">Bridge Actors</h3>
                      <p className="text-sm text-slate-400">
                        {METRIC_HELP.bridgeRole}
                      </p>
                      {analytics.brokers?.length ? (
                        <Table
                          columns={[
                            { key: 'name', label: 'Name' },
                            { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
                            { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                            { key: 'betweenness_centrality', label: <InfoLabel label="Bridge Role" help={METRIC_HELP.bridgeRole} />, render: (row) => formatMetricValue(row.betweenness_centrality) },
                            { key: 'degree_centrality', label: <InfoLabel label="Connection Reach" help={METRIC_HELP.connectionReach} />, render: (row) => formatMetricValue(row.degree_centrality) },
                            { key: 'organization', label: 'Organization', render: (row) => row.organization || '—' },
                          ]}
                          rows={analytics.brokers}
                        />
                      ) : (
                        <p className="text-slate-400 text-sm">
                          {!analytics.has_edges
                            ? 'No relationships detected — Bridge Role requires at least one lobbying or co-sponsorship edge.'
                            : !analytics.has_both_sides
                              ? 'Bridge detection requires both proponent and opponent actors to be present.'
                              : 'No actors currently bridge the proponent and opponent coalitions directly.'}
                        </p>
                      )}
                    </section>

                    {/* ── Centrality Rankings ──────────────────────────────── */}
                    {analytics.has_edges && (
                      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="space-y-3">
                          <h3 className="app-subsection-title">Top by Bridge Role</h3>
                          <p className="text-sm text-slate-400">{METRIC_HELP.bridgeRole}</p>
                          <Table
                            columns={[
                              { key: 'name', label: 'Name' },
                              { key: 'betweenness_centrality', label: <InfoLabel label="Bridge Role" help={METRIC_HELP.bridgeRole} />, render: (row) => formatMetricValue(row.betweenness_centrality) },
                              { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                            ]}
                            rows={analytics.top_by_betweenness || []}
                          />
                        </div>
                        <div className="space-y-3">
                          <h3 className="app-subsection-title">Top by Connection Reach</h3>
                          <p className="text-sm text-slate-400">{METRIC_HELP.connectionReach}</p>
                          <Table
                            columns={[
                              { key: 'name', label: 'Name' },
                              { key: 'degree_centrality', label: <InfoLabel label="Connection Reach" help={METRIC_HELP.connectionReach} />, render: (row) => formatMetricValue(row.degree_centrality) },
                              { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                            ]}
                            rows={analytics.top_by_degree || []}
                          />
                        </div>
                      </section>
                    )}

                    {/* ── Network metrics ──────────────────────────────────── */}
                    <section className="space-y-4">
                      <h3 className="app-subsection-title">Network Metrics</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <SummaryMetric label="Network Density" value={Number(analytics.network_density || 0).toFixed(3)} />
                        <SummaryMetric label="Structural Communities" value={analytics.communities || 0} />
                        <SummaryMetric label="Bridge Actors" value={analytics.brokers?.length || 0} />
                        <SummaryMetric label="Multi-Venue Actors" value={analytics.multi_venue_actors?.length || 0} />
                      </div>
                    </section>

                    {/* ── Multi-Venue Actors ───────────────────────────────── */}
                    {analytics.multi_venue_actors?.length > 0 && (
                      <section className="space-y-3">
                        <h3 className="app-subsection-title">Multi-Venue Actors</h3>
                        <p className="text-sm text-slate-400">
                          Active in both administrative (LDA) and legislative (LegiScan) venues — consistent with higher-influence advocacy.
                        </p>
                        <Table
                          columns={[
                            { key: 'name', label: 'Name' },
                            { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
                            { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                            { key: 'lda_amount', label: 'LDA Amount', render: (row) => formatMoney(row.lda_amount) },
                            { key: 'bill_numbers', label: 'Bills', render: (row) => (row.bill_numbers || []).join(', ') || '—' },
                          ]}
                          rows={analytics.multi_venue_actors}
                        />
                      </section>
                    )}
                  </>
                ) : (
                  <p className="text-slate-400">Network analytics are not available for this run.</p>
                )}
              </div>
            )}

            {activeTab === 'Proponents' && (
              <div className="space-y-4">
                {rd.proponent_summary && (
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">{rd.proponent_summary}</div>
                )}
                <Table columns={actorColumns} rows={proponents} emptyMessage="No proponents identified for this issue." />
              </div>
            )}

            {activeTab === 'Opponents' && (
              <div className="space-y-4">
                {rd.opponent_summary && (
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">{rd.opponent_summary}</div>
                )}
                <Table columns={actorColumns} rows={opponents} emptyMessage="No opponents identified for this issue." />
              </div>
            )}

            {activeTab === 'All Actors' && (
              <div className="space-y-8">
                <Table columns={allActorColumns} rows={actors} />
                {relationships.length > 0 && (
                  <section className="space-y-3">
                    <h3 className="app-subsection-title">Relationships</h3>
                    <Table
                      columns={[
                        { key: 'from_name', label: 'From' },
                        { key: 'to_name', label: 'To' },
                        { key: 'relationship', label: 'Relationship' },
                        { key: 'label', label: 'Label' },
                        {
                          key: 'source', label: 'Source',
                          render: (row) => row.source === 'inferred'
                            ? <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#94a3b8', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.2)', borderRadius: 4, padding: '1px 6px' }}>inferred</span>
                            : <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#86efac', background: 'rgba(134,239,172,0.08)', border: '1px solid rgba(134,239,172,0.2)', borderRadius: 4, padding: '1px 6px' }}>data</span>,
                        },
                      ]}
                      rows={relationships.map((relationship, index) => ({
                        key: index,
                        from_name: actors.find((actor) => actor.id === relationship.from_id)?.name || relationship.from_id,
                        to_name: actors.find((actor) => actor.id === relationship.to_id)?.name || relationship.to_id,
                        relationship: formatTitle(String(relationship.type || '').replaceAll(' ', '_')),
                        label: relationship.label || '—',
                        source: relationship.source || 'data',
                      }))}
                    />
                  </section>
                )}
              </div>
            )}

            {activeTab === 'Strategic Analysis' && (
              <div className="space-y-6 text-slate-300">
                {Object.keys(strategicAnalysis).length === 0 ? (
                  <p className="text-slate-400">Strategic analysis not available for this run.</p>
                ) : (
                  <>
                    {/* Landscape + Dynamics */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                      {strategicAnalysis.landscape && (
                        <div style={{ background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 12, padding: '16px 20px' }}>
                          <div style={{ color: '#a78bfa', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 8 }}>Power Landscape</div>
                          <p style={{ color: '#e2e8f0', fontSize: 14, lineHeight: 1.65 }}>{strategicAnalysis.landscape}</p>
                        </div>
                      )}
                      {strategicAnalysis.dynamics && (
                        <div style={{ background: 'rgba(59,130,246,0.07)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 12, padding: '16px 20px' }}>
                          <div style={{ color: '#60a5fa', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 8 }}>Key Dynamics</div>
                          <p style={{ color: '#e2e8f0', fontSize: 14, lineHeight: 1.65 }}>{strategicAnalysis.dynamics}</p>
                        </div>
                      )}
                    </div>

                    {/* Immediate Actions */}
                    {strategicAnalysis.immediate_actions?.length > 0 && (
                      <section className="space-y-3">
                        <h3 className="app-subsection-title">Immediate Actions</h3>
                        <div className="space-y-2">
                          {strategicAnalysis.immediate_actions.map((action, i) => {
                            const actionText = typeof action === 'string'
                              ? action
                              : [action.actor, action.action, action.why].filter(Boolean).join(' — ');
                            const support = typeof action === 'object' ? (action.support || []) : [];
                            const metrics = typeof action === 'object' ? (action.metrics || []) : [];
                            const confidence = typeof action === 'object' ? action.confidence : '';
                            const parts = actionText.split(' — ');
                            return (
                              <div key={i} style={{ display: 'flex', gap: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '10px 14px', border: '1px solid rgba(255,255,255,0.06)' }}>
                                <span style={{ color: '#a78bfa', fontWeight: 700, fontSize: 13, minWidth: 18 }}>{i + 1}.</span>
                                <div>
                                  {parts.length >= 3 ? (
                                    <>
                                      <span style={{ color: '#c4b5fd', fontWeight: 600, fontSize: 13 }}>{parts[0]}</span>
                                      <span style={{ color: '#64748b', fontSize: 13 }}> — </span>
                                      <span style={{ color: '#e2e8f0', fontSize: 13 }}>{parts[1]}</span>
                                      <span style={{ color: '#64748b', fontSize: 13 }}> — </span>
                                      <span style={{ color: '#94a3b8', fontSize: 12 }}>{parts.slice(2).join(' — ')}</span>
                                    </>
                                  ) : (
                                    <span style={{ color: '#e2e8f0', fontSize: 13 }}>{actionText}</span>
                                  )}
                                  {(support.length > 0 || metrics.length > 0 || confidence) && (
                                    <div className="mt-2 space-y-1">
                                      {confidence && <ConfidenceBadge confidence={confidence} />}
                                      {support.length > 0 && (
                                        <div className="text-xs text-slate-400">
                                          Support: {support.join(' · ')}
                                        </div>
                                      )}
                                      {metrics.length > 0 && (
                                        <div className="text-xs text-slate-500">
                                          Metrics: {metrics.join(' · ')}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </section>
                    )}

                    {/* Coalition Opportunities + Risks */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                      {strategicAnalysis.coalition_opportunities?.length > 0 && (
                        <section className="space-y-3">
                          <h3 className="app-subsection-title">Coalition Opportunities</h3>
                          <ul className="space-y-2">
                            {strategicAnalysis.coalition_opportunities.map((opp, i) => {
                              const text = typeof opp === 'string' ? opp : opp.opportunity;
                              const support = typeof opp === 'object' ? (opp.support || []) : [];
                              const metrics = typeof opp === 'object' ? (opp.metrics || []) : [];
                              const confidence = typeof opp === 'object' ? opp.confidence : '';
                              return (
                                <li key={i} style={{ display: 'flex', gap: 10, color: '#4ade80', fontSize: 13, lineHeight: 1.55 }}>
                                  <span>→</span>
                                  <div>
                                    <div style={{ color: '#d1fae5' }}>{text}</div>
                                    {(support.length > 0 || metrics.length > 0 || confidence) && (
                                      <div className="mt-1 space-y-1">
                                        {confidence && <ConfidenceBadge confidence={confidence} />}
                                        {support.length > 0 && <div className="text-xs text-slate-400">Support: {support.join(' · ')}</div>}
                                        {metrics.length > 0 && <div className="text-xs text-slate-500">Metrics: {metrics.join(' · ')}</div>}
                                      </div>
                                    )}
                                  </div>
                                </li>
                              );
                            })}
                          </ul>
                        </section>
                      )}
                      {strategicAnalysis.risks?.length > 0 && (
                        <section className="space-y-3">
                          <h3 className="app-subsection-title">Risks</h3>
                          <ul className="space-y-2">
                            {strategicAnalysis.risks.map((risk, i) => {
                              const text = typeof risk === 'string' ? risk : risk.risk;
                              const support = typeof risk === 'object' ? (risk.support || []) : [];
                              const metrics = typeof risk === 'object' ? (risk.metrics || []) : [];
                              const confidence = typeof risk === 'object' ? risk.confidence : '';
                              return (
                                <li key={i} style={{ display: 'flex', gap: 10, fontSize: 13, lineHeight: 1.55 }}>
                                  <span style={{ color: '#f87171' }}>⚠</span>
                                  <div>
                                    <div style={{ color: '#fecaca' }}>{text}</div>
                                    {(support.length > 0 || metrics.length > 0 || confidence) && (
                                      <div className="mt-1 space-y-1">
                                        {confidence && <ConfidenceBadge confidence={confidence} />}
                                        {support.length > 0 && <div className="text-xs text-slate-400">Support: {support.join(' · ')}</div>}
                                        {metrics.length > 0 && <div className="text-xs text-slate-500">Metrics: {metrics.join(' · ')}</div>}
                                      </div>
                                    )}
                                  </div>
                                </li>
                              );
                            })}
                          </ul>
                        </section>
                      )}
                    </div>

                    {/* Swing actor strategy */}
                    {strategicAnalysis.swing_actor_strategy && (
                      <section>
                        <h3 className="app-subsection-title" style={{ marginBottom: 8 }}>Swing Actor Strategy</h3>
                        <p style={{ color: '#cbd5e1', fontSize: 14, lineHeight: 1.65 }}>
                          {typeof strategicAnalysis.swing_actor_strategy === 'string'
                            ? strategicAnalysis.swing_actor_strategy
                            : strategicAnalysis.swing_actor_strategy.summary}
                        </p>
                        {typeof strategicAnalysis.swing_actor_strategy === 'object' && (
                          <div className="mt-2 space-y-1">
                            {strategicAnalysis.swing_actor_strategy.confidence && <ConfidenceBadge confidence={strategicAnalysis.swing_actor_strategy.confidence} />}
                            {strategicAnalysis.swing_actor_strategy.support?.length > 0 && (
                              <div className="text-xs text-slate-400">Support: {strategicAnalysis.swing_actor_strategy.support.join(' · ')}</div>
                            )}
                            {strategicAnalysis.swing_actor_strategy.metrics?.length > 0 && (
                              <div className="text-xs text-slate-500">Metrics: {strategicAnalysis.swing_actor_strategy.metrics.join(' · ')}</div>
                            )}
                          </div>
                        )}
                      </section>
                    )}

                    {/* Issue context */}
                    {rd.issue_summary && (
                      <section style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16 }}>
                        <h3 className="app-subsection-title" style={{ marginBottom: 8 }}>Issue Overview</h3>
                        <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.65 }}>{rd.issue_summary}</p>
                      </section>
                    )}

                    {rd.key_coalitions?.length > 0 && (
                      <section>
                        <h3 className="app-subsection-title" style={{ marginBottom: 8 }}>Known Coalitions</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                          {rd.key_coalitions.map((c) => (
                            <span key={c} style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 6, padding: '3px 10px', fontSize: 12, color: '#a5b4fc' }}>{c}</span>
                          ))}
                        </div>
                      </section>
                    )}

                    <p className="text-xs text-slate-600">
                      Stance classifications are LLM-inferred from public data. Verify before strategic use. Network metrics follow Varone, Ingold &amp; Jourdain (2016).
                    </p>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button data-testid="download-stakeholder-map-xlsx" onClick={() => downloadArtifact(artifactMap['stakeholder_map.xlsx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
              <DownloadSimple size={18} /> Download XLSX
            </button>
            <button data-testid="download-stakeholder-map-docx" onClick={() => downloadArtifact(artifactMap['stakeholder_map.docx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download DOCX
            </button>
            <button data-testid="download-stakeholder-map-markdown" onClick={() => downloadText(job?.result_data?.markdown || '', 'stakeholder_map.md')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download Markdown
            </button>
            <button data-testid="download-stakeholder-map-json" onClick={() => downloadJson(rd || {}, 'stakeholder_map.json')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download JSON
            </button>
          </div>
        </div>
      )}
      <ActorModal actor={selectedActor} onClose={() => setSelectedActor(null)} />
    </motion.div>
  );
}
