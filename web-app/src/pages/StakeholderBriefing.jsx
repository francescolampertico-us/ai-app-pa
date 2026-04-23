/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';
import ToolTourButton from '../components/tour/ToolTourButton';
import { TOOL_TOUR_IDS } from '../components/tour/tourDefinitions';

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
  const [llmModel, setLlmModel] = useState('ChangeAgent');

  const rd = job?.result_data;
  const disclosures = rd?.disclosures || {};
  const profile = rd?.profile || {};
  const curatedDisclosures = rd?.curated_disclosures || [];
  const evidenceFlags = rd?.evidence_flags || [];
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
  const tabs = ['Profile', 'Policy Positions', 'Talking Points', ...(hasDisclosures ? ['Disclosures'] : []), ...(rd?.news?.length ? ['News'] : [])];

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
    payload.append('llm_model', llmModel);
    uploadedFiles.forEach((file) => payload.append('file', file));
    submitJob(payload);
  };

  return (
    <motion.div data-testid="tool-page-stakeholder-briefing" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="app-page-shell app-page-shell-wide">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <h1 data-testid="page-title-stakeholder-briefing" className="app-page-title">Stakeholder Briefing</h1>
        <p className="app-page-intro" style={{ maxWidth: '70ch' }}>
          Generates a pre-meeting briefing with bio, policy positions, suggested talking points, optional disclosure records, and optional recent news.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <ModelSelector value={llmModel} onChange={setLlmModel} />
          <div data-tour="tour-button-stakeholder-briefing"><ToolTourButton tourId={TOOL_TOUR_IDS.stakeholderBriefing} /></div>
        </div>
      </header>

      <ResearchPrototypeNote
        category="Stakeholder Mapping and Network Analysis"
        refs={['bitonti2023', 'digiacomo2025']}
        message="This prototype module converts stakeholder research into a structured meeting brief. It supports preparation and synthesis, but positions, biographies, and disclosure references remain provisional until checked against primary material."
      />

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="field-label">Stakeholder Name</label>
              <input data-testid="input-stakeholder-name" data-tour="stakeholder-briefing-name" value={stakeholderName} onChange={(event) => setStakeholderName(event.target.value)}
                className="field" placeholder="e.g. Sen. Maria Cantwell" required />
            </div>
            <div>
              <label className="field-label">Organization</label>
              <input data-testid="input-stakeholder-organization" value={organization} onChange={(event) => setOrganization(event.target.value)}
                className="field" placeholder="e.g. Senate Commerce Committee" />
            </div>
          </div>

          <div>
            <label className="field-label">Meeting Purpose</label>
            <textarea data-testid="input-stakeholder-meeting-purpose" value={meetingPurpose} onChange={(event) => setMeetingPurpose(event.target.value)}
              className="field resize-none" rows={4}
              placeholder="e.g. Discuss support for the AI Safety Act and potential co-sponsorship" required />
          </div>

          <details data-tour="stakeholder-briefing-options" className="rounded-xl border border-white/10 bg-black/20 p-5">
            <summary className="cursor-pointer text-white font-semibold">Additional Options</summary>
            <div className="mt-5 flex flex-col gap-5">
              <div>
                <label className="field-label">Your Organization</label>
                <input data-testid="input-stakeholder-your-org" value={yourOrg} onChange={(event) => setYourOrg(event.target.value)}
                  className="field" placeholder="e.g. TechForward Alliance" />
              </div>
              <div>
                <label className="field-label">Additional Context</label>
                <textarea data-testid="input-stakeholder-context" value={context} onChange={(event) => setContext(event.target.value)}
                  className="field resize-none" rows={5} placeholder="Paste relevant material, notes, or background here..." />
              </div>
              <div>
                <label className="field-label">Context Document</label>
                <input data-testid="input-stakeholder-files" type="file" accept=".pdf,.docx,.txt" multiple
                  onChange={(event) => setUploadedFiles(Array.from(event.target.files || []))}
                  className="field file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-violet-500/20 file:text-violet-300" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input data-testid="toggle-stakeholder-disclosures" type="checkbox" checked={includeDisclosures} onChange={() => setIncludeDisclosures((prev) => !prev)} className="accent-violet-500" />
                  <span>Search disclosure records</span>
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input data-testid="toggle-stakeholder-news" type="checkbox" checked={includeNews} onChange={() => setIncludeNews((prev) => !prev)} className="accent-violet-500" />
                  <span>Fetch recent news mentions</span>
                </label>
              </div>
            </div>
          </details>

          <button data-testid="submit-stakeholder-briefing" data-tour="stakeholder-briefing-submit" type="submit" disabled={loading || !stakeholderName.trim() || !meetingPurpose.trim()} className="btn-primary mt-auto">
            {loading ? <><SpinnerGap size={18} className="animate-spin" /> Generating…</> : <>Generate Briefing <ArrowRight size={18} /></>}
          </button>
        </div>

        <div data-tour="stakeholder-briefing-output" className="glass-card p-8 flex flex-col gap-5">
          {job ? (
            <div data-testid="status-stakeholder-briefing" className="rounded-xl border border-white/10 bg-black/20 p-5">
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
            null
          )}

          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
            Additional verification needed. Confirm all biographical details, positions, and disclosure references before use.
          </div>
        </div>
      </form>

      {job?.status === 'completed' && rd && (
        <div data-tour="stakeholder-briefing-output" className="mt-10 space-y-6">
          <div className="flex flex-wrap gap-3">
            {tabs.map((tab) => (
              <button data-testid={`tab-stakeholder-${tab.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`} key={tab} onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg border text-sm ${activeTab === tab ? 'bg-violet-500/20 border-violet-400/40 text-violet-200' : 'bg-white/5 border-white/10 text-slate-300'}`}>
                {tab}
              </button>
            ))}
          </div>

          <div className="glass-card p-8">
            <div className="app-output-header">Stakeholder Briefing</div>
            {activeTab === 'Profile' && (
              <div className="space-y-5">
                <div>
                  <h2 className="app-section-title" style={{ fontSize: 28 }}>{rd.header?.stakeholder_name}</h2>
                  {rd.header?.organization && <p className="text-slate-400 mt-2">{rd.header.organization}</p>}
                </div>
                <div className="flex flex-wrap gap-3 text-xs uppercase tracking-wider">
                  <span className={`px-3 py-1 rounded-full border ${rd.briefing_quality === 'complete' ? 'border-emerald-500/30 text-emerald-300 bg-emerald-500/10' : 'border-amber-500/30 text-amber-200 bg-amber-500/10'}`}>
                    {rd.briefing_quality || 'partial'}
                  </span>
                  <span className="px-3 py-1 rounded-full border border-white/10 text-slate-300 bg-black/20">
                    disclosure: {rd.disclosure_mode || 'none'}
                  </span>
                </div>
                {profile.summary && <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">{profile.summary}</div>}
                {profile.current_role && <p className="text-slate-300"><strong className="text-white">Current Role:</strong> {profile.current_role}</p>}
                {profile.key_areas?.length > 0 && <p className="text-slate-300"><strong className="text-white">Key Policy Areas:</strong> {profile.key_areas.join(', ')}</p>}
                {profile.notable_positions && <p className="text-slate-300"><strong className="text-white">Notable Positions:</strong> {profile.notable_positions}</p>}
                {evidenceFlags.length > 0 && (
                  <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4">
                    <h3 className="text-amber-200 font-semibold mb-2">Needs Verification</h3>
                    <div className="space-y-1">
                      {evidenceFlags.map((flag, index) => (
                        <p key={index} className="text-amber-100 text-sm">{flag}</p>
                      ))}
                    </div>
                  </div>
                )}
                {rd.key_questions?.length > 0 && (
                  <div>
                    <h3 className="app-subsection-title">Key Questions To Ask</h3>
                    <div className="space-y-3">
                      {rd.key_questions.map((question, index) => (
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
                {(rd.policy_positions || []).length > 0 ? rd.policy_positions.map((position, index) => (
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
                {(rd.talking_points || []).length > 0 ? rd.talking_points.map((point, index) => (
                  <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                    <p className="text-white font-medium">{index + 1}. {point.point}</p>
                    {point.rationale && <p className="text-slate-400 text-sm mt-2">{point.rationale}</p>}
                  </div>
                )) : <p className="text-slate-400">No talking points generated.</p>}
              </div>
            )}

            {activeTab === 'Disclosures' && (
              <div className="space-y-6 text-sm text-slate-300">
                {curatedDisclosures.length > 0 && (
                  <div>
                    <h3 className="app-subsection-title">Curated Disclosure Intelligence</h3>
                    <div className="space-y-3">
                      {curatedDisclosures.map((item, index) => (
                        <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                          <p className="text-white font-medium">{item.who}</p>
                          <p className="text-slate-300 mt-1">{item.what}</p>
                          <p className="text-slate-400 text-sm mt-2">Why it matters: {item.why_it_matters}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {disclosures.lda_entity?.length > 0 && (
                  <div>
                    <h3 className="app-subsection-title">LDA Lobbying (Stakeholder Activity)</h3>
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
                    <h3 className="app-subsection-title">Lobbying Activity On Meeting Topic</h3>
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
                    <h3 className="app-subsection-title">FARA Records</h3>
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
                    <h3 className="app-subsection-title">IRS 990 Records</h3>
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
                {(rd.news || []).map((item, index) => (
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
            <button data-testid="download-stakeholder-markdown" onClick={() => downloadText(job?.result_data?.markdown || '', 'stakeholder_briefing.md')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download Markdown
            </button>
            <button data-testid="download-stakeholder-docx" onClick={() => downloadArtifact(artifactMap['stakeholder_briefing.docx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
              <DownloadSimple size={18} /> Download DOCX
            </button>
            <button data-testid="download-stakeholder-json" onClick={() => downloadJson(rd || {}, 'stakeholder_briefing.json')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download JSON
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
