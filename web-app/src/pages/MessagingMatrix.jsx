/* eslint-disable no-unused-vars */
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import StyledMarkdown from '../components/StyledMarkdown';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';

const VARIANT_LABELS = {
  talking_points: 'Hill Talking Points',
  media_talking_points: 'Media Talking Points',
  news_release: 'News Release',
  social_media: 'Social Media',
  grassroots_email: 'Grassroots Email',
  op_ed: 'Op-Ed Draft',
  speech_draft: 'Speech Draft',
};

const DELIVERABLES = Object.entries(VARIANT_LABELS);
const DEFAULT_VARIANTS = DELIVERABLES.map(([value]) => value);

function cleanVariant(text) {
  if (!text) return '';
  return text
    // Known document-type header lines → H2 (purple, separated from metadata below)
    .replace(/^((?:TALKING POINTS|FOR IMMEDIATE RELEASE|OP-ED|MEDIA TALKING POINTS|GRASSROOTS EMAIL|SOCIAL MEDIA POSTS?)[^\n]*)/gm, '\n## $1\n')
    // "**Long bold title.** Body text starts with capital" → H3 + paragraph
    .replace(/^\*\*([^*]{15,})\*\*\s+([A-Z])/gm, '### $1\n\n$2')
    // Trailing-space soft-breaks after bold lines → proper paragraph break
    .replace(/\*\*\s{2,}\n/g, '**\n\n');
}

export default function MessagingMatrix() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('messaging_matrix');

  const [position, setPosition] = useState('');
  const [coreMessages, setCoreMessages] = useState('');
  const [facts, setFacts] = useState('');
  const [contextPaste, setContextPaste] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [organization, setOrganization] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [selectedVariants, setSelectedVariants] = useState(DEFAULT_VARIANTS);
  const [activeTab, setActiveTab] = useState('Message Map');
  const [llmModel, setLlmModel] = useState('ChangeAgent');

  const rd = job?.result_data;
  const house = rd?.message_house || {};
  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  const toggleVariant = (variant) => {
    setSelectedVariants((prev) => (
      prev.includes(variant) ? prev.filter((item) => item !== variant) : [...prev, variant]
    ));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = new FormData();
    payload.append('position', position);
    payload.append('core_messages', coreMessages);
    payload.append('facts', facts);
    payload.append('context_paste', contextPaste);
    payload.append('organization', organization);
    payload.append('target_audience', targetAudience);
    payload.append('variants', selectedVariants.join(','));
    payload.append('llm_model', llmModel);
    uploadedFiles.forEach((file) => payload.append('file', file));
    submitJob(payload);
  };

  const tabs = ['Message Map', ...Object.keys(rd?.variants || {}).map((variant) => VARIANT_LABELS[variant] || variant)];
  const activeVariantKey = Object.keys(rd?.variants || {}).find((key) => (VARIANT_LABELS[key] || key) === activeTab);

  return (
    <motion.div data-testid="tool-page-messaging-matrix" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-10 max-w-6xl mx-auto relative z-10">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div className="app-kicker">
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect · TOOL
        </div>
        <h1 data-testid="page-title-messaging-matrix" className="app-page-title">Messaging Deliverables</h1>
        <p className="app-page-intro">
          Builds reusable advocacy message outputs and platform-specific deliverables from a core policy position, optional proof points, supporting documents, and audience guidance.
        </p>
        <div className="mt-3"><ModelSelector value={llmModel} onChange={setLlmModel} /></div>
      </header>

      <ResearchPrototypeNote
        category="Content Generation & Drafting Support"
        message="This module translates policy positioning into bounded drafting outputs. It is informed by the project’s house style and reference materials, but its deliverables remain drafts that support message development rather than substitute for final strategic judgment."
      />

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8 flex flex-col gap-5">
          <div>
            <label className="field-label">Core Policy Position</label>
            <textarea data-testid="input-messaging-position" value={position} onChange={(event) => setPosition(event.target.value)}
              className="field resize-none" rows={4}
              placeholder="e.g. Support the AI Safety Act — mandatory pre-deployment testing protects consumers without stifling innovation." required />
          </div>

          <details className="rounded-xl border border-white/10 bg-black/20 p-5">
            <summary className="cursor-pointer text-white font-semibold">Optional: Core Messages & Supporting Facts</summary>
            <div className="mt-5 flex flex-col gap-5">
              <div>
                <label className="field-label">Core Messages</label>
                <textarea data-testid="input-messaging-core-messages" value={coreMessages} onChange={(event) => setCoreMessages(event.target.value)}
                  className="field resize-none" rows={4}
                  placeholder="If you already have core messages, enter them here. Otherwise the tool will generate them." />
              </div>
              <div>
                <label className="field-label">Supporting Facts / Proof Points</label>
                <textarea data-testid="input-messaging-facts" value={facts} onChange={(event) => setFacts(event.target.value)}
                  className="field resize-none" rows={4}
                  placeholder="Key statistics, evidence, or specific claims to anchor the message house." />
              </div>
            </div>
          </details>

          <div>
            <label className="field-label">Supporting Context</label>
            <input data-testid="input-messaging-files" type="file" accept=".pdf,.docx,.txt" multiple
              onChange={(event) => setUploadedFiles(Array.from(event.target.files || []))}
              className="field mb-3 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-violet-500/20 file:text-violet-300" />
            <textarea data-testid="input-messaging-context" value={contextPaste} onChange={(event) => setContextPaste(event.target.value)}
              className="field resize-none" rows={5} placeholder="Paste bill summaries, hearing memo excerpts, or any other grounding text..." />
          </div>
        </div>

        <div className="glass-card p-8 flex flex-col gap-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="field-label">Organization Name</label>
              <input data-testid="input-messaging-organization" value={organization} onChange={(event) => setOrganization(event.target.value)}
                className="field" placeholder="e.g. TechForward Alliance" />
            </div>
            <div>
              <label className="field-label">Primary Target Audience</label>
              <input data-testid="input-messaging-target-audience" value={targetAudience} onChange={(event) => setTargetAudience(event.target.value)}
                className="field" placeholder="e.g. Senate Commerce Committee members" />
            </div>
          </div>

          <div>
            <label className="field-label">Select Deliverables To Generate</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {DELIVERABLES.map(([value, label]) => (
                <label key={value} className="flex items-center gap-2 text-sm text-slate-300">
                  <input data-testid={`toggle-messaging-variant-${value}`} type="checkbox" checked={selectedVariants.includes(value)} onChange={() => toggleVariant(value)} className="accent-violet-500" />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>

          {job ? (
            <div data-testid="status-messaging-matrix" className="rounded-xl border border-white/10 bg-black/20 p-5">
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
              Run the tool to generate the message map and selected deliverables.
            </div>
          )}

          <button data-testid="submit-messaging-matrix" type="submit" disabled={loading || !position.trim() || selectedVariants.length === 0} className="btn-primary mt-auto">
            {loading ? <><SpinnerGap size={18} className="animate-spin" /> Generating…</> : <>Generate Deliverables <ArrowRight size={18} /></>}
          </button>
        </div>
      </form>

      {job?.status === 'completed' && rd && (
        <div className="mt-10 space-y-6">
          <div className="flex flex-wrap gap-3">
            {tabs.map((tab) => (
              <button data-testid={`tab-messaging-${tab.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`} key={tab} onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg border text-sm ${activeTab === tab ? 'bg-violet-500/20 border-violet-400/40 text-violet-200' : 'bg-white/5 border-white/10 text-slate-300'}`}>
                {tab}
              </button>
            ))}
          </div>

          <div className="glass-card p-8">
            <div className="flex items-center gap-3 mb-6">
              <div style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)' }}>
                Str<span style={{ color: '#A78BFA' }}>α</span>tegitect
              </div>
              <span style={{ color: 'rgba(255,255,255,0.15)' }}>·</span>
              <span className="font-serif text-lg text-slate-200">Messaging Deliverables</span>
            </div>
            {activeTab === 'Message Map' && (
              <div className="space-y-6">
                {house.target_audiences?.length > 0 && <p className="text-slate-300"><strong className="text-white">Target Audiences:</strong> {house.target_audiences.join(', ')}</p>}
                <div>
                  <h2 className="app-section-title">Overarching Message</h2>
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100">
                    {house.overarching_message || house.core_message}
                  </div>
                </div>

                {(house.key_messages || house.pillars || []).length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {(house.key_messages || house.pillars || []).map((item, index) => (
                      <div key={index} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
                        <h3 className="text-white font-semibold mb-3">{item.title || item.name || `Key Message ${index + 1}`}</h3>
                        <ul className="space-y-2 text-sm text-slate-300">
                          {(item.supporting_facts || item.proof_points || []).map((fact, factIndex) => (
                            <li key={factIndex}>• {fact}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {house.key_terms?.length > 0 && <p className="text-slate-300"><strong className="text-white">Key Terms:</strong> {house.key_terms.join(', ')}</p>}
              </div>
            )}

            {activeTab !== 'Message Map' && (
              <div className="text-sm leading-7">
                <StyledMarkdown>{cleanVariant(activeVariantKey ? rd.variants?.[activeVariantKey] : '')}</StyledMarkdown>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button data-testid="download-messaging-markdown" onClick={() => downloadText(job?.result_data?.markdown || '', 'messaging_deliverables.md')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download Markdown
            </button>
            <button data-testid="download-messaging-docx" onClick={() => downloadArtifact(artifactMap['messaging_matrix.docx'])}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
              <DownloadSimple size={18} /> Download DOCX
            </button>
            <button data-testid="download-messaging-json" onClick={() => downloadJson(rd || {}, 'messaging_deliverables.json')}
              className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
              <DownloadSimple size={18} /> Download JSON
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
