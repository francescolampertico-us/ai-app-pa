/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';

function DisclosureTable({ columns, rows }) {
  if (!rows?.length) return null;
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
            <tr key={rowIndex} className="border-b border-white/5 align-top">
              {columns.map((column) => (
                <td key={column.key} className="py-3 px-4 whitespace-pre-wrap">{row[column.key] || '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function StakeholderBriefing() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('stakeholder_briefing');

  const [stakeholderName, setStakeholderName] = useState('');
  const [organization, setOrganization] = useState('');
  const [meetingPurpose, setMeetingPurpose] = useState('');
  const [yourOrg, setYourOrg] = useState('');
  const [context, setContext] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [includeDisclosures, setIncludeDisclosures] = useState(true);
  const [includeNews, setIncludeNews] = useState(true);
  const [activeTab, setActiveTab] = useState('Profile');

  const result = job?.result_data?.result;
  const disclosures = result?.disclosures || {};
  const profile = result?.profile || {};
  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  const hasDisclosures = Boolean(
    (disclosures.lda_entity && disclosures.lda_entity.length) ||
    (disclosures.lda_topic && disclosures.lda_topic.length) ||
    (disclosures.fara?.registrants && disclosures.fara.registrants.length) ||
    (disclosures.fara?.foreign_principals && disclosures.fara.foreign_principals.length) ||
    (disclosures.irs990?.organizations && disclosures.irs990.organizations.length) ||
    (disclosures.irs990?.filings && disclosures.irs990.filings.length)
  );
  const tabs = ['Profile', 'Policy Positions', 'Talking Points', ...(hasDisclosures ? ['Disclosures'] : []), ...(result?.news?.length ? ['News'] : [])];

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('stakeholder_name', stakeholderName);
    payload.append('organization', organization);
    payload.append('meeting_purpose', meetingPurpose);
    payload.append('your_org', yourOrg);
    payload.append('context', context);
    payload.append('include_disclosures', String(includeDisclosures));
    payload.append('include_news', String(includeNews));
    uploadedFiles.forEach((file) => payload.append('file', file));
    submitJob(payload);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-10 max-w-6xl mx-auto relative z-10">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)', marginBottom: 10 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect · TOOL
        </div>
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Stakeholder Briefing</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '70ch', fontWeight: 300 }}>
          Generates a pre-meeting briefing with bio, policy positions, suggested talking points, optional disclosure records, and optional recent news.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="field-label">Stakeholder Name</label>
              <input value={stakeholderName} onChange={(event) => setStakeholderName(event.target.value)}
                className="field" placeholder="e.g. Sen. Maria Cantwell" required />
            </div>
            <div>
              <label className="field-label">Organization</label>
              <input value={organization} onChange={(event) => setOrganization(event.target.value)}
                className="field" placeholder="e.g. Senate Commerce Committee" />
            </div>
          </div>

          <div>
            <label className="field-label">Meeting Purpose</label>
            <textarea value={meetingPurpose} onChange={(event) => setMeetingPurpose(event.target.value)}
              className="field resize-none" rows={4}
              placeholder="e.g. Discuss support for the AI Safety Act and potential co-sponsorship" required />
          </div>

          <details className="rounded-xl border border-white/10 bg-black/20 p-5">
            <summary className="cursor-pointer text-white font-semibold">Additional Options</summary>
            <div className="mt-5 flex flex-col gap-5">
              <div>
                <label className="field-label">Your Organization</label>
                <input value={yourOrg} onChange={(event) => setYourOrg(event.target.value)}
                  className="field" placeholder="e.g. TechForward Alliance" />
              </div>
              <div>
                <label className="field-label">Additional Context</label>
                <textarea value={context} onChange={(event) => setContext(event.target.value)}
                  className="field resize-none" rows={5} placeholder="Paste relevant material, notes, or background here..." />
              </div>
              <div>
                <label className="field-label">Context Document</label>
                <input type="file" accept=".pdf,.docx,.txt" multiple
                  onChange={(event) => setUploadedFiles(Array.from(event.target.files || []))}
                  className="field file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-violet-500/20 file:text-violet-300" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="checkbox" checked={includeDisclosures} onChange={() => setIncludeDisclosures((prev) => !prev)} className="accent-violet-500" />
                  <span>Search disclosure records</span>
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="checkbox" checked={includeNews} onChange={() => setIncludeNews((prev) => !prev)} className="accent-violet-500" />
                  <span>Fetch recent news mentions</span>
                </label>
              </div>
            </div>
          </details>

          <button type="submit" disabled={loading || !stakeholderName.trim() || !meetingPurpose.trim()} className="btn-primary mt-auto">
            {loading ? <><SpinnerGap size={18} className="animate-spin" /> Generating…</> : <>Generate Briefing <ArrowRight size={18} /></>}
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
              Fill in the meeting objective and run the tool to generate the briefing.
            </div>
          )}

          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
            Review required. Confirm all biographical details, positions, and disclosure references before use.
          </div>
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
            {activeTab === 'Profile' && (
              <div className="space-y-5">
                <div>
                  <h2 className="display" style={{ fontSize: 28, color: '#fff' }}>{result.header?.stakeholder_name}</h2>
                  {result.header?.organization && <p className="text-slate-400 mt-2">{result.header.organization}</p>}
                </div>
                {profile.summary && <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">{profile.summary}</div>}
                {profile.current_role && <p className="text-slate-300"><strong className="text-white">Current Role:</strong> {profile.current_role}</p>}
                {profile.key_areas?.length > 0 && <p className="text-slate-300"><strong className="text-white">Key Policy Areas:</strong> {profile.key_areas.join(', ')}</p>}
                {profile.notable_positions && <p className="text-slate-300"><strong className="text-white">Notable Positions:</strong> {profile.notable_positions}</p>}
                {result.key_questions?.length > 0 && (
                  <div>
                    <h3 className="text-white text-lg font-semibold mb-3">Key Questions To Ask</h3>
                    <div className="space-y-3">
                      {result.key_questions.map((question, index) => (
                        <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                          <p className="text-slate-100 font-medium">{question.question}</p>
                          {question.purpose && <p className="text-slate-400 text-sm mt-2">Purpose: {question.purpose}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'Policy Positions' && (
              <div className="space-y-5">
                {(result.policy_positions || []).length > 0 ? result.policy_positions.map((position, index) => (
                  <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                    <p className="text-white font-medium">{position.position}</p>
                    {position.evidence && <p className="text-slate-400 text-sm mt-2">Evidence: {position.evidence}</p>}
                    {position.relevance && <p className="text-slate-400 text-sm mt-1">Relevance: {position.relevance}</p>}
                  </div>
                )) : <p className="text-slate-400">No specific policy positions identified.</p>}
              </div>
            )}

            {activeTab === 'Talking Points' && (
              <div className="space-y-4">
                {(result.talking_points || []).length > 0 ? result.talking_points.map((point, index) => (
                  <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                    <p className="text-white font-medium">{index + 1}. {point.point}</p>
                    {point.rationale && <p className="text-slate-400 text-sm mt-2">{point.rationale}</p>}
                  </div>
                )) : <p className="text-slate-400">No talking points generated.</p>}
              </div>
            )}

            {activeTab === 'Disclosures' && (
              <div className="space-y-6 text-sm text-slate-300">
                {disclosures.lda_entity?.length > 0 && (
                  <div>
                    <h3 className="text-white font-semibold mb-3">LDA Lobbying (Stakeholder Activity)</h3>
                    <DisclosureTable
                      columns={[
                        { key: 'registrant_name', label: 'Registrant' },
                        { key: 'client_name', label: 'Client' },
                        { key: 'filing_year', label: 'Year' },
                        { key: 'amount_reported', label: 'Amount' },
                      ]}
                      rows={disclosures.lda_entity.slice(0, 10)}
                    />
                  </div>
                )}
                {disclosures.lda_topic?.length > 0 && (
                  <div>
                    <h3 className="text-white font-semibold mb-3">Lobbying Activity On Meeting Topic</h3>
                    <p className="text-slate-400 text-sm mb-3">Organizations actively lobbying on the issue you&apos;re meeting about.</p>
                    <DisclosureTable
                      columns={[
                        { key: 'client_name', label: 'Client' },
                        { key: 'registrant_name', label: 'Registrant' },
                        { key: 'filing_year', label: 'Year' },
                        { key: 'filing_period', label: 'Quarter' },
                        { key: 'amount_reported', label: 'Amount' },
                      ]}
                      rows={disclosures.lda_topic.slice(0, 10)}
                    />
                  </div>
                )}
                {(disclosures.fara?.registrants?.length > 0 || disclosures.fara?.foreign_principals?.length > 0) && (
                  <div>
                    <h3 className="text-white font-semibold mb-3">FARA Records</h3>
                    {disclosures.fara?.registrants?.length > 0 && (
                      <div className="space-y-3 mb-5">
                        <p className="text-slate-400 text-sm">Registrants</p>
                        <DisclosureTable
                          columns={Object.keys(disclosures.fara.registrants[0] || {}).slice(0, 6).map((key) => ({ key, label: key.replaceAll('_', ' ') }))}
                          rows={disclosures.fara.registrants.slice(0, 10)}
                        />
                      </div>
                    )}
                    {disclosures.fara?.foreign_principals?.length > 0 && (
                      <div className="space-y-3">
                        <p className="text-slate-400 text-sm">Foreign Principals</p>
                        <DisclosureTable
                          columns={Object.keys(disclosures.fara.foreign_principals[0] || {}).slice(0, 6).map((key) => ({ key, label: key.replaceAll('_', ' ') }))}
                          rows={disclosures.fara.foreign_principals.slice(0, 10)}
                        />
                      </div>
                    )}
                  </div>
                )}
                {(disclosures.irs990?.organizations?.length > 0 || disclosures.irs990?.filings?.length > 0) && (
                  <div>
                    <h3 className="text-white font-semibold mb-3">IRS 990 Records</h3>
                    {disclosures.irs990?.organizations?.length > 0 && (
                      <div className="space-y-3 mb-5">
                        <p className="text-slate-400 text-sm">Organizations</p>
                        <DisclosureTable
                          columns={Object.keys(disclosures.irs990.organizations[0] || {}).slice(0, 6).map((key) => ({ key, label: key.replaceAll('_', ' ') }))}
                          rows={disclosures.irs990.organizations.slice(0, 10)}
                        />
                      </div>
                    )}
                    {disclosures.irs990?.filings?.length > 0 && (
                      <div className="space-y-3">
                        <p className="text-slate-400 text-sm">Filings</p>
                        <DisclosureTable
                          columns={Object.keys(disclosures.irs990.filings[0] || {}).slice(0, 6).map((key) => ({ key, label: key.replaceAll('_', ' ') }))}
                          rows={disclosures.irs990.filings.slice(0, 10)}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'News' && (
              <div className="space-y-5">
                {(result.news || []).map((item, index) => (
                  <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                    <p className="text-white font-medium">{item.title}</p>
                    <p className="text-slate-400 text-sm mt-1">{item.source} {item.date ? `— ${item.date}` : ''}</p>
                    {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="text-violet-300 underline mt-2 inline-block">Read article</a>}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button onClick={() => downloadText(job?.result_data?.markdown || '', 'stakeholder_briefing.md')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download Markdown
            </button>
            <button onClick={() => downloadArtifact(artifactMap['stakeholder_briefing.docx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
              <DownloadSimple size={18} /> Download DOCX
            </button>
            <button onClick={() => downloadJson(result || {}, 'stakeholder_briefing.json')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download JSON
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
