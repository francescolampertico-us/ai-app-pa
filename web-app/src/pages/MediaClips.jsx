/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';

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
  const [clipsData, setClipsData] = useState([]);
  const [selectedClipIndex, setSelectedClipIndex] = useState(0);
  const [rawPaste, setRawPaste] = useState('');
  const [cleanerMode, setCleanerMode] = useState('llm');
  const [standaloneRawPaste, setStandaloneRawPaste] = useState('');
  const [standaloneMode, setStandaloneMode] = useState('llm');

  const artifactMap = useMemo(
    () => (clipsJob.job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [clipsJob.job?.artifacts],
  );

  const generatedQuery = useMemo(() => {
    const include = includeKeywords.split(',').map((item) => item.trim()).filter(Boolean);
    if (!include.length) return '';
    const includeString = include.map((item) => `"${item}"`).join(' OR ');
    const exclude = excludeKeywords.split(',').map((item) => item.trim()).filter(Boolean);
    if (!exclude.length) return includeString;
    return `(${includeString}) ${exclude.map((item) => `-"${item}"`).join(' ')}`;
  }, [includeKeywords, excludeKeywords]);

  useEffect(() => {
    if (clipsJob.job?.status === 'completed' && Array.isArray(clipsJob.job?.result_data?.clips_data)) {
      setClipsData(clipsJob.job.result_data.clips_data);
      setSelectedClipIndex(0);
    }
  }, [clipsJob.job]);

  useEffect(() => {
    if (cleanerJob.job?.status === 'completed' && clipsData[selectedClipIndex]) {
      setClipsData((prev) => prev.map((clip, index) => (
        index === selectedClipIndex
          ? { ...clip, extracted_text: cleanerJob.job.result_data.cleaned_text, has_full_text: true }
          : clip
      )));
      setRawPaste('');
    }
  }, [cleanerJob.job, clipsData, selectedClipIndex]);

  const handleGenerate = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('topic', topic);
    payload.append('queries', queryMode === 'Simple (keywords)' ? generatedQuery : queries);
    payload.append('period', period);
    payload.append('target_date', targetDate);
    payload.append('source_filter', sourceFilter);
    payload.append('custom_sources', customSources);
    payload.append('since', sinceDate);
    clipsJob.submitJob(payload);
  };

  const buildFinalReport = () => {
    const payload = new FormData();
    payload.append('action', 'build_report');
    payload.append('report_topic', topic);
    payload.append('report_date_str', targetDate);
    payload.append('clips_data_json', JSON.stringify(clipsData));
    clipsJob.submitJob(payload);
  };

  const runCleaner = () => {
    if (!rawPaste.trim()) return;
    const currentClip = clipsData[selectedClipIndex];
    const payload = new FormData();
    payload.append('raw_text', rawPaste);
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
    standaloneCleanerJob.submitJob(payload);
  };

  const currentClip = clipsData[selectedClipIndex];
  const missingCount = clipsData.filter((clip) => !clip.has_full_text).length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-10 max-w-6xl mx-auto relative z-10">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)', marginBottom: 10 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect · TOOL
        </div>
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Media Clips Generator</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '72ch', fontWeight: 300 }}>
          Search Google News with keyword or Boolean queries, review and clean extracted article text, then rebuild the final report and email draft files.
        </p>
      </header>

      <form onSubmit={handleGenerate} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div>
            <label className="field-label">Report Topic / Title</label>
            <input value={topic} onChange={(event) => setTopic(event.target.value)} className="field" placeholder="e.g. India Media Clips" required />
          </div>

          <div>
            <label className="field-label">Query Mode</label>
            <div className="flex flex-wrap gap-4 pt-2">
              {['Simple (keywords)', 'Advanced (Boolean)'].map((mode) => (
                <label key={mode} className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="radio" checked={queryMode === mode} onChange={() => setQueryMode(mode)} className="accent-violet-500" />
                  <span>{mode}</span>
                </label>
              ))}
            </div>
          </div>

          {queryMode === 'Simple (keywords)' ? (
            <>
              <div>
                <label className="field-label">Keywords To Include</label>
                <input value={includeKeywords} onChange={(event) => setIncludeKeywords(event.target.value)} className="field" placeholder="e.g. India, elections, Modi" />
              </div>
              <div>
                <label className="field-label">Keywords To Exclude (Optional)</label>
                <input value={excludeKeywords} onChange={(event) => setExcludeKeywords(event.target.value)} className="field" placeholder="e.g. cricket, Bollywood" />
              </div>
              {generatedQuery && <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100 text-sm"><strong>Generated query:</strong> {generatedQuery}</div>}
            </>
          ) : (
            <div>
              <label className="field-label">Search Queries (One Per Line)</label>
              <textarea value={queries} onChange={(event) => setQueries(event.target.value)}
                className="field resize-none" rows={5}
                placeholder={'"India" AND ("elections" OR "Modi")\n"New Delhi" AND "trade"'} required />
            </div>
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
              <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} className="field">
                {['Mainstream media only', 'All sources', 'Custom'].map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
          </div>

          {sourceFilter === 'Custom' && (
            <div>
              <label className="field-label">Custom Trusted Domains (One Per Line)</label>
              <textarea value={customSources} onChange={(event) => setCustomSources(event.target.value)} className="field resize-none" rows={4} placeholder={'nytimes.com\npolitico.com\nyourcustomsource.com'} />
            </div>
          )}

          <div>
            <label className="field-label">Filter Since (Optional)</label>
            <input value={sinceDate} onChange={(event) => setSinceDate(event.target.value)} className="field" placeholder="YYYY-MM-DD HH:MM" />
          </div>

          <button type="submit" disabled={clipsJob.loading || !topic.trim() || !(queryMode === 'Simple (keywords)' ? generatedQuery : queries.trim())} className="btn-primary mt-auto">
            {clipsJob.loading ? <><SpinnerGap size={18} className="animate-spin" /> Generating…</> : <>Generate Clips Report <ArrowRight size={18} /></>}
          </button>
        </div>
      </form>

      {(clipsJob.job || cleanerJob.job) && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {clipsJob.job && (
            <div className="glass-card p-6">
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

      <section className="glass-card p-8 space-y-5 mt-8">
        <h2 className="text-white text-xl font-semibold">Clip Cleaner</h2>
        <p className="text-slate-400 text-sm">
          Paste raw article text to strip ads, navigation, and boilerplate. Use standalone or as part of the clips workflow below.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="field-label">Cleaning Mode</label>
            <div className="flex gap-4 pt-3">
              {[['llm', 'LLM (recommended)'], ['local', 'Local (rule-based)']].map(([value, label]) => (
                <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                  <input type="radio" checked={standaloneMode === value} onChange={() => setStandaloneMode(value)} className="accent-violet-500" />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <div>
          <label className="field-label">Paste Raw Article Text</label>
          <textarea value={standaloneRawPaste} onChange={e => setStandaloneRawPaste(e.target.value)}
            className="field resize-none" rows={10}
            placeholder="Copy the full article text from the webpage and paste it here..." />
        </div>
        <button onClick={runStandaloneCleaner} disabled={standaloneCleanerJob.loading || !standaloneRawPaste.trim()}
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

      {clipsData.length > 0 && (
        <div className="mt-10 space-y-8">
          <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100 text-sm">
            Found {clipsData.length} articles. {missingCount} article(s) still need full text review.
          </div>

          <section className="glass-card p-8 space-y-4">
            <h2 className="text-white text-xl font-semibold">Review Articles</h2>
            <p className="text-slate-400 text-sm">
              Articles marked as missing full text are the ones that need a raw pasted article and cleaner pass.
            </p>
            <div className="space-y-3">
              {clipsData.map((clip, index) => (
                <details key={`${clip.title}-${index}`} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                  <summary className="cursor-pointer text-slate-200">
                    {clip.has_full_text ? '✅' : '❌'} {index + 1}. {clip.source}: {clip.title}
                  </summary>
                  <div className="mt-4 space-y-3">
                    {clip.url && <a href={clip.url} target="_blank" rel="noreferrer" className="text-violet-300 underline">Open article</a>}
                    <p className="text-slate-400 text-sm">{clip.author || 'Staff'} · {clip.date}</p>
                    <textarea
                      value={clip.extracted_text || ''}
                      onChange={(event) => setClipsData((prev) => prev.map((item, clipIndex) => clipIndex === index ? { ...item, extracted_text: event.target.value } : item))}
                      className="field resize-none"
                      rows={8}
                      placeholder="[PASTE FULL TEXT HERE]"
                    />
                  </div>
                </details>
              ))}
            </div>
          </section>

          <section className="glass-card p-8 space-y-5">
            <h2 className="text-white text-xl font-semibold">Clip Cleaner</h2>
            <p className="text-slate-400 text-sm">
              Paste the raw article text for a paywalled or missing article, choose the target article, then clean and update it.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="field-label">Update Which Article?</label>
                <select value={String(selectedClipIndex)} onChange={(event) => setSelectedClipIndex(Number(event.target.value))} className="field">
                  {clipsData.map((clip, index) => (
                    <option key={`${clip.title}-${index}`} value={index}>
                      {index + 1}. {clip.source}: {clip.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="field-label">Cleaning Mode</label>
                <div className="flex gap-4 pt-3">
                  {[['llm', 'LLM (recommended)'], ['local', 'Local (rule-based)']].map(([value, label]) => (
                    <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                      <input type="radio" checked={cleanerMode === value} onChange={() => setCleanerMode(value)} className="accent-violet-500" />
                      <span>{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="field-label">Paste Raw Article Text</label>
              <textarea value={rawPaste} onChange={(event) => setRawPaste(event.target.value)}
                className="field resize-none" rows={12}
                placeholder="Copy the full article text from the webpage and paste it here..." />
            </div>

            <button onClick={runCleaner} disabled={cleanerJob.loading || !rawPaste.trim()}
              className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm">
              {cleanerJob.loading ? <><SpinnerGap size={16} className="inline mr-2 animate-spin" />Cleaning…</> : 'Clean & Update Article'}
            </button>

            {cleanerJob.job?.status === 'completed' && (
              <textarea
                value={cleanerJob.job.result_data?.cleaned_text || ''}
                readOnly
                className="field resize-none"
                rows={10}
              />
            )}
          </section>

          <section className="glass-card p-8 space-y-5">
            <h2 className="text-white text-xl font-semibold">Build Final Report</h2>
            {missingCount > 0 && (
              <p className="text-slate-400 text-sm">{missingCount} article(s) are still missing full text. You can still build the report.</p>
            )}

            <button onClick={buildFinalReport}
              className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm">
              Build & Download Report
            </button>

            {Object.keys(artifactMap).length > 0 && (
              <div className="space-y-4">
                {/* Report downloads */}
                {['media_clips.docx', 'clips_data.json'].filter(n => artifactMap[n]).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-slate-500 text-xs uppercase tracking-wider">Report Files</p>
                    <div className="flex flex-wrap gap-2">
                      {['media_clips.docx', 'clips_data.json'].filter(n => artifactMap[n]).map(n => (
                        <button key={n} onClick={() => clipsJob.downloadArtifact(artifactMap[n])}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm">
                          <DownloadSimple size={15} /> {n}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {/* Email draft */}
                {['media_clips_email.txt', 'media_clips_email.html'].filter(n => artifactMap[n]).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-slate-500 text-xs uppercase tracking-wider">Email Draft</p>
                    <div className="flex flex-wrap gap-2">
                      {['media_clips_email.txt', 'media_clips_email.html'].filter(n => artifactMap[n]).map(n => (
                        <button key={n} onClick={() => clipsJob.downloadArtifact(artifactMap[n])}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-500/10 border border-violet-400/20 text-violet-200 text-sm">
                          <DownloadSimple size={15} /> {n === 'media_clips_email.txt' ? 'Plain Text (.txt)' : 'HTML (.html)'}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </motion.div>
  );
}
