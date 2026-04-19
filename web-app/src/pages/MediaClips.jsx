/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap, BookmarkSimpleIcon as BookmarkSimple, TrashIcon as Trash } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';

const SAVED_SEARCHES_KEY = 'mediaClips_savedSearches';

function loadSavedSearches() {
  try {
    return JSON.parse(localStorage.getItem(SAVED_SEARCHES_KEY) || '[]');
  } catch {
    return [];
  }
}

function persistSavedSearches(searches) {
  localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(searches));
}

export default function MediaClips() {
  const clipsJob = useFastApiJob('media_clips');
  const cleanerJob = useFastApiJob('media_clip_cleaner');
  const standaloneCleanerJob = useFastApiJob('media_clip_cleaner');

  const [topic, setTopic] = useState('');
  const [queryMode, setQueryMode] = useState('Simple (keywords)');
  const [includeKeywords, setIncludeKeywords] = useState('');
  const [excludeKeywords, setExcludeKeywords] = useState('');
  const [queries, setQueries] = useState('');
  const [period, setPeriod] = useState('24h');
  const [targetDate, setTargetDate] = useState(new Date().toISOString().slice(0, 10));
  const [sourceFilter, setSourceFilter] = useState('Mainstream media only');
  const [customSources, setCustomSources] = useState('');
  const [sinceDate, setSinceDate] = useState('');
  const [maxClips, setMaxClips] = useState('20');
  const [clipsData, setClipsData] = useState([]);
  const [selectedClipIndex, setSelectedClipIndex] = useState(0);
  const [cleanerMode, setCleanerMode] = useState('llm');
  const [standaloneRawPaste, setStandaloneRawPaste] = useState('');
  const [standaloneMode, setStandaloneMode] = useState('llm');
  const [standaloneTitle, setStandaloneTitle] = useState('');
  const [llmModel, setLlmModel] = useState('ChangeAgent');
  const [savedSearches, setSavedSearches] = useState(() => loadSavedSearches());
  const [selectedSaved, setSelectedSaved] = useState('');
  const [emailTo, setEmailTo] = useState('');
  const [emailSender, setEmailSender] = useState('');
  const [emailStatus, setEmailStatus] = useState(null); // null | 'sending' | 'ok' | 'error'
  const [emailError, setEmailError] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [showEmailPreview, setShowEmailPreview] = useState(false);
  const processedCleanerJobId = useRef(null);
  const isBuildReportRef = useRef(false);
  const cleanerTargetIndexRef = useRef(0);

  const artifactMap = useMemo(
    () => (clipsJob.job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [clipsJob.job?.artifacts],
  );
  const selectedClip = clipsData[selectedClipIndex] || null;

  // Sanitize and format a single exclusion term — strips stray quotes, then wraps in -"..."
  const formatExclusion = (term) => `-"${term.replace(/"/g, '').trim()}"`;

  const generatedQuery = useMemo(() => {
    const include = includeKeywords.split(',').map((item) => item.trim()).filter(Boolean);
    if (!include.length) return '';
    const includeString = include.map((item) => `"${item}"`).join(' OR ');
    const exclude = excludeKeywords.split(',').map((item) => item.trim()).filter(Boolean);
    if (!exclude.length) return includeString;
    return `(${includeString}) ${exclude.map(formatExclusion).join(' ')}`;
  }, [includeKeywords, excludeKeywords]);

  // Effective Boolean queries — shows exactly what will be sent to GNews
  const effectiveBooleanQueries = useMemo(() => {
    if (queryMode !== 'Advanced (Boolean)' || !queries.trim()) return '';
    const exclusions = excludeKeywords
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
      .map(formatExclusion)
      .join(' ');
    return queries
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => exclusions ? `${line} ${exclusions}` : line)
      .join('\n');
  }, [queryMode, queries, excludeKeywords]);

  useEffect(() => {
    if (clipsJob.job?.status === 'completed') {
      if (clipsJob.job?.result_data?.email_body) {
        setEmailBody(clipsJob.job.result_data.email_body);
      }
      // Only overwrite clipsData for the initial generation, not for build_report.
      // During a build_report, the user may have cleaned more articles while waiting —
      // overwriting would lose those changes.
      if (!isBuildReportRef.current && Array.isArray(clipsJob.job?.result_data?.clips_data)) {
        setClipsData(clipsJob.job.result_data.clips_data);
        setSelectedClipIndex(0);
      }
      isBuildReportRef.current = false;
    }
  }, [clipsJob.job]);

  useEffect(() => {
    if (
      cleanerJob.job?.status === 'completed' &&
      cleanerJob.job.id !== processedCleanerJobId.current
    ) {
      processedCleanerJobId.current = cleanerJob.job.id;
      // Use the index captured at submission time, not the current selectedClipIndex,
      // so changing the selection while the cleaner runs doesn't update the wrong article.
      const targetIndex = cleanerTargetIndexRef.current;
      setClipsData((prev) => prev.map((clip, index) => (
        index === targetIndex
          ? { ...clip, extracted_text: cleanerJob.job.result_data.cleaned_text, has_full_text: true }
          : clip
      )));
    }
  }, [cleanerJob.job]);

  const buildCurrentConfig = () => ({
    topic, queryMode, includeKeywords, excludeKeywords, queries,
    period, targetDate, sourceFilter, customSources, sinceDate, maxClips,
  });

  const saveSearch = () => {
    const name = topic.trim() || 'Untitled';
    const ts = new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const entry = { id: Date.now(), name: `${name} (${ts})`, config: buildCurrentConfig() };
    const updated = [entry, ...savedSearches].slice(0, 20); // keep max 20
    setSavedSearches(updated);
    persistSavedSearches(updated);
    setSelectedSaved(String(entry.id));
  };

  const loadSearch = (id) => {
    const entry = savedSearches.find((s) => String(s.id) === String(id));
    if (!entry) return;
    const c = entry.config;
    setTopic(c.topic ?? '');
    setQueryMode(c.queryMode ?? 'Simple (keywords)');
    setIncludeKeywords(c.includeKeywords ?? '');
    setExcludeKeywords(c.excludeKeywords ?? '');
    setQueries(c.queries ?? '');
    setPeriod(c.period ?? '24h');
    setTargetDate(c.targetDate ?? new Date().toISOString().slice(0, 10));
    setSourceFilter(c.sourceFilter ?? 'Mainstream media only');
    setCustomSources(c.customSources ?? '');
    setSinceDate(c.sinceDate ?? '');
    setMaxClips(c.maxClips ?? '20');
    setSelectedSaved(String(id));
  };

  const deleteSavedSearch = (id) => {
    const updated = savedSearches.filter((s) => String(s.id) !== String(id));
    setSavedSearches(updated);
    persistSavedSearches(updated);
    if (selectedSaved === String(id)) setSelectedSaved('');
  };

  const handleGenerate = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('topic', topic);

    // For Boolean mode, append sanitized exclusions to every query line
    // (Simple mode exclusions are already baked into generatedQuery via the useMemo)
    const finalQueries = queryMode === 'Simple (keywords)'
      ? generatedQuery
      : effectiveBooleanQueries || queries.trim();
    payload.append('queries', finalQueries);
    payload.append('period', period);
    payload.append('target_date', targetDate);
    payload.append('source_filter', sourceFilter);
    payload.append('custom_sources', customSources);
    payload.append('since', sinceDate);
    payload.append('max_clips', maxClips);
    payload.append('llm_model', llmModel);
    clipsJob.submitJob(payload);
  };

  const buildFinalReport = () => {
    isBuildReportRef.current = true;
    const payload = new FormData();
    payload.append('action', 'build_report');
    payload.append('report_topic', topic);
    payload.append('report_date_str', targetDate);
    payload.append('clips_data_json', JSON.stringify(clipsData));
    clipsJob.submitJob(payload);
  };

  const removeClip = (indexToRemove) => {
    setClipsData((prev) => {
      const next = prev.filter((_, index) => index !== indexToRemove);
      setSelectedClipIndex((current) => {
        if (next.length === 0) return 0;
        if (current > indexToRemove) return current - 1;
        return Math.min(current, next.length - 1);
      });
      return next;
    });
  };

  const updateClip = (indexToUpdate, updates) => {
    setClipsData((prev) => prev.map((clip, index) => (
      index === indexToUpdate ? { ...clip, ...updates } : clip
    )));
  };

  const updateSelectedClipText = (text) => {
    if (selectedClipIndex < 0 || selectedClipIndex >= clipsData.length) return;
    updateClip(selectedClipIndex, {
      extracted_text: text,
      has_full_text: Boolean(text.trim()),
    });
  };

  const runCleaner = () => {
    const currentClip = clipsData[selectedClipIndex];
    const sourceText = currentClip?.extracted_text || '';
    if (!sourceText.trim()) return;
    // Capture the target index now so the completion handler updates the right article
    // even if the user changes the selection while the cleaner is running.
    cleanerTargetIndexRef.current = selectedClipIndex;
    const payload = new FormData();
    payload.append('raw_text', sourceText);
    payload.append('mode', cleanerMode);
    payload.append('fallback_local', 'true');
    payload.append('title', currentClip?.title || '');
    cleanerJob.submitJob(payload);
  };

  const runStandaloneCleaner = () => {
    if (!standaloneRawPaste.trim()) return;
    const payload = new FormData();
    payload.append('raw_text', standaloneRawPaste);
    payload.append('mode', standaloneMode);
    payload.append('fallback_local', 'true');
    payload.append('title', standaloneTitle.trim());
    standaloneCleanerJob.submitJob(payload);
  };

  const openInMail = async () => {
    if (!clipsJob.job?.id || !emailTo.trim()) return;
    setEmailStatus('sending');
    setEmailError('');
    try {
      const payload = new FormData();
      payload.append('job_id', clipsJob.job.id);
      payload.append('to', emailTo.trim());
      payload.append('subject', `${topic || 'Media Clips'} - ${targetDate}`);
      if (emailSender.trim()) payload.append('sender', emailSender.trim());
      const res = await fetch('http://localhost:8000/api/tools/open-email-draft', { method: 'POST', body: payload });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Unknown error');
      }
      setEmailStatus('ok');
    } catch (err) {
      setEmailStatus('error');
      setEmailError(err.message);
    }
  };

  const missingCount = clipsData.filter((clip) => !clip.has_full_text).length;

  return (
    <motion.div data-testid="tool-page-media-clips" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-10 max-w-6xl mx-auto relative z-10">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)', marginBottom: 10 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect · TOOL
        </div>
        <h1 data-testid="page-title-media-clips" className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Media Clips</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '72ch', fontWeight: 300 }}>
          Search Google News with keyword or Boolean queries, review and clean extracted article text, then rebuild the final report and email draft files.
        </p>
        <div className="mt-3"><ModelSelector value={llmModel} onChange={setLlmModel} /></div>
      </header>

      <ResearchPrototypeNote
        category="Policy Monitoring & Legislative Tracking"
        message="This prototype module supports recurring media monitoring and clip production. It is designed to accelerate collection and synthesis, but article extraction, outlet selection, and downstream summaries still require manual verification before external circulation."
      />

      {/* ── Saved Searches bar ── */}
      <div className="mb-6 glass-card px-5 py-4 flex flex-wrap items-center gap-3">
        <BookmarkSimple size={16} className="text-violet-400 shrink-0" />
        <span className="text-slate-400 text-sm shrink-0">Saved searches</span>

        {savedSearches.length > 0 ? (
          <select
            data-testid="saved-media-clips-select"
            value={selectedSaved}
            onChange={(e) => loadSearch(e.target.value)}
            className="field flex-1 min-w-0 text-sm py-1.5"
            style={{ maxWidth: 340 }}
          >
            <option value="">— load a saved search —</option>
            {savedSearches.map((s) => (
              <option key={s.id} value={String(s.id)}>{s.name}</option>
            ))}
          </select>
        ) : (
          <span className="text-slate-600 text-sm italic">No saved searches yet.</span>
        )}

        {selectedSaved && (
          <button
            data-testid="delete-media-clips-search"
            type="button"
            onClick={() => deleteSavedSearch(selectedSaved)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs hover:bg-red-500/20 transition-colors"
          >
            <Trash size={13} /> Delete
          </button>
        )}

        <button
          data-testid="save-media-clips-search"
          type="button"
          onClick={saveSearch}
          disabled={!topic.trim()}
          className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-xs hover:bg-violet-500/30 transition-colors disabled:opacity-40"
        >
          <BookmarkSimple size={13} /> Save current search
        </button>
      </div>

      <form onSubmit={handleGenerate} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div>
            <label className="field-label">Report Topic / Title</label>
            <input data-testid="input-media-clips-topic" value={topic} onChange={(event) => setTopic(event.target.value)} className="field" placeholder="e.g. India Media Clips" required />
          </div>

          <div>
            <label className="field-label">Query Mode</label>
            <div className="flex flex-wrap gap-4 pt-2">
              {['Simple (keywords)', 'Advanced (Boolean)'].map((mode) => (
                <label key={mode} className="flex items-center gap-2 text-sm text-slate-300">
                  <input data-testid={`toggle-media-clips-query-mode-${mode === 'Simple (keywords)' ? 'simple' : 'advanced'}`} type="radio" checked={queryMode === mode} onChange={() => setQueryMode(mode)} className="accent-violet-500" />
                  <span>{mode}</span>
                </label>
              ))}
            </div>
          </div>

          {queryMode === 'Simple (keywords)' ? (
            <>
              <div>
                <label className="field-label">Keywords To Include</label>
                <input data-testid="input-media-clips-include-keywords" value={includeKeywords} onChange={(event) => setIncludeKeywords(event.target.value)} className="field" placeholder="e.g. India, elections, Modi" />
              </div>
              <div>
                <label className="field-label">Keywords To Exclude (Optional)</label>
                <input data-testid="input-media-clips-exclude-keywords" value={excludeKeywords} onChange={(event) => setExcludeKeywords(event.target.value)} className="field" placeholder="e.g. cricket, Bollywood" />
              </div>
              {generatedQuery && <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100 text-sm"><strong>Generated query:</strong> {generatedQuery}</div>}
            </>
          ) : (
            <>
              <div>
                <label className="field-label">Search Queries (One Per Line)</label>
                <textarea data-testid="input-media-clips-queries" value={queries} onChange={(event) => setQueries(event.target.value)}
                  className="field resize-none" rows={5}
                  placeholder={'"India" AND ("elections" OR "Modi")\n"New Delhi" AND "trade"'} required />
              </div>
              <div>
                <label className="field-label">Exclude Words / Phrases (Optional)</label>
                <input value={excludeKeywords} onChange={(event) => setExcludeKeywords(event.target.value)} className="field"
                  placeholder="e.g. cricket, Bollywood" />
                <p className="text-xs text-slate-500 mt-1">Comma-separated. Each term is appended as <code className="text-violet-400">-"term"</code> to every query line.</p>
              </div>
              {effectiveBooleanQueries && (
                <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100 text-xs space-y-1">
                  <p className="font-semibold text-violet-300">Effective queries sent to GNews:</p>
                  {effectiveBooleanQueries.split('\n').map((line, i) => (
                    <p key={i} className="font-mono break-all">{line}</p>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div className="glass-card p-8 flex flex-col gap-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="field-label">Search Period</label>
              <select value={period} onChange={(event) => setPeriod(event.target.value)} className="field">
                {['24h', '12h', '72h', '7d'].map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Target Date</label>
              <input type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} className="field" />
            </div>
            <div>
              <label className="field-label">Source Filter</label>
              <select data-testid="input-media-clips-source-filter" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} className="field">
                {['Mainstream media only', 'All sources', 'Custom'].map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
          </div>

          {sourceFilter === 'Custom' && (
            <div>
              <label className="field-label">Custom Trusted Domains (One Per Line)</label>
              <textarea data-testid="input-media-clips-custom-sources" value={customSources} onChange={(event) => setCustomSources(event.target.value)} className="field resize-none" rows={4} placeholder={'nytimes.com\npolitico.com\nyourcustomsource.com'} />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="field-label">Filter Since (Optional)</label>
              <input value={sinceDate} onChange={(event) => setSinceDate(event.target.value)} className="field" placeholder="YYYY-MM-DD HH:MM" />
            </div>
            <div>
              <label className="field-label">Max Articles</label>
              <select value={maxClips} onChange={(event) => setMaxClips(event.target.value)} className="field">
                {['10', '15', '20', '25', 'All'].map((v) => <option key={v} value={v === 'All' ? 'all' : v}>{v}</option>)}
              </select>
            </div>
          </div>

          <button data-testid="submit-media-clips" type="submit" disabled={clipsJob.loading || !topic.trim() || !(queryMode === 'Simple (keywords)' ? generatedQuery : queries.trim())} className="btn-primary mt-auto">
            {clipsJob.loading ? <><SpinnerGap size={18} className="animate-spin" /> Generating…</> : <>Generate Clips Report <ArrowRight size={18} /></>}
          </button>
        </div>
      </form>

      {(clipsJob.job || cleanerJob.job) && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {clipsJob.job && (
            <div data-testid="status-media-clips" className="glass-card p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs text-purple-300">{clipsJob.job.id.slice(0, 8).toUpperCase()}</span>
                <span className={clipsJob.job.status === 'completed' ? 'badge-complete' : clipsJob.job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>{clipsJob.job.status}</span>
              </div>
              <p className="text-slate-300 text-sm mb-4">{clipsJob.job.message}</p>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${clipsJob.job.progress || 0}%` }} /></div>
            </div>
          )}
          {cleanerJob.job && (
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs text-purple-300">{cleanerJob.job.id.slice(0, 8).toUpperCase()}</span>
                <span className={cleanerJob.job.status === 'completed' ? 'badge-complete' : cleanerJob.job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>{cleanerJob.job.status}</span>
              </div>
              <p className="text-slate-300 text-sm mb-4">{cleanerJob.job.message}</p>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${cleanerJob.job.progress || 0}%` }} /></div>
            </div>
          )}
        </div>
      )}

      {clipsJob.job?.result_data?.stdout && (
        <details className="glass-card p-6 mt-8">
          <summary className="cursor-pointer text-white font-semibold">Pipeline Log</summary>
          <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{clipsJob.job.result_data.stdout}</pre>
        </details>
      )}

      {clipsJob.job?.result_data?.stderr && (
        <details className="glass-card p-6 mt-6">
          <summary className="cursor-pointer text-white font-semibold">Errors / Warnings</summary>
          <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{clipsJob.job.result_data.stderr}</pre>
        </details>
      )}

      <section data-testid="media-clip-cleaner-panel" className="glass-card p-8 space-y-5 mt-8">
        <h2 data-testid="standalone-clip-cleaner-title" style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: '#A78BFA' }}>Clip Cleaner</h2>
        <p className="text-slate-400 text-sm">
          Paste raw article text to strip ads, navigation, and boilerplate. Use standalone or as part of the clips workflow below.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="field-label">Cleaning Mode</label>
            <div className="flex gap-4 pt-3">
              {[['llm', 'LLM (recommended)'], ['local', 'Local (rule-based)']].map(([value, label]) => (
                <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                      <input data-testid={`toggle-standalone-clip-cleaner-${value}`} type="radio" checked={standaloneMode === value} onChange={() => setStandaloneMode(value)} className="accent-violet-500" />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="field-label">Article Headline (optional)</label>
            <input
              value={standaloneTitle}
              onChange={(e) => setStandaloneTitle(e.target.value)}
              className="field"
              placeholder="Paste the article title to help remove it from output"
            />
          </div>
        </div>
        <div>
          <label className="field-label">Paste Raw Article Text</label>
          <textarea data-testid="input-standalone-clip-cleaner-raw" value={standaloneRawPaste} onChange={e => setStandaloneRawPaste(e.target.value)}
            className="field resize-none" rows={10}
            placeholder="Copy the full article text from the webpage and paste it here..." />
        </div>
        <button data-testid="submit-standalone-clip-cleaner" onClick={runStandaloneCleaner} disabled={standaloneCleanerJob.loading || !standaloneRawPaste.trim()}
          className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm">
          {standaloneCleanerJob.loading ? <><SpinnerGap size={16} className="inline mr-2 animate-spin" />Cleaning…</> : 'Clean Article Text'}
        </button>
        {standaloneCleanerJob.job?.status === 'completed' && (
          <div className="space-y-3">
            <textarea value={standaloneCleanerJob.job.result_data?.cleaned_text || ''} readOnly className="field resize-none" rows={10} />
            <button onClick={() => {
              const text = standaloneCleanerJob.job.result_data?.cleaned_text || '';
              navigator.clipboard.writeText(text);
            }} className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm">
              Copy to Clipboard
            </button>
          </div>
        )}
        {standaloneCleanerJob.job && standaloneCleanerJob.job.status !== 'completed' && (
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs text-purple-300">{standaloneCleanerJob.job.id.slice(0, 8).toUpperCase()}</span>
              <span className={standaloneCleanerJob.job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>{standaloneCleanerJob.job.status}</span>
            </div>
            <p className="text-slate-300 text-sm mb-3">{standaloneCleanerJob.job.message}</p>
            <div className="progress-track"><div className="progress-fill" style={{ width: `${standaloneCleanerJob.job.progress || 0}%` }} /></div>
          </div>
        )}
      </section>

      {clipsJob.job?.status === 'completed' && clipsData.length === 0 && (
        <div className="mt-10 rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm space-y-1">
          <p className="font-semibold">No matching articles found in the selected {period} window.</p>
          <p className="text-amber-300/80">Consider expanding to 7 days or broadening your search query.</p>
        </div>
      )}

      {clipsData.length > 0 && (
        <div className="mt-10 space-y-8">
          <div className="flex items-center gap-3 mb-2">
            <div style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)' }}>
              Str<span style={{ color: '#A78BFA' }}>α</span>tegitect
            </div>
            <span style={{ color: 'rgba(255,255,255,0.15)' }}>·</span>
            <span className="font-serif text-lg text-slate-200">Media Clips</span>
          </div>
          <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100 text-sm">
            Found {clipsData.length} articles. {missingCount} article(s) still need article text review or paste-in.
          </div>

          <section className="glass-card p-8 space-y-4">
            <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: '#A78BFA' }}>Review Articles</h2>
            <p className="text-slate-400 text-sm">
              The initial run does a light cleanup for speed. Click any article row to expand its inline editor, then edit, paste, clean further, or remove it.
            </p>
            <div className="space-y-3">
              {clipsData.map((clip, index) => (
                <div key={`${clip.title}-${index}`}
                  className={`rounded-xl border px-5 py-4 space-y-4 ${index === selectedClipIndex ? 'border-violet-400/40 bg-violet-500/10' : clip.has_full_text ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-white/10 bg-black/20'}`}>
                  <div className="flex items-start justify-between gap-4">
                    <button
                      type="button"
                      onClick={() => setSelectedClipIndex(index)}
                      className="flex items-start gap-3 min-w-0 flex-1 text-left cursor-pointer"
                    >
                      <span className="shrink-0 text-base">{clip.has_full_text ? '✅' : '❌'}</span>
                      <div className="min-w-0">
                        <p className="text-slate-200 text-sm truncate">{index + 1}. <strong>{clip.source}</strong>: {clip.title}</p>
                        <p className="text-slate-500 text-xs mt-0.5">{clip.author || 'Staff'} · {clip.date}</p>
                      </div>
                    </button>
                    <div className="flex items-center gap-3 shrink-0">
                      {clip.url && <a href={clip.url} target="_blank" rel="noreferrer" className="text-violet-300 text-xs underline hover:text-violet-200">Open</a>}
                      <button
                        type="button"
                        onClick={() => setSelectedClipIndex(index)}
                        className="text-xs px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 hover:bg-violet-500/30 transition-colors"
                      >
                        {index === selectedClipIndex ? 'Expanded' : 'Review'}
                      </button>
                      <button
                        data-testid={`remove-media-clips-article-${index}`}
                        onClick={() => removeClip(index)}
                        className="text-xs px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 hover:bg-red-500/20 transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  {index === selectedClipIndex && (
                    <div className="border-t border-white/10 pt-4 space-y-4">
                      <div className="rounded-xl border border-violet-400/20 bg-violet-500/10 px-4 py-3">
                        <p className="text-violet-200 text-sm font-medium">Expanded article editor</p>
                        <p className="text-slate-400 text-xs mt-1">Edit author and text here. Changes apply immediately to this article.</p>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="field-label">Cleaning Mode</label>
                          <div className="flex gap-4 pt-3">
                            {[['llm', 'LLM (recommended)'], ['local', 'Local (rule-based)']].map(([value, label]) => (
                              <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                                <input data-testid={`toggle-media-clips-cleaner-${value}`} type="radio" checked={cleanerMode === value} onChange={() => setCleanerMode(value)} className="accent-violet-500" />
                                <span>{label}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                        <div className="rounded-xl border border-white/10 bg-black/20 px-4 py-3 space-y-1">
                          <p className="text-slate-200 text-sm"><strong>{clip.source}</strong>: {clip.title}</p>
                          <p className="text-slate-500 text-xs">{clip.author || 'Staff'} · {clip.date}</p>
                          <p className="text-slate-400 text-xs">{clip.url || 'No source URL available'}</p>
                        </div>
                      </div>

                      <div>
                        <label className="field-label">Author</label>
                        <input
                          data-testid="input-media-clips-author"
                          value={clip.author || ''}
                          onChange={(event) => updateClip(index, { author: event.target.value })}
                          className="field"
                          placeholder="Add or edit the author name"
                        />
                      </div>

                      <div>
                        <label className="field-label">Article Text</label>
                        <textarea
                          data-testid="input-media-clips-cleaner-raw"
                          value={clip.extracted_text || ''}
                          onChange={(event) => updateClip(index, {
                            extracted_text: event.target.value,
                            has_full_text: Boolean(event.target.value.trim()),
                          })}
                          className="field resize-none"
                          rows={12}
                          placeholder="Paste the article text here if extraction missed it, or edit the preview manually before building the report."
                        />
                        <p className="text-xs text-slate-500 mt-2">
                          This text goes into the final report. Paste, edit, or run deeper cleaning only for this article.
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-3">
                        <button
                          data-testid="submit-media-clips-cleaner"
                          onClick={runCleaner}
                          disabled={cleanerJob.loading || !clip.extracted_text?.trim()}
                          className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm"
                        >
                          {cleanerJob.loading ? <><SpinnerGap size={16} className="inline mr-2 animate-spin" />Cleaning…</> : 'Clean Selected Article Further'}
                        </button>
                        <button
                          type="button"
                          onClick={() => updateClip(index, {
                            extracted_text: clip.description || '',
                            has_full_text: Boolean((clip.description || '').trim()),
                          })}
                          className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm disabled:opacity-40"
                        >
                          Reset To Snippet
                        </button>
                      </div>

                      {cleanerJob.job?.status === 'completed' && index === cleanerTargetIndexRef.current && (
                        <textarea
                          data-testid="output-media-clips-cleaner"
                          value={cleanerJob.job.result_data?.cleaned_text || ''}
                          readOnly
                          className="field resize-none"
                          rows={10}
                        />
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="glass-card p-8 space-y-5">
            <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: '#A78BFA' }}>Build Final Report</h2>
            <p className="text-slate-400 text-sm">
              Generates the final DOCX report and an email draft (plain text + HTML). Download buttons appear below after the job completes.
            </p>
            {missingCount > 0 && (
              <p className="text-slate-400 text-sm">{missingCount} article(s) are still missing full text. You can still build the report.</p>
            )}

            <button data-testid="submit-media-clips-build-report" onClick={buildFinalReport}
              className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm">
              Build Report + Email Draft
            </button>

            {Object.keys(artifactMap).length > 0 && (
              <div className="space-y-4">
                {/* Report downloads — match by extension since generate_clips.py uses dynamic filenames */}
                {(() => {
                  const reportFiles = (clipsJob.job?.artifacts || []).filter(a =>
                    (a.name.endsWith('.docx') || (a.name.endsWith('.json') && !a.name.includes('email')))
                  );
                  if (!reportFiles.length) return null;
                  return (
                    <div className="space-y-2">
                      <p className="text-slate-500 text-xs uppercase tracking-wider">Report Files</p>
                      <div className="flex flex-wrap gap-2">
                        {reportFiles.map(a => (
                          <button data-testid={`download-media-clips-artifact-${a.name}`} key={a.name} onClick={() => clipsJob.downloadArtifact(a)}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm">
                            <DownloadSimple size={15} /> {a.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })()}
                {/* Email draft */}
                {(clipsJob.job?.artifacts || []).filter(a => /media_clips_.*_email\.(txt|html)$/i.test(a.name)).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-slate-500 text-xs uppercase tracking-wider">Email Draft</p>
                    <div className="flex flex-wrap gap-2">
                      {(clipsJob.job?.artifacts || []).filter(a => /media_clips_.*_email\.(txt|html)$/i.test(a.name)).map(a => (
                        <button data-testid={`download-media-clips-artifact-${a.name}`} key={a.name} onClick={() => clipsJob.downloadArtifact(a)}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-500/10 border border-violet-400/20 text-violet-200 text-sm">
                          <DownloadSimple size={15} /> {a.name.endsWith('.txt') ? 'Plain Text (.txt)' : 'HTML (.html)'}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Inline email preview */}
                {emailBody && (
                  <div className="border-t border-white/10 pt-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-slate-500 text-xs uppercase tracking-wider">Email Draft Preview</p>
                      <button onClick={() => setShowEmailPreview(v => !v)}
                        className="text-xs text-violet-300 hover:text-violet-200 transition-colors">
                        {showEmailPreview ? 'Hide' : 'Show'}
                      </button>
                    </div>
                    {showEmailPreview && (
                      <pre className="whitespace-pre-wrap text-sm text-slate-300 bg-black/30 rounded-xl border border-white/10 p-5 max-h-96 overflow-y-auto font-sans leading-relaxed">
                        {emailBody}
                      </pre>
                    )}
                  </div>
                )}

                {/* Open in Mail */}
                <div className="border-t border-white/10 pt-5 space-y-4">
                  <p className="text-slate-500 text-xs uppercase tracking-wider">Send via Mail.app</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="field-label">To (comma-separated)</label>
                      <input data-testid="input-media-clips-email-to" value={emailTo} onChange={e => setEmailTo(e.target.value)} className="field" placeholder="recipient@example.com" />
                    </div>
                    <div>
                      <label className="field-label">From (optional)</label>
                      <input data-testid="input-media-clips-email-from" value={emailSender} onChange={e => setEmailSender(e.target.value)} className="field" placeholder="your@email.com" />
                    </div>
                  </div>
                  <button
                    data-testid="submit-open-email-draft"
                    onClick={openInMail}
                    disabled={!emailTo.trim() || emailStatus === 'sending'}
                    className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm hover:bg-violet-500/30 transition-colors disabled:opacity-50"
                  >
                    {emailStatus === 'sending' ? <><SpinnerGap size={15} className="inline mr-2 animate-spin" />Opening Mail…</> : 'Open Draft in Mail.app'}
                  </button>
                  {emailStatus === 'ok' && <p className="text-emerald-400 text-sm">Mail.app opened with draft ready to send.</p>}
                  {emailStatus === 'error' && <p className="text-red-400 text-sm">Error: {emailError}</p>}
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </motion.div>
  );
}
