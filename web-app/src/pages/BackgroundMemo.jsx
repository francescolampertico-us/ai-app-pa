/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';

const DISCLOSURE_SOURCES = ['lda', 'fara', 'irs990'];

function DownloadRow({ job, onDownloadArtifact, onDownloadJson, onDownloadText }) {
  if (job?.status !== 'completed') return null;
  const artifactByName = (job.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {});

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <button onClick={() => onDownloadArtifact(artifactByName['background_memo.docx'])}
        className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
        <DownloadSimple size={18} /> Download DOCX
      </button>
      <button onClick={() => onDownloadText(job?.result_data?.markdown || '', 'background_memo.md')}
        className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
        <DownloadSimple size={18} /> Download Markdown
      </button>
      <button onClick={() => onDownloadJson(job?.result_data?.result || {}, 'background_memo.json')}
        className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
        <DownloadSimple size={18} /> Download JSON
      </button>
    </div>
  );
}

export default function BackgroundMemo() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('background_memo_generator');

  const [subject, setSubject] = useState('');
  const [memoDate, setMemoDate] = useState(new Date().toLocaleDateString('en-US', { month: 'long', day: '2-digit', year: 'numeric' }));
  const [sectionsText, setSectionsText] = useState('Corporate Overview\nKey Leadership\nU.S. Presence\nPolicy Positions');
  const [context, setContext] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [disclosureEntity, setDisclosureEntity] = useState('');
  const [disclosureSources, setDisclosureSources] = useState(['lda', 'fara']);

  const result = job?.result_data?.result;
  const researchMd = job?.result_data?.research_md || '';
  const disclosureMd = job?.result_data?.disclosure_md || '';

  const disclosureArtifacts = useMemo(
    () => (job?.artifacts || []).filter(artifact => /report\.md$|\.csv$/i.test(artifact.name)),
    [job?.artifacts],
  );

  const toggleDisclosureSource = (source) => {
    setDisclosureSources((prev) => (
      prev.includes(source) ? prev.filter((item) => item !== source) : [...prev, source]
    ));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('subject', subject);
    payload.append('memo_date', memoDate);
    payload.append('sections_text', sectionsText);
    payload.append('context', context);
    payload.append('disclosure_entity_override', disclosureEntity);
    payload.append('disclosure_sources', disclosureSources.join(','));
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
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Background Memo Generator</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '70ch', fontWeight: 300 }}>
          Generates a structured background memo on a client, organization, policy issue, or individual, with optional file grounding and automatic disclosure research.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="glass-card p-8 flex flex-col gap-5">
            <div>
              <label className="field-label">Subject</label>
              <input value={subject} onChange={(event) => setSubject(event.target.value)}
                className="field" placeholder="e.g. Jagello 2000, Giordano Riello Group, AI Safety Act" required />
            </div>
            <div>
              <label className="field-label">Memo Date</label>
              <input value={memoDate} onChange={(event) => setMemoDate(event.target.value)} className="field" />
            </div>
            <div>
              <label className="field-label">Sections</label>
              <textarea value={sectionsText} onChange={(event) => setSectionsText(event.target.value)}
                className="field resize-none" rows={8} placeholder={'Corporate Overview\nKey Leadership\nU.S. Presence\nPolicy Positions'} required />
            </div>
            <div>
              <label className="field-label">Additional Context</label>
              <textarea value={context} onChange={(event) => setContext(event.target.value)}
                className="field resize-none" rows={4} placeholder="Key angles, background notes, or facts to anchor the memo..." />
            </div>
          </div>

          <div className="glass-card p-8 flex flex-col gap-5">
            <div>
              <label className="field-label">Source Files</label>
              <input type="file" multiple accept=".pdf,.docx,.txt,.md"
                onChange={(event) => setUploadedFiles(Array.from(event.target.files || []))}
                className="field file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-violet-500/20 file:text-violet-300" />
              {uploadedFiles.length > 0 && (
                <div className="mt-3 text-sm text-slate-400 flex flex-col gap-1">
                  {uploadedFiles.map((file) => <span key={file.name}>{file.name}</span>)}
                </div>
              )}
            </div>

            <div className="rounded-xl border border-white/10 bg-black/20 p-5 flex flex-col gap-4">
              <div>
                <div className="field-label">Disclosure Search Options</div>
                <p className="text-sm text-slate-500">The backend searches disclosures across all available years and adds the results into the memo context.</p>
              </div>
              <div>
                <label className="field-label">Entity Name In Filings</label>
                <input value={disclosureEntity} onChange={(event) => setDisclosureEntity(event.target.value)}
                  className="field" placeholder="Leave blank to use the subject name" />
              </div>
              <div>
                <label className="field-label">Sources</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                  {DISCLOSURE_SOURCES.map((source) => (
                    <label key={source} className="flex items-center gap-2 text-sm text-slate-300">
                      <input type="checkbox" checked={disclosureSources.includes(source)} onChange={() => toggleDisclosureSource(source)} className="accent-violet-500" />
                      <span>{source}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <button type="submit" disabled={loading || !subject.trim() || !sectionsText.trim()}
              className="btn-primary mt-auto">
              {loading ? <><SpinnerGap size={18} className="animate-spin" /> Generating…</> : <>Generate Memo <ArrowRight size={18} /></>}
            </button>
          </div>
        </div>
      </form>

      {job && (
        <div className="mt-12 space-y-8">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-3">
              <span className="font-mono text-xs text-purple-300">{job.id.slice(0, 8).toUpperCase()}</span>
              <span className={job.status === 'completed' ? 'badge-complete' : job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>{job.status}</span>
            </div>
            <p className="text-slate-300 text-sm mb-4">{job.message}</p>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${job.progress || 0}%` }} />
            </div>
          </div>

          {job.status === 'completed' && result && (
            <>
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
                Review required. All memo text is model-generated and should be checked against primary sources before distribution.
              </div>

              <div className="glass-card p-8 space-y-8">
                <section>
                  <h2 className="display" style={{ fontSize: 26, color: '#fff', marginBottom: 12 }}>Overview</h2>
                  <p className="text-slate-300 leading-7">{result.overview}</p>
                </section>

                <section>
                  <h2 className="display" style={{ fontSize: 26, color: '#fff', marginBottom: 12 }}>Fast Facts</h2>
                  <div className="space-y-3">
                    {(result.fast_facts || []).map((fact) => (
                      <p key={fact} className="text-slate-300 leading-7"><strong className="text-white">• {fact}</strong></p>
                    ))}
                  </div>
                </section>

                {(result.sections || []).map((section) => (
                  <section key={section.heading}>
                    <h2 className="display" style={{ fontSize: 26, color: '#fff', marginBottom: 12 }}>{section.heading}</h2>
                    {(section.subsections || []).map((subsection, index) => (
                      <div key={`${section.heading}-${index}`} className="space-y-4 mb-5">
                        {subsection.heading && <h3 className="text-lg text-slate-200 font-semibold">{subsection.heading}</h3>}
                        {(subsection.paragraphs || []).map((paragraph, paragraphIndex) => (
                          <p key={paragraphIndex} className="text-slate-300 leading-7">{paragraph}</p>
                        ))}
                      </div>
                    ))}
                  </section>
                ))}

                <section>
                  <h2 className="display" style={{ fontSize: 26, color: '#fff', marginBottom: 12 }}>Links</h2>
                  <div className="space-y-2">
                    {(result.links || []).map((link) => (
                      <a key={`${link.label}-${link.url}`} href={link.url} target="_blank" rel="noreferrer"
                        className="block text-violet-300 hover:text-violet-200 underline underline-offset-4">
                        {link.label || link.url}
                      </a>
                    ))}
                  </div>
                </section>
              </div>

              <DownloadRow
                job={job}
                onDownloadArtifact={downloadArtifact}
                onDownloadJson={downloadJson}
                onDownloadText={downloadText}
              />

              {researchMd && (
                <details className="glass-card p-6">
                  <summary className="cursor-pointer text-white font-semibold">View Articles Used For Research</summary>
                  <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{researchMd}</pre>
                </details>
              )}

              {disclosureMd && (
                <details className="glass-card p-6">
                  <summary className="cursor-pointer text-white font-semibold">View Raw Disclosure Data Used</summary>
                  <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{disclosureMd}</pre>
                </details>
              )}

              {disclosureArtifacts.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-white text-lg font-semibold mb-4">Disclosure Downloads</h3>
                  <div className="flex flex-wrap gap-3">
                    {disclosureArtifacts.map((artifact) => (
                      <button key={artifact.url} onClick={() => downloadArtifact(artifact)}
                        className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm">
                        {artifact.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </motion.div>
  );
}
