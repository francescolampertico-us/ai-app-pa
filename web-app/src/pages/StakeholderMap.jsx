/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { API, useFastApiJob } from '../hooks/useFastApiJob';

const ACTOR_TYPES = ['Legislators', 'Lobbyists', 'Corporations', 'Nonprofits'];

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
    <div className="rounded-xl bg-black/20 border border-white/10 px-4 py-3">
      <div className="text-slate-500 text-xs uppercase tracking-wider">{label}</div>
      <div className="text-white text-2xl mt-1">{value}</div>
    </div>
  );
}

export default function StakeholderMap() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('stakeholder_map_builder');

  const [policyIssue, setPolicyIssue] = useState('');
  const [scope, setScope] = useState('Federal');
  const [state, setState] = useState('');
  const [year, setYear] = useState('');
  const [includeTypes, setIncludeTypes] = useState([...ACTOR_TYPES]);
  const [activeTab, setActiveTab] = useState('Network Graph');

  const result = job?.result_data?.result;
  const analytics = job?.result_data?.analytics;
  const actors = result?.actors || [];
  const relationships = result?.relationships || [];
  const proponents = actors.filter((actor) => actor.stance === 'proponent');
  const opponents = actors.filter((actor) => actor.stance === 'opponent');
  const neutral = actors.filter((actor) => !['proponent', 'opponent'].includes(actor.stance));
  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  const actorColumns = [
    { key: 'name', label: 'Name' },
    { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
    { key: 'organization', label: 'Organization', render: (row) => row.organization || '—' },
    { key: 'influence_tier', label: 'Influence', render: (row) => formatTitle(row.influence_tier) },
    { key: 'betweenness_centrality', label: 'Betweenness', render: (row) => row.betweenness_centrality ?? '—' },
    { key: 'evidence', label: 'Evidence', render: (row) => row.evidence || '—' },
    { key: 'lda_amount', label: 'LDA Amount ($)', render: (row) => formatMoney(row.lda_amount) },
  ];

  const allActorColumns = [
    { key: 'name', label: 'Name' },
    { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
    { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
    { key: 'influence_tier', label: 'Influence', render: (row) => formatTitle(row.influence_tier) },
    { key: 'betweenness_centrality', label: 'Betweenness', render: (row) => row.betweenness_centrality ?? '—' },
    { key: 'degree_centrality', label: 'Degree', render: (row) => row.degree_centrality ?? '—' },
    { key: 'community_id', label: 'Community', render: (row) => `C${(row.community_id ?? 0) + 1}` },
    { key: 'organization', label: 'Organization', render: (row) => row.organization || '—' },
    { key: 'evidence', label: 'Evidence', render: (row) => row.evidence || '—' },
    { key: 'lda_amount', label: 'LDA Amount ($)', render: (row) => formatMoney(row.lda_amount) },
    { key: 'source', label: 'Source', render: (row) => row.source || '—' },
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
    payload.append('scope', scope.toLowerCase());
    payload.append('state', scope === 'State' ? state.toUpperCase() : 'US');
    payload.append('year', year);
    payload.append('include_types', includeTypes.map((item) => item.toLowerCase()).join(','));
    submitJob(payload);
  };

  const tabs = ['Network Graph', 'Network Analysis', 'Proponents', 'Opponents', 'All Actors', 'Summary'];
  const graphArtifact = artifactMap['stakeholder_map.html'];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-10 max-w-6xl mx-auto relative z-10">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)', marginBottom: 10 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect · TOOL
        </div>
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Stakeholder Map Builder</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '72ch', fontWeight: 300 }}>
          Discovers and classifies policy actors from lobbying filings, bill sponsorships, and news, then returns an interactive graph and network analysis.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div>
            <label className="field-label">Policy Issue</label>
            <input value={policyIssue} onChange={(event) => setPolicyIssue(event.target.value)}
              className="field" placeholder="e.g. artificial intelligence regulation" required />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="field-label">Scope</label>
              <select value={scope} onChange={(event) => setScope(event.target.value)} className="field">
                <option>Federal</option>
                <option>State</option>
              </select>
            </div>
            <div>
              <label className="field-label">State</label>
              <input value={state} onChange={(event) => setState(event.target.value)}
                className="field" placeholder="e.g. TX" disabled={scope === 'Federal'} />
            </div>
            <div>
              <label className="field-label">Year</label>
              <input value={year} onChange={(event) => setYear(event.target.value)} className="field" placeholder="optional" />
            </div>
          </div>
          <div>
            <label className="field-label">Actor Types To Include</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {ACTOR_TYPES.map((type) => (
                <label key={type} className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="checkbox" checked={includeTypes.includes(type)} onChange={() => toggleType(type)} className="accent-violet-500" />
                  <span>{type}</span>
                </label>
              ))}
            </div>
          </div>
          <button type="submit" disabled={loading || !policyIssue.trim()} className="btn-primary mt-auto">
            {loading ? <><SpinnerGap size={18} className="animate-spin" /> Building…</> : <>Build Stakeholder Map <ArrowRight size={18} /></>}
          </button>
        </div>

        <div className="glass-card p-8 flex flex-col gap-5">
          {job ? (
            <div className="rounded-xl border border-white/10 bg-black/20 p-5">
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
            <div className="rounded-xl border border-dashed border-white/10 px-5 py-8 text-sm text-slate-500">
              Run the tool to generate the graph, actor tables, and downloads.
            </div>
          )}

          {job?.status === 'completed' && result && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <SummaryMetric label="Total Actors" value={actors.length} />
              <SummaryMetric label="Proponents" value={proponents.length} />
              <SummaryMetric label="Opponents" value={opponents.length} />
              <SummaryMetric label="Neutral / Unknown" value={neutral.length} />
              <SummaryMetric label="Relationships" value={relationships.length} />
            </div>
          )}
        </div>
      </form>

      {job?.status === 'completed' && result && (
        <div className="mt-10 space-y-6">
          <div className="flex flex-wrap gap-3">
            {tabs.map((tab) => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg border text-sm ${activeTab === tab ? 'bg-violet-500/20 border-violet-400/40 text-violet-200' : 'bg-white/5 border-white/10 text-slate-300'}`}>
                {tab}
              </button>
            ))}
          </div>

          <div className="glass-card p-8">
            {activeTab === 'Network Graph' && (
              <div className="space-y-4">
                {graphArtifact ? (
                  <>
                    <iframe title="Stakeholder Map Graph" src={`${API}${graphArtifact.url}`} className="w-full h-[720px] rounded-xl border border-white/10 bg-white" />
                    <button onClick={() => downloadArtifact(graphArtifact)}
                      className="px-4 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 text-sm">
                      <DownloadSimple size={16} className="inline mr-2" /> Download Interactive Graph (.html)
                    </button>
                  </>
                ) : (
                  <p className="text-slate-400">Interactive graph export is not available for this run.</p>
                )}
              </div>
            )}

            {activeTab === 'Network Analysis' && (
              <div className="space-y-8 text-slate-300">
                {analytics ? (
                  <>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <SummaryMetric label="Network Density" value={Number(analytics.network_density || 0).toFixed(3)} />
                      <SummaryMetric label="Structural Communities" value={analytics.communities || 0} />
                      <SummaryMetric label="Bridge Actors" value={analytics.brokers?.length || 0} />
                      <SummaryMetric label="Multi-Venue Actors" value={analytics.multi_venue_actors?.length || 0} />
                    </div>

                    {analytics.strategic_summary && (
                      <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">
                        {analytics.strategic_summary}
                      </div>
                    )}

                    <section className="space-y-3">
                      <h3 className="text-white font-semibold">Bridge Actors</h3>
                      <p className="text-sm text-slate-400">
                        Bridge actors sit between proponent and opponent coalitions. In the Streamlit workflow these are the highest-value engagement targets.
                      </p>
                      {analytics.brokers?.length ? (
                        <Table
                          columns={[
                            { key: 'name', label: 'Name' },
                            { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
                            { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                            { key: 'betweenness_centrality', label: 'Betweenness', render: (row) => Number(row.betweenness_centrality || 0).toFixed(3) },
                            { key: 'degree_centrality', label: 'Degree', render: (row) => Number(row.degree_centrality || 0).toFixed(3) },
                            { key: 'organization', label: 'Organization', render: (row) => row.organization || '—' },
                          ]}
                          rows={analytics.brokers}
                        />
                      ) : (
                        <p className="text-slate-400">
                          {!analytics.has_edges
                            ? 'No relationships detected, so betweenness centrality cannot be computed.'
                            : !analytics.has_both_sides
                              ? 'Bridge actor detection requires both proponent and opponent actors.'
                              : 'No actors currently bridge the proponent and opponent coalitions directly.'}
                        </p>
                      )}
                    </section>

                    <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <h3 className="text-white font-semibold">Top by Betweenness</h3>
                        <p className="text-sm text-slate-400">How often an actor lies on the shortest path between others.</p>
                        <Table
                          columns={[
                            { key: 'name', label: 'Name' },
                            { key: 'betweenness_centrality', label: 'Betweenness', render: (row) => Number(row.betweenness_centrality || 0).toFixed(3) },
                            { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                          ]}
                          rows={analytics.top_by_betweenness || []}
                        />
                      </div>
                      <div className="space-y-3">
                        <h3 className="text-white font-semibold">Top by Degree</h3>
                        <p className="text-sm text-slate-400">Number of direct connections across the network.</p>
                        <Table
                          columns={[
                            { key: 'name', label: 'Name' },
                            { key: 'degree_centrality', label: 'Degree', render: (row) => Number(row.degree_centrality || 0).toFixed(3) },
                            { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                          ]}
                          rows={analytics.top_by_degree || []}
                        />
                      </div>
                    </section>

                    <section className="space-y-3">
                      <h3 className="text-white font-semibold">Structural Communities</h3>
                      <p className="text-sm text-slate-400">
                        Communities are detected from the relationship structure and may not align with stance labels.
                      </p>
                      {analytics.communities > 1 ? (
                        <Table
                          columns={[
                            { key: 'community', label: 'Community' },
                            { key: 'name', label: 'Name' },
                            { key: 'stance', label: 'Stance', render: (row) => formatTitle(row.stance) },
                            { key: 'stakeholder_type', label: 'Type', render: (row) => formatTitle(row.stakeholder_type) },
                          ]}
                          rows={actors.map((actor) => ({
                            ...actor,
                            community: `C${(actor.community_id ?? 0) + 1}`,
                          }))}
                        />
                      ) : (
                        <p className="text-slate-400">All actors fall into a single structural community.</p>
                      )}
                    </section>

                    {analytics.multi_venue_actors?.length > 0 && (
                      <section className="space-y-3">
                        <h3 className="text-white font-semibold">Multi-Venue Actors</h3>
                        <p className="text-sm text-slate-400">
                          These actors appear in both administrative and legislative venues.
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
                {result.proponent_summary && (
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">{result.proponent_summary}</div>
                )}
                <Table columns={actorColumns} rows={proponents} emptyMessage="No proponents identified for this issue." />
              </div>
            )}

            {activeTab === 'Opponents' && (
              <div className="space-y-4">
                {result.opponent_summary && (
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">{result.opponent_summary}</div>
                )}
                <Table columns={actorColumns} rows={opponents} emptyMessage="No opponents identified for this issue." />
              </div>
            )}

            {activeTab === 'All Actors' && (
              <div className="space-y-8">
                <Table columns={allActorColumns} rows={actors} />
                {relationships.length > 0 && (
                  <section className="space-y-3">
                    <h3 className="text-white font-semibold">Relationships</h3>
                    <Table
                      columns={[
                        { key: 'from_name', label: 'From' },
                        { key: 'to_name', label: 'To' },
                        { key: 'relationship', label: 'Relationship' },
                        { key: 'label', label: 'Label' },
                      ]}
                      rows={relationships.map((relationship, index) => ({
                        key: index,
                        from_name: actors.find((actor) => actor.id === relationship.from_id)?.name || relationship.from_id,
                        to_name: actors.find((actor) => actor.id === relationship.to_id)?.name || relationship.to_id,
                        relationship: formatTitle(String(relationship.type || '').replaceAll(' ', '_')),
                        label: relationship.label || '—',
                      }))}
                    />
                  </section>
                )}
              </div>
            )}

            {activeTab === 'Summary' && (
              <div className="space-y-5 text-slate-300">
                {result.issue_summary && (
                  <section>
                    <h3 className="text-white font-semibold mb-2">Issue Overview</h3>
                    <p>{result.issue_summary}</p>
                  </section>
                )}

                {result.key_coalitions?.length > 0 && (
                  <section>
                    <h3 className="text-white font-semibold mb-2">Key Coalitions</h3>
                    <ul className="space-y-2">
                      {result.key_coalitions.map((coalition) => (
                        <li key={coalition}>• {coalition}</li>
                      ))}
                    </ul>
                  </section>
                )}

                {result.strategic_notes && (
                  <section>
                    <h3 className="text-white font-semibold mb-2">Strategic Notes</h3>
                    <p>{result.strategic_notes}</p>
                  </section>
                )}

                <p className="text-sm text-slate-500">
                  Stance classifications are LLM-inferred from public data and should be verified before strategic use. Network metrics follow the Varone, Ingold &amp; Jourdain framework.
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button onClick={() => downloadArtifact(artifactMap['stakeholder_map.xlsx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
              <DownloadSimple size={18} /> Download XLSX
            </button>
            <button onClick={() => downloadArtifact(artifactMap['stakeholder_map.docx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download DOCX
            </button>
            <button onClick={() => downloadText(job?.result_data?.markdown || '', 'stakeholder_map.md')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download Markdown
            </button>
            <button onClick={() => downloadJson(result || {}, 'stakeholder_map.json')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download JSON
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
