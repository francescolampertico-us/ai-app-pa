/* eslint-disable no-unused-vars */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DownloadSimpleIcon as DownloadSimple, ArrowRightIcon as ArrowRight, SpinnerGapIcon as SpinnerGap, CaretDownIcon as CaretDown, WarningIcon as Warning, CheckCircleIcon as CheckCircle, UploadSimpleIcon as UploadSimple, LinkIcon } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import StyledMarkdown from '../components/StyledMarkdown';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';
import ToolTourButton from '../components/tour/ToolTourButton';
import { TOOL_TOUR_IDS } from '../components/tour/tourDefinitions';

export default function HearingMemo() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText, downloadFile } = useFastApiJob("hearing_memo_generator");
  
  const [formData, setFormData] = useState({
    youtube_url: '',
    memo_from: '',
    memo_date: '',
    subject_override: '',
    hearing_title: '',
    hearing_date: '',
    committee: '',
    hearing_time: '',
    confidentiality: ''
  });
  const [file, setFile] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [llmModel, setLlmModel] = useState('ChangeAgent');

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleExecute = (e) => {
    e.preventDefault();
    submitJob({ ...formData, llm_model: llmModel }, file);
  }

  // Derived parsed outputs
  const verdict = job?.result_data?.verdict;
  const flags = job?.result_data?.flags || [];
  const checks = job?.result_data?.human_checks || [];
  const memoText = job?.result_data?.memo_text || "";
  const pipelineStdout = job?.result_data?.stdout || "";
  const pipelineStderr = job?.result_data?.stderr || "";
  const artifactMap = (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {});
  const docxArtifact = (job?.artifacts || []).find(a => a.name.endsWith('.docx'));
  const downloadNamedArtifact = (name, fallbackAction) => {
    if (artifactMap[name]) {
      downloadArtifact(artifactMap[name]);
      return;
    }
    fallbackAction?.();
  };

  return (
    <motion.div 
      data-testid="tool-page-hearing-memo"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="app-page-shell app-page-shell-wide"
    >
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <h1 data-testid="page-title-hearing-memo" data-tour="hearing-memo-title-heading" className="app-page-title">Hearing Memo</h1>
        <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <p className="app-page-intro" style={{ maxWidth: '70ch' }}>
            Generates a structured first-draft hearing memo from congressional transcripts with extraction, house-style composition, and automated verification.
          </p>
          <div className="flex flex-wrap items-center gap-3 md:justify-end">
            <ModelSelector value={llmModel} onChange={setLlmModel} />
            <div data-tour="tour-button-hearing-memo"><ToolTourButton tourId={TOOL_TOUR_IDS.hearingMemo} /></div>
          </div>
        </div>
      </header>

      <ResearchPrototypeNote
        category="Policy Monitoring and Legislative Tracking"
        refs={['bitonti2023', 'digiacomo2025']}
        message="This module demonstrates bounded AI use on a structured drafting task. It produces a house-style draft and verification outputs, but the final memo still depends on human review, contextual interpretation, and editorial judgment."
      />

      <form onSubmit={handleExecute} className="space-y-8 relative z-20">
        
        {/* Main Columns mimicking st.columns([2, 1]) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column (2x width) */}
          <div className="lg:col-span-2 glass-card p-8 flex flex-col gap-6">
            <div data-tour="hearing-memo-source" className="flex flex-col gap-2">
              <label className="field-label">Upload hearing transcript (PDF or TXT)</label>
              <div className="relative border border-dashed border-white/20 rounded-xl p-4 hover:border-purple-500/50 transition-colors bg-black/20 focus-within:ring-1 focus-within:ring-purple-400">
                <input 
                  data-testid="input-hearing-file"
                  type="file" 
                  accept=".pdf,.txt"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={(e) => setFile(e.target.files[0])}
                />
                <div className="flex items-center gap-3 text-slate-400 pointer-events-none">
                  <UploadSimple size={24} />
                  <span className="text-[13px]">{file ? file.name : "Drag and drop or click to upload"}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 hidden">
                <hr className="flex-1 border-white/10" />
                <span className="text-slate-500 text-sm">OR</span>
                <hr className="flex-1 border-white/10" />
            </div>

            <div data-tour="hearing-memo-youtube" className="flex flex-col gap-2">
              <label className="field-label">Or paste a YouTube URL</label>
              <div className="relative">
                <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input 
                  data-testid="input-hearing-youtube-url"
                  type="text" 
                  name="youtube_url"
                  placeholder="e.g., https://www.youtube.com/watch?v=..."
                  onChange={handleInputChange}
                  className="field pl-11 pr-4"
                />
              </div>
              <span className="text-xs text-slate-500">The tool will auto-fetch the transcript from YouTube.</span>
            </div>
          </div>

          {/* Right Column (1x width) */}
          <div data-tour="hearing-memo-header" className="lg:col-span-1 glass-card p-8 flex flex-col gap-6">
             <div className="flex flex-col gap-2">
               <label className="field-label">FROM Field</label>
               <input data-testid="input-hearing-memo-from" type="text" name="memo_from" placeholder="e.g., Your Organization" onChange={handleInputChange} className="field" />
             </div>

             <div className="flex flex-col gap-2">
               <label className="field-label">Memo Date</label>
               <input data-testid="input-hearing-memo-date" type="text" name="memo_date" placeholder="e.g., Thursday, March 13, 2026" onChange={handleInputChange} className="field" />
             </div>

             <div className="flex flex-col gap-2">
               <label className="field-label">Subject Override</label>
               <input data-testid="input-hearing-subject-override" type="text" name="subject_override" placeholder="Auto-detected if blank" onChange={handleInputChange} className="field" />
             </div>
          </div>
        </div>

        {/* Advanced Options Expander */}
        <div data-tour="hearing-memo-options" className="glass-card rounded-2xl overflow-hidden border border-white/10">
          <button 
            data-testid="toggle-hearing-advanced"
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)} 
            className="w-full flex items-center justify-between p-6 bg-white/5 hover:bg-white/10 transition-colors"
          >
            <span className="app-surface-title !text-lg !mb-0">Advanced Options</span>
            <CaretDown size={20} className={`text-slate-400 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          </button>
          
          <AnimatePresence>
            {showAdvanced && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6 pt-2"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <input data-testid="input-hearing-title-override" type="text" name="hearing_title" placeholder="Override hearing title" onChange={handleInputChange} className="field" />
                  <input data-testid="input-hearing-committee-override" type="text" name="committee" placeholder="Override committee name" onChange={handleInputChange} className="field" />
                  <input data-testid="input-hearing-date-override" type="text" name="hearing_date" placeholder="Override hearing date" onChange={handleInputChange} className="field" />
                  <input data-testid="input-hearing-time-override" type="text" name="hearing_time" placeholder="Override hearing time" onChange={handleInputChange} className="field" />
                </div>
                <input data-testid="input-hearing-confidentiality" type="text" name="confidentiality" placeholder="Footer Default: Confidential - Not for Public Consumption" onChange={handleInputChange} className="field" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <button 
           data-testid="submit-hearing-memo"
           data-tour="hearing-memo-submit"
           type="submit" 
           disabled={loading || (!file && !formData.youtube_url)}
           className="btn-primary text-base"
        >
          {loading ? (
            <><SpinnerGap size={20} className="animate-spin" /> Running 4-stage pipeline...</>
          ) : (
            <>Generate Memo <ArrowRight size={18} /></>
          )}
        </button>
      </form>

      <section data-tour="hearing-memo-output" className="mt-16">
      {job && (
        <AnimatePresence>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-16 pt-12 border-t border-white/10"
          >
            <h2 className="app-output-header text-[30px] md:text-[34px]">Generated Memo</h2>
            
            {/* Status Panel */}
            <div data-testid="status-hearing-memo" className="glass-card p-6 mb-8 relative overflow-hidden">
               {job.status !== "completed" ? (
                 <div className="flex flex-col gap-4">
                   <div className="flex justify-between items-center mb-2">
                      <span className="font-mono text-xs text-purple-300">Phase: {job.progress}%</span>
                      <span className="badge-processing">{job.status}</span>
                    </div>
                   <p className="text-slate-300 text-sm">{job.message}</p>
                   <div className="progress-track mt-1">
                     <motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${job.progress}%` }} />
                   </div>
                 </div>
               ) : (
                 <div className="flex flex-col gap-4">
                     {verdict === "pass" ? (
                       <div className="flex items-start gap-4 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                          <CheckCircle size={28} className="text-emerald-400 shrink-0" weight="fill" />
                          <div>
                            <h4 className="text-emerald-300 font-medium text-lg">Verification: PASS</h4>
                            <p className="text-emerald-400/80 font-light">No flags or human checks required.</p>
                          </div>
                       </div>
                     ) : (
                       <div className="flex items-start gap-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl">
                          <Warning size={28} className="text-amber-400 shrink-0" weight="fill" />
                          <div className="flex-1">
                            <h4 className="text-amber-300 font-medium text-lg mb-2">Verification: NEEDS REVIEW</h4>
                            {flags.length > 0 && (
                              <div className="mb-3">
                                <span className="text-amber-200/80 font-semibold text-sm uppercase tracking-wider">Flags:</span>
                                <ul className="mt-1 space-y-1">
                                  {flags.map((f, i) => <li key={i} className="text-amber-300/80 text-sm font-light flex gap-2"><span>⚠️</span> {f}</li>)}
                                </ul>
                              </div>
                            )}
                            {checks.length > 0 && (
                              <div>
                                <span className="text-amber-200/80 font-semibold text-sm uppercase tracking-wider">Human checks needed:</span>
                                <ul className="mt-1 space-y-1">
                                  {checks.map((c, i) => <li key={i} className="text-amber-300/80 text-sm font-light flex gap-2"><span>👁️</span> {c}</li>)}
                                </ul>
                              </div>
                            )}
                          </div>
                       </div>
                     )}
                 </div>
               )}
            </div>

            {/* Markdown Preview */}
            {job.status === "completed" && memoText && (
               <div className="glass-card mb-8 rounded-2xl overflow-hidden border border-white/10 bg-black/40">
                  <div className="bg-white/5 border-b border-white/10 p-4">
                    <div className="app-output-header !text-lg !mb-0">Memo Preview</div>
                  </div>
                  <div className="p-8 max-w-none">
                    <StyledMarkdown>{memoText}</StyledMarkdown>
                  </div>
               </div>
            )}

            {/* Downloads */}
            {job.status === "completed" && (
              <div>
                <h3 className="font-serif text-2xl mb-4">Downloads</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button data-testid="download-hearing-docx" onClick={() => docxArtifact ? downloadArtifact(docxArtifact) : downloadFile('docx')} className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
                    <DownloadSimple size={20} /> Download .docx
                  </button>
                  <button data-testid="download-hearing-text" onClick={() => downloadNamedArtifact("hearing_memo.txt", () => downloadText(memoText, "hearing_memo.txt"))} className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                    <DownloadSimple size={20} /> Download .txt
                  </button>
                  <button data-testid="download-hearing-verification-json" onClick={() => downloadNamedArtifact("hearing_memo_verification.json", () => downloadJson(job.result_data?.verification || {}, "hearing_memo_verification.json"))} className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                    <DownloadSimple size={20} /> Download verification.json
                  </button>
                </div>
              </div>
            )}

            {/* Pipeline logs */}
            {pipelineStdout && (
              <details className="glass-card p-5 mt-6">
                <summary className="cursor-pointer text-slate-300 text-sm font-medium">Pipeline Log</summary>
                <pre className="mt-3 whitespace-pre-wrap text-xs text-slate-400 leading-relaxed">{pipelineStdout}</pre>
              </details>
            )}
            {pipelineStderr && (
              <details className="glass-card p-5 mt-4">
                <summary className="cursor-pointer text-amber-300 text-sm font-medium">Errors / Warnings</summary>
                <pre className="mt-3 whitespace-pre-wrap text-xs text-amber-200/70 leading-relaxed">{pipelineStderr}</pre>
              </details>
            )}

          </motion.div>
        </AnimatePresence>
      )}
      </section>
    </motion.div>
  );
}
