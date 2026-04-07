/* eslint-disable no-unused-vars */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DownloadSimpleIcon as DownloadSimple, ArrowRightIcon as ArrowRight, SpinnerGapIcon as SpinnerGap, CaretDownIcon as CaretDown, WarningIcon as Warning, CheckCircleIcon as CheckCircle, UploadSimpleIcon as UploadSimple, LinkIcon } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';

export default function HearingMemo() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob("hearing_memo_generator");
  
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

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleExecute = (e) => {
    e.preventDefault();
    submitJob(formData, file);
  }

  // Derived parsed outputs
  const verdict = job?.result_data?.verdict;
  const flags = job?.result_data?.flags || [];
  const checks = job?.result_data?.human_checks || [];
  const memoText = job?.result_data?.memo_text || "";
  const artifactMap = (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {});
  const downloadNamedArtifact = (name, fallbackAction) => {
    if (artifactMap[name]) {
      downloadArtifact(artifactMap[name]);
      return;
    }
    fallbackAction?.();
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-12 max-w-6xl mx-auto relative z-10"
    >
      <header className="mb-12 border-b border-white/10 pb-8 relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/10 blur-[100px] pointer-events-none rounded-full" />
        <h1 className="display-hero text-5xl mb-4 text-white">Congressional Hearing Memo Generator <span className="text-3xl">📝</span></h1>
        <p className="text-slate-400 text-lg font-light leading-relaxed max-w-[80ch]">
          Converts congressional hearing transcripts into professional hearing memos with structured extraction, house-style composition, and automated verification.
        </p>
      </header>

      <form onSubmit={handleExecute} className="space-y-8 relative z-20">
        
        {/* Main Columns mimicking st.columns([2, 1]) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column (2x width) */}
          <div className="lg:col-span-2 glass-card p-8 flex flex-col gap-6">
            <h3 className="text-xl font-serif mb-2">Source Input</h3>
            
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium tracking-wide text-slate-300">Upload hearing transcript (PDF or TXT)</label>
              <div className="relative border border-dashed border-white/20 rounded-xl p-4 hover:border-purple-500/50 transition-colors bg-black/20 focus-within:ring-1 focus-within:ring-purple-400">
                <input 
                  type="file" 
                  accept=".pdf,.txt"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={(e) => setFile(e.target.files[0])}
                />
                <div className="flex items-center gap-3 text-slate-400 pointer-events-none">
                  <UploadSimple size={24} />
                  <span>{file ? file.name : "Drag and drop or click to upload"}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 hidden">
                <hr className="flex-1 border-white/10" />
                <span className="text-slate-500 text-sm">OR</span>
                <hr className="flex-1 border-white/10" />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium tracking-wide text-slate-300">Or paste a YouTube URL</label>
              <div className="relative">
                <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input 
                  type="text" 
                  name="youtube_url"
                  placeholder="e.g., https://www.youtube.com/watch?v=..."
                  onChange={handleInputChange}
                  className="w-full bg-white/5 border border-white/10 pl-11 pr-4 py-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 transition-all font-light placeholder:text-slate-600"
                />
              </div>
              <span className="text-xs text-slate-500">The tool will auto-fetch the transcript from YouTube.</span>
            </div>
          </div>

          {/* Right Column (1x width) */}
          <div className="lg:col-span-1 glass-card p-8 flex flex-col gap-6">
             <h3 className="text-xl font-serif mb-2">Letterhead</h3>
             
             <div className="flex flex-col gap-2">
               <label className="text-sm font-medium tracking-wide text-slate-300">FROM Field</label>
               <input type="text" name="memo_from" placeholder="e.g., Your Organization" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
             </div>

             <div className="flex flex-col gap-2">
               <label className="text-sm font-medium tracking-wide text-slate-300">Memo Date</label>
               <input type="text" name="memo_date" placeholder="e.g., Thursday, March 13, 2026" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
             </div>

             <div className="flex flex-col gap-2">
               <label className="text-sm font-medium tracking-wide text-slate-300">Subject Override</label>
               <input type="text" name="subject_override" placeholder="Auto-detected if blank" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
             </div>
          </div>
        </div>

        {/* Advanced Options Expander */}
        <div className="glass-card rounded-2xl overflow-hidden border border-white/10">
          <button 
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)} 
            className="w-full flex items-center justify-between p-6 bg-white/5 hover:bg-white/10 transition-colors"
          >
            <span className="font-serif text-lg text-white">Advanced Options</span>
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
                  <input type="text" name="hearing_title" placeholder="Override hearing title" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
                  <input type="text" name="committee" placeholder="Override committee name" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
                  <input type="text" name="hearing_date" placeholder="Override hearing date" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
                  <input type="text" name="hearing_time" placeholder="Override hearing time" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
                </div>
                <input type="text" name="confidentiality" placeholder="Footer Default: Confidential - Not for Public Consumption" onChange={handleInputChange} className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-1 focus:ring-purple-400 font-light placeholder:text-slate-600" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <button 
           type="submit" 
           disabled={loading || (!file && !formData.youtube_url)}
           className="w-full py-5 rounded-2xl bg-white text-black font-semibold text-lg tracking-wide flex items-center justify-center gap-3 hover:bg-slate-200 transition-colors disabled:opacity-50 interactive-button"
        >
          {loading ? (
            <><SpinnerGap size={24} className="animate-spin" /> Running 4-stage pipeline...</>
          ) : (
            <>Generate Memo <ArrowRight size={24} /></>
          )}
        </button>
      </form>

      {/* output block */}
      {job && (
        <AnimatePresence>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-16 pt-12 border-t border-white/10"
          >
            <h2 className="display-hero text-4xl mb-8">Generated Memo</h2>
            
            {/* Status Panel */}
            <div className="glass-card p-6 mb-8 relative overflow-hidden">
               {job.status !== "completed" ? (
                 <div className="flex flex-col gap-4">
                   <div className="flex justify-between items-center mb-2">
                      <span className="font-mono text-xs text-purple-300">Phase: {job.progress}%</span>
                      <span className="font-mono text-xs text-yellow-500 animate-pulse">{job.status.toUpperCase()}</span>
                   </div>
                   <p className="text-white text-lg font-light">{job.message}</p>
                   <div className="h-1 w-full bg-white/10 mt-2">
                     <motion.div className="h-full bg-purple-500" initial={{ width: 0 }} animate={{ width: `${job.progress}%` }} />
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
                    <span className="font-serif text-lg text-slate-200">Memo Preview (Markdown)</span>
                  </div>
                  <div className="p-8 prose prose-invert prose-purple max-w-none">
                    <pre className="text-slate-300 bg-transparent whitespace-pre-wrap font-sans text-base leading-relaxed">{memoText}</pre>
                  </div>
               </div>
            )}

            {/* Downloads */}
            {job.status === "completed" && (
              <div>
                <h3 className="font-serif text-2xl mb-4">Downloads</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button onClick={() => downloadNamedArtifact("hearing_memo.docx")} className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/30 text-purple-200 transition-colors">
                    <DownloadSimple size={20} /> Download .docx
                  </button>
                  <button onClick={() => downloadNamedArtifact("hearing_memo.txt", () => downloadText(memoText, "hearing_memo.txt"))} className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                    <DownloadSimple size={20} /> Download .txt
                  </button>
                  <button onClick={() => downloadNamedArtifact("hearing_memo_verification.json", () => downloadJson(job.result_data?.verification || {}, "hearing_memo_verification.json"))} className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                    <DownloadSimple size={20} /> Download verification.json
                  </button>
                </div>
              </div>
            )}

          </motion.div>
        </AnimatePresence>
      )}
    </motion.div>
  );
}
