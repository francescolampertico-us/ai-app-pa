/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';

const MEDIA_TYPES = [
  ['mainstream', 'Mainstream'],
  ['print', 'Print'],
  ['broadcast', 'Broadcast (TV/Radio)'],
  ['digital', 'Digital / Online'],
  ['trade', 'Trade / Policy'],
  ['podcast', 'Podcast'],
];
const MEDIA_TYPE_LABELS = Object.fromEntries(MEDIA_TYPES);

export default function MediaListBuilder() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('media_list_builder');

  const [issue, setIssue] = useState('');
  const [locationType, setLocationType] = useState('National (US)');
  const [location, setLocation] = useState('');
  const [numContacts, setNumContacts] = useState(20);
  const [selectedTypes, setSelectedTypes] = useState(['mainstream', 'print', 'broadcast', 'digital', 'trade']);
  const [filterTypes, setFilterTypes] = useState([]);

  const result = job?.result_data?.result;
  const contacts = useMemo(() => result?.contacts || [], [result]);
  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  const resolvedLocation = locationType === 'National (US)' ? 'US' : location;

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
    payload.append('location', resolvedLocation || 'US');
    payload.append('num_contacts', String(numContacts));
    payload.append('media_types', selectedTypes.join(','));
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
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Media List Builder</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '68ch', fontWeight: 300 }}>
          Generates a targeted media pitch list based on a policy issue, geographic scope, and media type filter, then returns Excel, markdown, and JSON outputs.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div>
            <label className="field-label">Policy Issue To Pitch</label>
            <textarea value={issue} onChange={(event) => setIssue(event.target.value)}
              className="field resize-none" rows={4}
              placeholder="e.g. AI safety regulation and mandatory pre-deployment testing requirements" required />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="field-label">Geographic Scope</label>
              <select value={locationType} onChange={(event) => setLocationType(event.target.value)} className="field">
                <option>National (US)</option>
                <option>State</option>
                <option>City / Metro</option>
              </select>
            </div>
            <div>
              <label className="field-label">{locationType === 'State' ? 'State' : 'City / Metro'}</label>
              <input value={location} onChange={(event) => setLocation(event.target.value)}
                className="field" disabled={locationType === 'National (US)'}
                placeholder={locationType === 'State' ? 'e.g. California' : 'e.g. Washington DC'} />
            </div>
            <div>
              <label className="field-label">Number Of Contacts</label>
              <input type="range" min="5" max="40" step="5" value={numContacts} onChange={(event) => setNumContacts(Number(event.target.value))}
                className="w-full accent-violet-500 mt-4" />
              <div className="text-sm text-slate-400 mt-2">{numContacts}</div>
            </div>
          </div>

          <div>
            <label className="field-label">Media Types To Include</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {MEDIA_TYPES.map(([value, label]) => (
                <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="checkbox" checked={selectedTypes.includes(value)} onChange={() => toggleSelectedType(value)} className="accent-violet-500" />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>

          <button type="submit" disabled={loading || !issue.trim() || selectedTypes.length === 0}
            className="btn-primary mt-auto">
            {loading ? <><SpinnerGap size={18} className="animate-spin" /> Building…</> : <>Build Media List <ArrowRight size={18} /></>}
          </button>
        </div>

        <div className="glass-card p-8 flex flex-col gap-5">
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
            Review required. Journalist names, roles, and story links may be inaccurate or outdated. Verify all contacts before pitching.
          </div>

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
              Run the tool to generate the contact list and downloads.
            </div>
          )}

          {job?.status === 'completed' && contacts.length > 0 && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="rounded-xl bg-black/20 border border-white/10 px-4 py-3">
                  <div className="text-slate-500 text-xs uppercase tracking-wider">Total Contacts</div>
                  <div className="text-white text-2xl mt-1">{contacts.length}</div>
                </div>
                {Object.entries(typeCounts).slice(0, 3).map(([type, count]) => (
                  <div key={type} className="rounded-xl bg-black/20 border border-white/10 px-4 py-3">
                    <div className="text-slate-500 text-xs uppercase tracking-wider">{MEDIA_TYPE_LABELS[type] || type}</div>
                    <div className="text-white text-2xl mt-1">{count}</div>
                  </div>
                ))}
              </div>

              {result?.pitch_timing && (
                <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-200 text-sm">
                  <strong>Pitch Timing:</strong> {result.pitch_timing}
                </div>
              )}

              <div>
                <div className="field-label mb-2">Filter By Media Type</div>
                <div className="flex flex-wrap gap-3">
                  {Object.keys(typeCounts).map((type) => (
                    <label key={type} className="flex items-center gap-2 text-sm text-slate-300">
                      <input type="checkbox" checked={visibleTypes.includes(type)} onChange={() => toggleFilterType(type)} className="accent-violet-500" />
                      <span>{MEDIA_TYPE_LABELS[type] || type}</span>
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </form>

      {job?.status === 'completed' && contacts.length > 0 && (
        <div className="mt-10 space-y-6">
          <div className="glass-card p-6 overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-300">
              <thead className="text-slate-500 uppercase tracking-wider text-xs border-b border-white/10">
                <tr>
                  <th className="py-3 pr-4">Name</th>
                  <th className="py-3 pr-4">Outlet</th>
                  <th className="py-3 pr-4">Role</th>
                  <th className="py-3 pr-4">Media Type</th>
                  <th className="py-3 pr-4">Location</th>
                  <th className="py-3 pr-4">Pitch Angle</th>
                  <th className="py-3 pr-4">Previous Story</th>
                </tr>
              </thead>
              <tbody>
                {filteredContacts.map((contact, index) => (
                  <tr key={`${contact.outlet}-${index}`} className="border-b border-white/5 align-top">
                    <td className="py-3 pr-4">{[contact.first_name, contact.last_name].filter(Boolean).join(' ') || '—'}</td>
                    <td className="py-3 pr-4">
                      {contact.outlet_website ? <a href={contact.outlet_website.startsWith('http') ? contact.outlet_website : `https://${contact.outlet_website}`} target="_blank" rel="noreferrer" className="text-violet-300 underline">{contact.outlet}</a> : (contact.outlet || '—')}
                    </td>
                    <td className="py-3 pr-4">{contact.role || '—'}</td>
                    <td className="py-3 pr-4">{MEDIA_TYPE_LABELS[contact.media_type] || contact.media_type || '—'}</td>
                    <td className="py-3 pr-4">{contact.location || '—'}</td>
                    <td className="py-3 pr-4">{contact.pitch_angle || '—'}</td>
                    <td className="py-3 pr-4">
                      {contact.previous_story_url ? <a href={contact.previous_story_url.startsWith('http') ? contact.previous_story_url : `https://${contact.previous_story_url}`} target="_blank" rel="noreferrer" className="text-violet-300 underline">{contact.previous_story_title || 'View story'}</a> : (contact.previous_story_title || '—')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button onClick={() => downloadArtifact(artifactMap['media_list.xlsx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
              <DownloadSimple size={18} /> Download Excel
            </button>
            <button onClick={() => downloadText(job?.result_data?.markdown || '', 'media_list.md')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download Markdown
            </button>
            <button onClick={() => downloadJson(result || {}, 'media_list.json')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download JSON
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
