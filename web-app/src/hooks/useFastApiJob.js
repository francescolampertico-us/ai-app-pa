import { useState, useEffect, useRef } from 'react';

export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useFastApiJob(toolId) {
  const [job, setJob]         = useState(null);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!job || !['pending', 'processing'].includes(job.status)) return;
    intervalRef.current = setInterval(async () => {
      try {
        const res  = await fetch(`${API}/api/jobs/${job.id}/status`);
        const data = await res.json();
        setJob(data);
        if (['completed', 'failed'].includes(data.status)) {
          setLoading(false);
          clearInterval(intervalRef.current);
        }
      } catch { /* retry on next tick */ }
    }, 2000);
    return () => clearInterval(intervalRef.current);
  }, [job]);

  const submitJob = async (formData, file) => {
    setLoading(true);
    setJob(null);
    const payload = formData instanceof FormData ? formData : new FormData();
    if (!(formData instanceof FormData)) {
      Object.entries(formData).forEach(([k, v]) => {
        if (Array.isArray(v)) {
          v.forEach(item => { if (item !== undefined && item !== null && item !== '') payload.append(k, item); });
        } else if (v !== undefined && v !== null && v !== '') {
          payload.append(k, v);
        }
      });
      if (file) {
        if (Array.isArray(file)) file.forEach(item => payload.append('file', item));
        else payload.append('file', file);
      }
    }
    try {
      const res  = await fetch(`${API}/api/tools/execute/${toolId}`, { method: 'POST', body: payload });
      const data = await res.json();
      if (data.job_id) setJob({ id: data.job_id, status: 'pending', progress: 0, message: 'Queued' });
    } catch {
      setLoading(false);
    }
  };

  const downloadFile = async (ext = 'docx') => {
    if (!job?.download_url) return;
    const res  = await fetch(`${API}${job.download_url}`);
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {
      href: url,
      download: `strategitect_${toolId}_${job.id.slice(0, 6)}.${ext}`,
    });
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadArtifact = async (artifact, fallbackName = 'download.bin') => {
    if (!artifact?.url) return;
    const res  = await fetch(`${API}${artifact.url}`);
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {
      href: url,
      download: artifact.name || fallbackName,
    });
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadJson = (data, filename = 'output.json') => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: filename });
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadText = (text, filename = 'output.txt') => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: filename });
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  return { job, loading, submitJob, downloadFile, downloadArtifact, downloadJson, downloadText };
}
