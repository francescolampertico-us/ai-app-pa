/* eslint-disable no-unused-vars */
import { useMemo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap, EnvelopeSimpleIcon as EnvelopeSimple, CopyIcon as Copy, XIcon as X } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import { API } from '../hooks/useFastApiJob';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';
import ToolTourButton from '../components/tour/ToolTourButton';
import ToolOutputPreview from '../components/tour/ToolOutputPreview';
import { TOOL_TOUR_IDS } from '../components/tour/tourDefinitions';

const MEDIA_TYPES = [
  ['mainstream', 'Mainstream'],
  ['print', 'Print'],
  ['broadcast', 'Broadcast (TV/Radio)'],
  ['digital', 'Digital / Online'],
  ['trade', 'Trade / Policy'],
  ['podcast', 'Podcast'],
];
const MEDIA_TYPE_LABELS = Object.fromEntries(MEDIA_TYPES);
const DESK_OPTIONS = [
  ['health', 'Health'],
  ['business', 'Business'],
  ['finance', 'Finance'],
  ['politics', 'Politics'],
  ['policy', 'Policy / Regulation'],
  ['technology', 'Technology'],
  ['climate', 'Climate'],
  ['energy', 'Energy'],
  ['transportation', 'Transportation'],
  ['education', 'Education'],
  ['legal', 'Legal / Courts'],
  ['labor', 'Labor'],
  ['housing', 'Housing'],
  ['agriculture', 'Agriculture'],
  ['defense', 'Defense'],
  ['foreign affairs', 'Foreign Affairs'],
];

function PitchModal({ contact, issue, llmModel, onClose }) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const generate = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/tools/pitch-draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact, issue, llm_model: llmModel }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setSubject(data.subject || '');
      setBody(data.body || '');
    } catch (err) {
      setError(err.message || 'Failed to generate pitch.');
    } finally {
      setLoading(false);
    }
  }, [contact, issue, llmModel]);

  const copyAll = () => {
    const text = `Subject: ${subject}\n\n${body}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const rawName = [contact.first_name, contact.last_name].filter(Boolean).join(' ').trim();
  const isStoryLead = contact.contact_status === 'story_lead' || rawName.toLowerCase() === 'to verify';
  const name = isStoryLead ? 'Outlet story lead' : (rawName || 'this journalist');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}>
      <motion.div
        data-testid="media-list-pitch-modal"
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 8 }}
        className="glass-card w-full max-w-2xl p-8 flex flex-col gap-5 relative"
        style={{ maxHeight: '85vh', overflowY: 'auto' }}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs text-violet-400 uppercase tracking-widest mb-1">Pitch Draft</div>
            <h2 className="text-white text-lg font-semibold">{name}</h2>
            <div className="text-slate-400 text-sm">{contact.outlet} · {contact.role}</div>
          </div>
          <button data-testid="close-media-list-pitch-modal" onClick={onClose} className="text-slate-500 hover:text-white transition-colors mt-1">
            <X size={20} />
          </button>
        </div>

        {!subject && !body && !loading && !error && (
          <div className="rounded-xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-500 text-center">
            Click Generate to draft a personalised pitch email for {name}.
          </div>
        )}

        {loading && (
          <div className="flex items-center gap-3 text-slate-400 text-sm py-4">
            <SpinnerGap size={18} className="animate-spin text-violet-400" />
            Drafting pitch…
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-300 text-sm">{error}</div>
        )}

        {(subject || body) && (
          <div className="flex flex-col gap-4">
            <div>
              <label className="field-label">Subject</label>
              <input
                data-testid="input-media-list-pitch-subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="field"
              />
            </div>
            <div>
              <label className="field-label">Body</label>
              <textarea
                data-testid="input-media-list-pitch-body"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="field resize-none"
                rows={12}
              />
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            data-testid="submit-media-list-pitch"
            onClick={generate}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading
              ? <><SpinnerGap size={16} className="animate-spin" /> Generating…</>
              : <><EnvelopeSimple size={16} /> {subject || body ? 'Regenerate' : 'Generate Pitch'}</>
            }
          </button>
          {(subject || body) && (
            <button
              data-testid="copy-media-list-pitch"
              onClick={copyAll}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-colors"
            >
              <Copy size={16} /> {copied ? 'Copied!' : 'Copy'}
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}

export default function MediaListBuilder() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('media_list_builder');

  const [issue, setIssue] = useState('');
  const [broadTopic, setBroadTopic] = useState('');
  const [coverageDesk, setCoverageDesk] = useState('');
  const [locationType, setLocationType] = useState('National (US)');
  const [location, setLocation] = useState('');
  const [numContacts, setNumContacts] = useState(20);
  const [selectedTypes, setSelectedTypes] = useState(['mainstream', 'print', 'broadcast', 'digital', 'trade']);
  const [filterTypes, setFilterTypes] = useState([]);
  const [llmModel, setLlmModel] = useState('ChangeAgent');
  const [sourceFilter, setSourceFilter] = useState('national');
  const [pitchContact, setPitchContact] = useState(null);

  const rd = job?.result_data;
  const contacts = useMemo(() => rd?.contacts || [], [rd]);
  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  const resolvedLocation = locationType === 'National (US)' ? 'US' : location.trim();
  const canSubmit = Boolean(issue.trim() || broadTopic.trim() || coverageDesk.trim()) && selectedTypes.length > 0;

  const typeCounts = useMemo(() => {
    const counts = {};
    contacts.forEach((contact) => {
      const type = contact.media_type || 'other';
      counts[type] = (counts[type] || 0) + 1;
    });
    return counts;
  }, [contacts]);

  const visibleTypes = filterTypes.length ? filterTypes : Object.keys(typeCounts);
  const filteredContacts = contacts.filter((contact) => visibleTypes.includes(contact.media_type));

  const toggleSelectedType = (type) => {
    setSelectedTypes((prev) => (
      prev.includes(type) ? prev.filter((item) => item !== type) : [...prev, type]
    ));
  };

  const toggleFilterType = (type) => {
    setFilterTypes((prev) => (
      prev.includes(type) ? prev.filter((item) => item !== type) : [...prev, type]
    ));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('issue', issue);
    payload.append('topic_mode', (broadTopic.trim() || coverageDesk.trim()) ? 'broad' : 'specific');
    payload.append('broad_topic', broadTopic);
    payload.append('coverage_desk', coverageDesk);
    payload.append('location', resolvedLocation || 'US');
    payload.append('num_contacts', String(numContacts));
    payload.append('media_types', selectedTypes.join(','));
    payload.append('llm_model', llmModel);
    payload.append('source_filter', sourceFilter);
    submitJob(payload);
  };

  return (
    <>
      <AnimatePresence>
        {pitchContact && (
          <PitchModal
            contact={pitchContact}
            issue={issue || rd?.issue || ''}
            llmModel={llmModel}
            onClose={() => setPitchContact(null)}
          />
        )}
      </AnimatePresence>

      <motion.div data-testid="tool-page-media-list" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="app-page-shell app-page-shell-wide">
        <header className="page-header relative">
          <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
            style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
          <h1 data-testid="page-title-media-list" className="app-page-title">Media List</h1>
          <p className="app-page-intro" style={{ maxWidth: '68ch' }}>
            Generates a targeted media list based on a policy issue, geographic scope, and media type filter, then returns Excel, markdown, and JSON outputs.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <ModelSelector value={llmModel} onChange={setLlmModel} />
            <div data-tour="tour-button-media-list"><ToolTourButton tourId={TOOL_TOUR_IDS.mediaList} /></div>
          </div>
        </header>

        <ResearchPrototypeNote
          category="Stakeholder Mapping and Network Analysis"
          refs={['karakulle2025', 'bitonti2023', 'digiacomo2025']}
          message="This module turns issue research into a media outreach starting point. It demonstrates how AI can support list-building and angle generation, but journalist identities, beats, and contact details remain review-required before any outreach is sent."
        />

        <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="glass-card p-8 flex flex-col gap-5">
            <div>
              <label className="field-label">Policy Issue To Pitch</label>
              <textarea data-testid="input-media-list-issue" data-tour="media-list-issue" value={issue} onChange={(event) => setIssue(event.target.value)}
                className="field resize-none" rows={4}
                placeholder="e.g. hospital price transparency or AI safety regulation and mandatory pre-deployment testing requirements" />
            </div>

            <div>
              <label className="field-label">Broad Topic</label>
              <input
                data-testid="input-media-list-broad-topic"
                value={broadTopic}
                onChange={(event) => setBroadTopic(event.target.value)}
                className="field"
                placeholder="Optional: e.g. health, transportation, housing affordability"
              />
            </div>

            <div>
              <label className="field-label">Coverage Desk</label>
              <select data-testid="input-media-list-coverage-desk" value={coverageDesk} onChange={(event) => setCoverageDesk(event.target.value)} className="field">
                <option value="">Optional: select a desk</option>
                {DESK_OPTIONS.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div className="text-xs text-slate-500">
              Use `Policy Issue` for a precise topic. Add `Broad Topic` or `Coverage Desk` if you want the tool to expand into a wider beat like Health or Energy without switching modes.
            </div>

            <div data-tour="media-list-options" className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="field-label">Geographic Scope</label>
                <select data-testid="input-media-list-location-type" value={locationType} onChange={(event) => { setLocationType(event.target.value); setLocation(''); }} className="field">
                  <option>National (US)</option>
                  <option>State</option>
                  <option>City / Metro</option>
                </select>
              </div>
              <div>
                {locationType === 'National (US)' ? (
                  <div>
                    <label className="field-label">Outlet Scope</label>
                    <select data-testid="input-media-list-source-filter" value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} className="field">
                      <option value="national">National outlets only</option>
                      <option value="all">All outlets</option>
                    </select>
                  </div>
                ) : (
                  <>
                    <label className="field-label">{locationType === 'State' ? 'State' : 'City / Metro'}</label>
                    <input data-testid="input-media-list-location" value={location} onChange={(event) => setLocation(event.target.value)}
                      className="field"
                      placeholder={locationType === 'State' ? 'e.g. California' : 'e.g. Washington DC'} />
                  </>
                )}
              </div>
              <div>
                <label className="field-label">Number Of Contacts</label>
                <input data-testid="input-media-list-num-contacts" type="range" min="5" max="40" step="5" value={numContacts} onChange={(event) => setNumContacts(Number(event.target.value))}
                  className="w-full accent-violet-500 mt-4" />
                <div className="text-sm text-slate-400 mt-2">{numContacts}</div>
              </div>
            </div>

            <div>
              <label className="field-label">Media Types To Include</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                {MEDIA_TYPES.map(([value, label]) => (
                  <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                    <input data-testid={`toggle-media-list-type-${value}`} type="checkbox" checked={selectedTypes.includes(value)} onChange={() => toggleSelectedType(value)} className="accent-violet-500" />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <button data-testid="submit-media-list" data-tour="media-list-submit" type="submit" disabled={loading || !canSubmit}
              className="btn-primary mt-auto">
              {loading ? <><SpinnerGap size={18} className="animate-spin" /> Building…</> : <>Build Media List <ArrowRight size={18} /></>}
            </button>
          </div>

          <div data-tour="media-list-output" className="glass-card p-8 flex flex-col gap-5">
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
              Additional verification needed. Journalist names, roles, and story links may be inaccurate or outdated. Verify all contacts before pitching.
            </div>

            {job ? (
              <div data-testid="status-media-list" className="rounded-xl border border-white/10 bg-black/20 p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs text-purple-300">{job.id.slice(0, 8).toUpperCase()}</span>
                  <span className={job.status === 'completed' ? 'badge-complete' : job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>{job.status}</span>
                </div>
                <p className="text-slate-300 text-sm mb-4">{job.message}</p>
                {['pending', 'processing'].includes(job.status) && (
                  <p className="text-xs text-slate-500 mb-4">
                    Complex searches may take several minutes to finish.
                  </p>
                )}
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${job.progress || 0}%` }} />
                </div>
              </div>
            ) : (
              <ToolOutputPreview
                title="Output Preview"
                summary="A run returns a contact list, quality notes, optional pitch support, and downloadable files."
                items={[
                  { title: 'Status', copy: 'Progress and quality messages show up here while the list is being built.' },
                  { title: 'Contacts', copy: 'The finished list organizes journalist names, outlets, roles, and source links.' },
                  { title: 'Follow-up', copy: 'You can filter the list, open pitch drafting, and export the final contacts.' },
                ]}
                downloads={['Excel', 'Markdown', 'JSON']}
              />
            )}

            {job?.status === 'completed' && contacts.length === 0 && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
                No journalist contacts were found for this topic and location. Try switching between specific and broad mode, widening outlet scope, or adding a desk like Health or Technology.
              </div>
            )}

            {job?.status === 'completed' && contacts.length > 0 && (
              <>
                <div className="app-output-header !mb-2">Media List</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="rounded-xl bg-black/20 border border-white/10 px-4 py-3">
                    <div className="text-slate-500 text-xs uppercase tracking-wider">Requested / Returned</div>
                    <div className="text-white text-2xl mt-1">{rd?.requested_contacts || contacts.length} / {rd?.returned_contacts || contacts.length}</div>
                  </div>
                  {Object.entries(rd?.coverage_by_media_type || typeCounts).slice(0, 3).map(([type, count]) => (
                    <div key={type} className="rounded-xl bg-black/20 border border-white/10 px-4 py-3">
                      <div className="text-slate-500 text-xs uppercase tracking-wider">{MEDIA_TYPE_LABELS[type] || type}</div>
                      <div className="text-white text-2xl mt-1">{count}</div>
                    </div>
                  ))}
                </div>

                {rd?.result_quality === 'partial' && (
                  <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
                    This run produced a constrained list. Review the coverage notes before using it as a full outreach set.
                  </div>
                )}

                {rd?.pitch_timing && (
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-200 text-sm">
                    <strong>Pitch Timing:</strong> {rd.pitch_timing}
                  </div>
                )}

                {rd?.coverage_notes?.length > 0 && (
                  <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-4 text-sm">
                    <div className="text-slate-400 uppercase tracking-wider text-xs mb-2">Coverage Notes</div>
                    <div className="space-y-1">
                      {rd.coverage_notes.map((note, index) => (
                        <p key={index} className="text-slate-300">{note}</p>
                      ))}
                    </div>
                  </div>
                )}

                {rd?.news_research?.length > 0 && (
                  <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-4 text-sm">
                    <div className="text-slate-400 uppercase tracking-wider text-xs mb-2">Top Reporting Used</div>
                    <div className="space-y-2">
                      {rd.news_research.slice(0, 4).map((article, index) => (
                        <div key={`${article.url}-${index}`} className="text-slate-300">
                          <a href={article.url} target="_blank" rel="noreferrer" className="text-violet-300 underline">
                            {article.title || 'View story'}
                          </a>
                          <span className="text-slate-500"> · {article.source || 'Unknown outlet'} · relevance {article.relevance_score ?? '—'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="field-label mb-2">Filter By Media Type</div>
                  <div className="flex flex-wrap gap-3">
                    {Object.keys(typeCounts).map((type) => (
                      <label key={type} className="flex items-center gap-2 text-sm text-slate-300">
                          <input data-testid={`toggle-media-list-filter-${type}`} type="checkbox" checked={visibleTypes.includes(type)} onChange={() => toggleFilterType(type)} className="accent-violet-500" />
                        <span>{MEDIA_TYPE_LABELS[type] || type}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </form>

        {job?.status === 'completed' && contacts.length === 0 && (
          <div className="mt-10">
            <div className="glass-card p-8 rounded-xl border border-white/10 bg-black/20 text-sm text-slate-400">
              No visible contacts were returned for this run. Try broad mode with a desk selection, changing geographic scope, or adjusting media types.
            </div>
          </div>
        )}

        {job?.status === 'completed' && contacts.length > 0 && (
          <div className="mt-10 space-y-6">
            <div className="glass-card p-6 overflow-x-auto">
              <table className="w-full text-sm text-left text-slate-300">
                <thead className="text-slate-500 uppercase tracking-wider text-xs border-b border-white/10">
                  <tr>
                    <th className="py-3 pr-4">Name</th>
                    <th className="py-3 pr-4">Confidence</th>
                    <th className="py-3 pr-4">Outlet</th>
                    <th className="py-3 pr-4">Role</th>
                    <th className="py-3 pr-4">Media Type</th>
                    <th className="py-3 pr-4">Location</th>
                    <th className="py-3 pr-4">Pitch Angle</th>
                    <th className="py-3 pr-4">Email</th>
                    <th className="py-3 pr-4">Evidence</th>
                    <th className="py-3 pr-4">Pitch</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredContacts.map((contact, index) => (
                    <tr key={`${contact.outlet}-${index}`} className="border-b border-white/5 align-top">
                      <td className="py-3 pr-4">
                        {[contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.host_name || (contact.media_type === 'podcast' ? 'Host to verify' : '—')}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                            contact.contact_status === 'story_lead' || contact.contact_status === 'show_only_verify_host'
                              ? 'bg-amber-500/15 text-amber-200 border border-amber-400/20'
                              : contact.contact_status === 'low_confidence_named'
                                ? 'bg-sky-500/15 text-sky-200 border border-sky-400/20'
                                : 'bg-emerald-500/15 text-emerald-200 border border-emerald-400/20'
                          }`}
                        >
                          {contact.contact_status === 'story_lead'
                            ? 'Story Lead'
                            : contact.contact_status === 'show_only_verify_host'
                              ? 'Show Match'
                              : contact.contact_status === 'identified_no_contact'
                                ? 'Host Identified'
                                : contact.contact_status === 'identified_with_contact'
                                  ? 'Host + Contact'
                            : contact.contact_status === 'low_confidence_named'
                              ? 'Low Confidence'
                              : 'Verified'}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        {contact.outlet_website ? <a href={contact.outlet_website.startsWith('http') ? contact.outlet_website : `https://${contact.outlet_website}`} target="_blank" rel="noreferrer" className="text-violet-300 underline">{contact.outlet}</a> : (contact.outlet || '—')}
                      </td>
                      <td className="py-3 pr-4">
                        <div>{contact.role || '—'}</div>
                        {(contact.contact_status === 'story_lead' || contact.contact_status === 'low_confidence_named' || contact.contact_status === 'show_only_verify_host') && (
                          <div className="mt-1 text-[11px] text-slate-500">Role inferred from story evidence</div>
                        )}
                        {contact.media_type === 'podcast' && contact.platform && (
                          <div className="mt-1 text-[11px] text-slate-500">{contact.platform}</div>
                        )}
                      </td>
                      <td className="py-3 pr-4">{MEDIA_TYPE_LABELS[contact.media_type] || contact.media_type || '—'}</td>
                      <td className="py-3 pr-4">{contact.location || '—'}</td>
                      <td className="py-3 pr-4">{contact.pitch_angle || '—'}</td>
                      <td className="py-3 pr-4">
                        <div>{contact.email || '—'}</div>
                        {!contact.email && (
                          <div className="mt-1 text-[11px] text-slate-500">
                            {contact.contact_status === 'story_lead' || contact.contact_status === 'show_only_verify_host'
                              ? 'Email not verified'
                              : contact.contact_status === 'identified_no_contact'
                                ? 'Host identified; no direct contact published'
                              : contact.contact_status === 'low_confidence_named'
                                ? 'Email omitted pending verification'
                                : 'Email not found'}
                          </div>
                        )}
                      </td>
                      <td className="py-3 pr-4">
                        {(contact.matched_url || contact.previous_story_url) ? (
                          <div>
                            <a
                              href={(contact.matched_url || contact.previous_story_url).startsWith('http') ? (contact.matched_url || contact.previous_story_url) : `https://${contact.matched_url || contact.previous_story_url}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-violet-300 underline"
                            >
                              {contact.matched_title || contact.previous_story_title || 'View evidence'}
                            </a>
                            {contact.media_type === 'podcast' && contact.matched_evidence_type && (
                              <div className="mt-1 text-[11px] text-slate-500">{contact.matched_evidence_type.replace('_', ' ')}</div>
                            )}
                          </div>
                        ) : (contact.matched_title || contact.previous_story_title || '—')}
                      </td>
                      <td className="py-3 pr-4">
                        <button
                          data-testid={`open-media-list-pitch-${index}`}
                          onClick={() => setPitchContact(contact)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600/20 hover:bg-violet-600/40 border border-violet-500/30 text-violet-300 text-xs transition-colors whitespace-nowrap"
                        >
                          <EnvelopeSimple size={13} /> Draft Pitch
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button data-testid="download-media-list-xlsx" onClick={() => downloadArtifact(artifactMap['media_list.xlsx'])}
                className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
                <DownloadSimple size={18} /> Download Excel
              </button>
              <button data-testid="download-media-list-markdown" onClick={() => downloadText(job?.result_data?.markdown || '', 'media_list.md')}
                className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                <DownloadSimple size={18} /> Download Markdown
              </button>
              <button data-testid="download-media-list-json" onClick={() => downloadJson(rd || {}, 'media_list.json')}
                className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                <DownloadSimple size={18} /> Download JSON
              </button>
            </div>
          </div>
        )}
      </motion.div>
    </>
  );
}
