import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DownloadSimpleIcon as DownloadSimple, ArrowRightIcon as ArrowRight, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { API } from '../../hooks/useFastApiJob';

export default function ToolPage({ title, description, toolId, inputs = [] }) {
  const [formData, setFormData] = useState(() => {
    const defaults = {};
    inputs.forEach(inp => {
      if (inp.type === 'select' && inp.options?.length > 0) defaults[inp.name] = inp.options[0].value;
      else if (inp.defaultValue !== undefined) defaults[inp.name] = inp.defaultValue;
    });
    return defaults;
  });
  const [file, setFile]         = useState(null);
  const [job, setJob]           = useState(null);
  const [loading, setLoading]   = useState(false);

  const handleChange = (e) => setFormData(p => ({ ...p, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const payload = new FormData();
    Object.entries(formData).forEach(([k, v]) => payload.append(k, v));
    if (file) payload.append('file', file);
    try {
      const res  = await fetch(`${API}/api/tools/execute/${toolId}`, { method: 'POST', body: payload });
      const data = await res.json();
      if (data.job_id) setJob({ id: data.job_id, status: 'pending', progress: 0, message: 'Queued' });
    } catch {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!job || !['pending','processing'].includes(job.status)) return;
    const iv = setInterval(async () => {
      try {
        const res  = await fetch(`${API}/api/jobs/${job.id}/status`);
        const data = await res.json();
        setJob(data);
        if (['completed','failed'].includes(data.status)) { setLoading(false); clearInterval(iv); }
      } catch { /* retry */ }
    }, 2000);
    return () => clearInterval(iv);
  }, [job]);

  const download = async () => {
    if (!job?.download_url) return;
    const res  = await fetch(`${API}${job.download_url}`);
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: `strategitect_${toolId}_${job.id.slice(0,6)}.docx` });
    document.body.appendChild(a); a.click(); a.remove();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="p-10 max-w-5xl mx-auto relative z-10"
    >
      {/* Header */}
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
             style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)', marginBottom: 10 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect &nbsp;·&nbsp; TOOL
        </div>
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>{title}</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '60ch', fontWeight: 300 }}>{description}</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">

        {/* Form */}
        <div className="glass-card lg:col-span-3 p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 rounded-full pointer-events-none"
               style={{ background: 'rgba(109,40,217,0.06)', filter: 'blur(60px)' }} />
          <form onSubmit={handleSubmit} className="flex flex-col gap-5 relative z-10">
            {inputs.map((inp) => (
              <div key={inp.name}>
                <label className="field-label">{inp.label}</label>
                {inp.type === 'file' ? (
                  <input type="file" onChange={e => setFile(e.target.files[0])}
                    className="field file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-violet-500/20 file:text-violet-300 hover:file:bg-violet-500/30" />
                ) : inp.type === 'textarea' ? (
                  <textarea name={inp.name} placeholder={inp.placeholder}
                    required={inp.required} onChange={handleChange}
                    rows={inp.rows || 4}
                    className="field resize-none"
                    style={{ fontFamily: 'Inter', fontSize: 14 }} />
                ) : inp.type === 'select' ? (
                  <select name={inp.name} onChange={handleChange}
                    defaultValue={inp.options?.[0]?.value}
                    className="field" style={{ fontFamily: 'Inter', fontSize: 14 }}>
                    {(inp.options || []).map(opt => (
                      <option key={opt.value} value={opt.value}
                        style={{ background: '#18181B', color: '#fff' }}>{opt.label}</option>
                    ))}
                  </select>
                ) : inp.type === 'radio' ? (
                  <div className="flex flex-wrap gap-4 pt-1">
                    {(inp.options || []).map((opt, i) => (
                      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name={inp.name} value={opt.value}
                          defaultChecked={i === 0} onChange={handleChange}
                          className="accent-violet-500" />
                        <span style={{ fontFamily: 'Inter', fontSize: 13, color: '#D4D4D8' }}>{opt.label}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <input type={inp.type || 'text'} name={inp.name} placeholder={inp.placeholder}
                    required={inp.required} onChange={handleChange} className="field" />
                )}
              </div>
            ))}
            <button type="submit" disabled={loading} className="btn-primary mt-3">
              {loading
                ? <><SpinnerGap size={18} className="animate-spin" /> Processing…</>
                : <>Run tool <ArrowRight size={18} /></>}
            </button>
          </form>
        </div>

        {/* Output panel */}
        <div className="glass-card lg:col-span-2 flex flex-col gap-5 p-7 relative overflow-hidden">
          <h2 className="display" style={{ fontSize: 20, color: '#fff' }}>Output</h2>

          {!job ? (
            <div className="flex-1 flex items-center justify-center rounded-xl border border-dashed border-white/8 p-8 bg-black/20">
              <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#52525B', textAlign: 'center', lineHeight: 1.6 }}>
                Submit parameters to start the pipeline.
              </p>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              <motion.div key={job.status} initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col gap-4 p-5 rounded-xl border border-white/8 bg-black/30">

                <div className="flex items-center justify-between">
                  <span style={{ fontFamily: 'monospace', fontSize: 10, color: '#A78BFA', background: 'rgba(109,40,217,0.15)', padding: '3px 8px', borderRadius: 6 }}>
                    {job.id.slice(0, 8).toUpperCase()}
                  </span>
                  <span className={job.status === 'completed' ? 'badge-complete' : job.status === 'failed' ? 'badge-failed' : 'badge-processing'}>
                    {job.status}
                  </span>
                </div>

                <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#D4D4D8', fontWeight: 400 }}>{job.message}</p>

                <div className="progress-track">
                  <motion.div className="progress-fill" initial={{ width: 0 }}
                    animate={{ width: `${job.progress}%` }} transition={{ ease: 'circOut', duration: 0.4 }} />
                </div>

                {job.download_url && (
                  <motion.button initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    onClick={download}
                    className="flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm mt-2 transition-all"
                    style={{ background: '#6D28D9', color: '#fff', boxShadow: '0 0 24px rgba(109,40,217,0.35)' }}>
                    <DownloadSimple size={18} /> Download output
                  </motion.button>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </motion.div>
  );
}
