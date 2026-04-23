/* eslint-disable no-unused-vars */
import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SpinnerGapIcon as SpinnerGap, ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, CaretDownIcon as CaretDown } from '@phosphor-icons/react';
import ModelSelector from '../components/ModelSelector';
import StyledMarkdown from '../components/StyledMarkdown';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';

import { API } from '../hooks/useFastApiJob';
const CUR_YEAR = new Date().getFullYear();
const ALL_YEARS = Array.from({ length: CUR_YEAR - 1999 }, (_, i) => CUR_YEAR - i);

function csvBlob(rows, headers) {
  const escape = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const lines = [headers.map(escape).join(',')];
  for (const row of rows) lines.push(headers.map(h => escape(row[h] ?? '')).join(','));
  return new Blob([lines.join('\n')], { type: 'text/csv' });
}

function downloadCsv(rows, headers, filename) {
  const url = URL.createObjectURL(csvBlob(rows, headers));
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

function downloadText(text, filename) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

function extractMatchedNames(csvData) {
  const clientCounts = {};
  const registrantCounts = {};

  const incClient = (name) => { if (name) clientCounts[name] = (clientCounts[name] || 0) + 1; };
  const incRegistrant = (name) => { if (name) registrantCounts[name] = (registrantCounts[name] || 0) + 1; };

  (csvData.lda_filings || []).forEach((row) => {
    incRegistrant(row.registrant_name);
    incClient(row.client_name);
  });
  (csvData.lda_issues || []).forEach((row) => {
    incRegistrant(row.registrant);
    incClient(row.client);
  });
  (csvData.lda_lobbyists || []).forEach((row) => {
    incRegistrant(row.registrant);
    incClient(row.client);
  });
  (csvData.fara_foreign_principals || []).forEach((row) => {
    incRegistrant(row.registrant_name);
    incClient(row.foreign_principal_name);
  });
  (csvData.irs990_organizations || []).forEach((row) => {
    incRegistrant(row.organization_name);
  });

  const sortByFreq = (counts) => Object.keys(counts).sort((a, b) => counts[b] - counts[a]);

  return {
    clients: sortByFreq(clientCounts),
    registrants: sortByFreq(registrantCounts),
    clientCounts,
    registrantCounts,
  };
}

function getAssociatedRegistrants(rawCsvData, clientName) {
  if (!clientName) return [];
  const registrants = new Set();
  const add = (name) => { if (name) registrants.add(name); };
  (rawCsvData.lda_filings || []).forEach(r => { if (r.client_name === clientName) add(r.registrant_name); });
  (rawCsvData.lda_issues || []).forEach(r => { if (r.client === clientName) add(r.registrant); });
  (rawCsvData.lda_lobbyists || []).forEach(r => { if (r.client === clientName) add(r.registrant); });
  (rawCsvData.fara_foreign_principals || []).forEach(r => { if (r.foreign_principal_name === clientName) add(r.registrant_name); });
  (rawCsvData.fara_documents || []).forEach(r => { if (r.foreign_principal_name === clientName) add(r.registrant_name); });
  return [...registrants].filter(Boolean);
}

function filterCsvData(csvData, allowedNames) {
  if (!allowedNames.size) return csvData;
  const match = (...values) => values.some((value) => value && allowedNames.has(value));
  return {
    ...csvData,
    lda_filings: (csvData.lda_filings || []).filter((row) => match(row.registrant_name, row.client_name)),
    lda_issues: (csvData.lda_issues || []).filter((row) => match(row.registrant, row.client)),
    lda_lobbyists: (csvData.lda_lobbyists || []).filter((row) => match(row.registrant, row.client)),
    fara_foreign_principals: (csvData.fara_foreign_principals || []).filter((row) => match(row.registrant_name, row.foreign_principal_name)),
    fara_registrants: (csvData.fara_registrants || []).filter((row) => match(row.registrant_name)),
    fara_documents: (csvData.fara_documents || []).filter((row) => match(row.registrant_name, row.foreign_principal_name)),
    irs990_filings: (csvData.irs990_filings || []).filter((row) => match(row.organization_name)),
    irs990_organizations: (csvData.irs990_organizations || []).filter((row) => match(row.organization_name)),
  };
}

function filterReport(reportText, allowedNames) {
  if (!reportText) return reportText;
  if (!allowedNames.size) return '';
  const allowed = new Set(Array.from(allowedNames).map(n => n.toLowerCase()));

  // These sections have no entity-specific ### subsections — always keep them.
  const ALWAYS_INCLUDE = new Set(['executive summary', 'appendix: matching confidence']);

  // Parse into blocks: preamble (level 0), ## sections (level 2), ### subsections (level 3)
  const blocks = [];
  let current = { level: 0, header: null, content: [] };
  for (const line of reportText.split('\n')) {
    if (line.startsWith('## ')) {
      blocks.push(current);
      current = { level: 2, header: line, content: [] };
    } else if (line.startsWith('### ')) {
      blocks.push(current);
      current = { level: 3, header: line, content: [] };
    } else {
      current.content.push(line);
    }
  }
  blocks.push(current);

  const output = [];
  let i = 0;
  while (i < blocks.length) {
    const block = blocks[i];
    if (block.level === 0) {
      output.push(...block.content);
      i++; continue;
    }
    if (block.level === 2) {
      const sectionKey = block.header.slice(3).trim().toLowerCase();
      // Collect all ### children of this ## section
      const children = [];
      i++;
      while (i < blocks.length && blocks[i].level === 3) {
        children.push(blocks[i]);
        i++;
      }
      if (ALWAYS_INCLUDE.has(sectionKey)) {
        // Keep header + all children regardless of filter
        output.push(block.header);
        output.push(...block.content);
        children.forEach(c => { output.push(c.header); output.push(...c.content); });
      } else {
        // Only keep children whose name is in allowedNames
        const kept = children.filter(c => allowed.has(c.header.slice(4).trim().toLowerCase()));
        if (kept.length > 0) {
          output.push(block.header);
          // Omit bare ## content (e.g. "No records matched") — only emit ### children
          kept.forEach(c => { output.push(c.header); output.push(...c.content); });
        }
        // If no kept children, entire ## section is suppressed
      }
      continue;
    }
    i++; // orphan ### — skip
  }

  return output.join('\n');
}

/* ── Year multi-select dropdown ─────────────────────────────────────────── */
function YearDropdown({ selected, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const toggle = y => {
    onChange(selected.includes(y) ? selected.filter(x => x !== y) : [...selected, y]);
  };

  const label = selected.length === 0
    ? 'Select years…'
    : selected.length === 1
      ? selected[0]
      : `${selected.length} years selected`;

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button type="button" onClick={() => setOpen(o => !o)}
        className="field flex items-center justify-between w-full"
        style={{ fontFamily: 'Inter', fontSize: 13, color: selected.length ? '#D4D4D8' : '#52525B', cursor: 'pointer', textAlign: 'left' }}>
        <span>{label}</span>
        <CaretDown size={14} style={{ color: '#71717A', flexShrink: 0, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }} />
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0, zIndex: 50,
          background: '#18181B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
          maxHeight: 220, overflowY: 'auto', padding: '6px 0', boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
        }}>
          {ALL_YEARS.map(y => {
            const ys = String(y);
            const checked = selected.includes(ys);
            return (
              <label key={y} onClick={e => { e.preventDefault(); toggle(ys); }}
                className="flex items-center gap-2.5 px-4 py-1.5 cursor-pointer hover:bg-white/5 transition-colors">
                <input type="checkbox" readOnly checked={checked} className="accent-violet-500 pointer-events-none" />
                <span style={{ fontFamily: 'Inter', fontSize: 13, color: checked ? '#c4b5fd' : '#D4D4D8' }}>{y}</span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Per-column multi-select checkbox dropdown ───────────────────────────── */
function ColumnFilter({ values, selected, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const handler = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);
  const toggle = v => onChange(selected.includes(v) ? selected.filter(x => x !== v) : [...selected, v]);
  const label = selected.length === 0 ? 'All' : `${selected.length} ✓`;
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button type="button" onClick={() => setOpen(o => !o)} style={{
        width: '100%', background: selected.length ? 'rgba(109,40,217,0.2)' : 'rgba(24,24,27,0.9)',
        border: `1px solid ${selected.length ? 'rgba(109,40,217,0.4)' : 'rgba(255,255,255,0.12)'}`,
        borderRadius: 5, padding: '3px 8px', fontFamily: 'Inter', fontSize: 11,
        color: selected.length ? '#c4b5fd' : '#71717A',
        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', minWidth: 60,
      }}>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>
        <span style={{ flexShrink: 0, marginLeft: 4, fontSize: 8 }}>▾</span>
      </button>
      {open && values.length > 0 && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 2px)', left: 0, zIndex: 200,
          background: '#18181B', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8,
          maxHeight: 180, overflowY: 'auto', padding: '4px 0', minWidth: 160,
          boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        }}>
          {values.map(v => {
            const checked = selected.includes(v);
            return (
              <label key={v} onClick={e => { e.preventDefault(); toggle(v); }}
                className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-white/5">
                <input type="checkbox" readOnly checked={checked} className="accent-violet-500 pointer-events-none" style={{ flexShrink: 0 }} />
                <span style={{ fontFamily: 'Inter', fontSize: 11, color: checked ? '#c4b5fd' : '#D4D4D8', whiteSpace: 'nowrap' }}>{v}</span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Collapsible data table with per-column multi-select filters ──────────── */
function DataTable({ title, rows, headers, filename }) {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({});

  if (!rows?.length) return null;

  const clearFilters = () => setFilters({});

  const uniqueValues = headers.reduce((acc, h) => {
    acc[h] = [...new Set(rows.map(r => String(r[h] ?? '')).filter(v => v && v !== '—'))].sort();
    return acc;
  }, {});

  const filtered = rows.filter(row =>
    headers.every(h => {
      const sel = filters[h] || [];
      if (!sel.length) return true;
      return sel.includes(String(row[h] ?? ''));
    })
  );

  const hasActiveFilter = Object.values(filters).some(f => f.length > 0);

  return (
    <div className="rounded-xl border border-white/8 overflow-hidden">
      <div className="w-full flex items-center justify-between px-5 py-4 bg-white/3">
        <button onClick={() => setOpen(o => !o)} className="flex items-center gap-3 text-left flex-1">
          <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 16, color: '#fff' }}>{title}</span>
          <span style={{ fontFamily: 'Inter', fontSize: 11, color: '#71717A' }}>{rows.length} records</span>
          {hasActiveFilter && (
            <span style={{ fontFamily: 'Inter', fontSize: 11, color: '#c4b5fd', background: 'rgba(109,40,217,0.2)', borderRadius: 4, padding: '1px 6px' }}>
              {filtered.length} shown
            </span>
          )}
          <span style={{ color: '#71717A', fontSize: 18, lineHeight: 1 }}>{open ? '−' : '+'}</span>
        </button>
        <button onClick={() => downloadCsv(rows, headers, filename)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-violet-300 text-xs transition-colors"
          style={{ background: 'rgba(109,40,217,0.15)', border: '1px solid rgba(109,40,217,0.25)', fontFamily: 'Inter', flexShrink: 0 }}>
          <DownloadSimple size={13} /> CSV
        </button>
      </div>
      {open && (
        <div className="p-5 border-t border-white/8">
          <div className="overflow-x-auto rounded-lg border border-white/8 mb-4">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'Inter', fontSize: 12 }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.04)' }}>
                  {headers.map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#71717A',
                      fontWeight: 600, letterSpacing: '0.5px', borderBottom: '1px solid rgba(255,255,255,0.08)', whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
                <tr style={{ background: 'rgba(109,40,217,0.08)' }}>
                  {headers.map(h => (
                    <th key={h} style={{ padding: '5px 8px' }}>
                      <ColumnFilter
                        values={uniqueValues[h]}
                        selected={filters[h] || []}
                        onChange={sel => setFilters(prev => ({ ...prev, [h]: sel }))}
                      />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    {headers.map(h => (
                      <td key={h} style={{ padding: '7px 12px', color: '#D4D4D8', maxWidth: 280,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {String(row[h] || '').startsWith('http')
                          ? <a href={row[h]} target="_blank" rel="noreferrer" className="text-violet-400 underline underline-offset-2 hover:text-violet-300 transition-colors">View</a>
                          : (row[h] || '—')}
                      </td>
                    ))}
                  </tr>
                ))}
                {!filtered.length && (
                  <tr>
                    <td colSpan={headers.length} style={{ padding: '14px 12px', textAlign: 'center', color: '#52525B', fontFamily: 'Inter', fontSize: 12 }}>
                      No rows match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {hasActiveFilter && (
              <button onClick={clearFilters}
                style={{ fontFamily: 'Inter', fontSize: 11, color: '#71717A', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
                Clear filters
              </button>
            )}
            <button onClick={() => downloadCsv(filtered, headers, filename)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-violet-300 transition-colors"
              style={{ background: 'rgba(109,40,217,0.15)', border: '1px solid rgba(109,40,217,0.25)', fontFamily: 'Inter', fontSize: 12 }}>
              <DownloadSimple size={14} /> Download {filename} ({filtered.length} rows)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* Irs990AnalysisCandidates removed — 990s now shown as plain DataTable like FARA */


/* ── Report section ─────────────────────────────────────────────────────── */
function Report({ text }) {
  if (!text) return null;
  return (
    <div className="glass-card p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="app-output-header !mb-0">Summary Report</div>
        <button onClick={() => downloadText(text, 'disclosure_report.md')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-violet-300 transition-colors"
          style={{ background: 'rgba(109,40,217,0.15)', border: '1px solid rgba(109,40,217,0.25)', fontFamily: 'Inter', fontSize: 12 }}>
          <DownloadSimple size={14} /> Download .md
        </button>
      </div>
      <StyledMarkdown>{text}</StyledMarkdown>
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────── */
export default function InfluenceTracker() {
  const [entities, setEntities]           = useState('');
  const [searchField, setSearchField]     = useState('both');
  const [allYears, setAllYears]           = useState(false);
  const [selectedYears, setSelectedYears] = useState([String(CUR_YEAR - 1)]);
  const [quarters, setQuarters]           = useState(['Q1','Q2','Q3','Q4']);
  const [sources, setSources]             = useState(['lda','irs990']);
  const [maxResults, setMaxResults]       = useState('500');
  const [fuzzyThreshold, setFuzzyThreshold] = useState('85');
  const [dryRun, setDryRun]               = useState(false);
  const [llmModel, setLlmModel]           = useState('ChangeAgent');
  const [selectedClients, setSelectedClients] = useState(null);
  const [selectedRegistrants, setSelectedRegistrants] = useState(null);
  const [job, setJob]     = useState(null);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  // Polling
  useEffect(() => {
    if (!job || !['pending','processing'].includes(job.status)) return;
    intervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/jobs/${job.id}/status`);
        const data = await res.json();
        setJob(data);
        if (['completed','failed'].includes(data.status)) {
          setLoading(false);
          setAnalysisPendingKey(null);
          clearInterval(intervalRef.current);
        }
      } catch (error) {
        console.debug(error);
      }
    }, 2000);
    return () => clearInterval(intervalRef.current);
  }, [job]);

  const toggleQuarter = q => setQuarters(prev => prev.includes(q) ? prev.filter(x => x !== q) : [...prev, q]);
  const toggleSource  = s => setSources(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!entities.trim()) return;
    if (!quarters.length) { alert('Select at least one quarter.'); return; }
    if (!allYears && !selectedYears.length) { alert('Select at least one year.'); return; }
    setLoading(true);
    setJob(null);
    setSelectedClients(null);
    setSelectedRegistrants(null);
    const payload = new FormData();
    payload.append('entities', entities);
    payload.append('search_field', searchField);
    payload.append('all_years', allYears ? 'true' : 'false');
    if (!allYears) payload.append('filing_years', selectedYears.join(','));
    payload.append('quarters', quarters.join(','));
    payload.append('sources', sources.join(','));
    payload.append('mode', 'basic');
    payload.append('max_results', maxResults);
    payload.append('fuzzy_threshold', fuzzyThreshold);
    payload.append('dry_run', dryRun ? 'true' : 'false');
    payload.append('llm_model', llmModel);
    try {
      const res = await fetch(`${API}/api/tools/execute/influence_disclosure_tracker`, { method: 'POST', body: payload });
      const data = await res.json();
      if (data.job_id) setJob({ id: data.job_id, status: 'pending', progress: 0, message: 'Queued' });
    } catch { setLoading(false); }
  };

  const result = job?.result_data;
  const rawCsvData = result?.csv_data || {};
  const matchedNames = extractMatchedNames(rawCsvData);
  const topClient = matchedNames.clients[0] ?? null;
  const topRegistrant = matchedNames.registrants[0] ?? null;
  // When no clients exist (990-only results), pre-select only the top registrant and no clients.
  // When clients exist (LDA/FARA), pre-select top client + their associated registrants.
  const defaultRegistrants = topClient
    ? getAssociatedRegistrants(rawCsvData, topClient)
    : (topRegistrant ? [topRegistrant] : []);
  const effectiveSelectedClients = selectedClients ?? (topClient ? [topClient] : []);
  const effectiveSelectedRegistrants = selectedRegistrants ?? defaultRegistrants;
  const allowedNames = new Set([...effectiveSelectedClients, ...effectiveSelectedRegistrants]);
  const csvData = filterCsvData(rawCsvData, allowedNames);
  const hasAnyMatchedNames = matchedNames.clients.length > 0 || matchedNames.registrants.length > 0;
  const reportText = hasAnyMatchedNames
    ? filterReport(result?.report || '', allowedNames)
    : (result?.report || '');
  const pipelineStdout = result?.stdout || '';
  const pipelineStderr = result?.stderr || '';

  const ldaFilings = (csvData.lda_filings || []).map(r => ({
    Firm: r.registrant_name || '—', Client: r.client_name || '—',
    Year: r.filing_year || '—', Quarter: r.filing_period || '—',
    Type: r.filing_type || '—',
    Amount: (() => { try { return r.amount ? `$${parseFloat(r.amount).toLocaleString('en-US', {maximumFractionDigits:0})}` : '—'; } catch { return r.amount || '—'; } })(),
    Link: r.filing_url || '—',
  }));
  const ldaIssues = (csvData.lda_issues || []).map(r => ({
    Firm: r.registrant || '—', Client: r.client || '—',
    'Issue Area': r.issue_area || '—', Topics: r.description || '—',
    'Gov. Entities': r.government_entities || '—',
  }));
  const seen = {};
  (csvData.lda_lobbyists || []).forEach(r => { const n = r.lobbyist_name?.trim(); if (n && !seen[n]) seen[n] = r; });
  const ldaLobbyists = Object.values(seen).sort((a,b) => (a.lobbyist_name||'').localeCompare(b.lobbyist_name||'')).map(r => ({
    Lobbyist: r.lobbyist_name || '—', Firm: r.registrant || '—',
    Client: r.client || '—', 'Former Gov. Position': r.covered_position || '—',
  }));
  const faraFPs = (() => {
    const seen2 = {};
    (csvData.fara_foreign_principals || []).forEach(r => {
      const k = (r.registration_number||'')+(r.foreign_principal_name||'');
      if (!seen2[k]) seen2[k] = r;
    });
    return Object.values(seen2).map(r => ({
      'Foreign Principal': r.foreign_principal_name || '—', Country: r.state_or_country || '—',
      Registrant: r.registrant_name || '—', Registered: r.foreign_principal_date || '—',
      Terminated: r.foreign_principal_term_date || '—',
    }));
  })();
  const faraDocs = (csvData.fara_documents || []).map(r => ({
    Date: r.document_date || '—', Type: r.document_type || '—',
    Registrant: r.registrant_name || '—', 'Foreign Principal': r.foreign_principal_name || '—',
    Link: r.document_url || '—',
  }));
  const fmtMoney = v => { try { return v ? `$${parseFloat(v).toLocaleString('en-US',{maximumFractionDigits:0})}` : '—'; } catch { return v||'—'; } };
  const irs990Filings = (csvData.irs990_filings || []).map(r => ({
    Organization: r.organization_name||'—', Year: r.tax_year||'—', Type: r.form_type||'—',
    Revenue: fmtMoney(r.total_revenue), Expenses: fmtMoney(r.total_functional_expenses),
    Assets: fmtMoney(r.net_assets), PDF: r.pdf_url||'—',
  }));

  const hasCompletedRun = job?.status === 'completed';
  const hasAnyVisibleData = Boolean(reportText || ldaFilings.length || faraFPs.length || irs990Filings.length);
  const showReport = Boolean(reportText);

  return (
    <motion.div data-testid="tool-page-influence-tracker" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="app-page-shell app-page-shell-wide">

      {/* Header */}
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
             style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <h1 data-testid="page-title-influence-tracker" className="app-page-title">Influence Disclosure Tracker</h1>
        <p className="app-page-intro" style={{ maxWidth: '60ch' }}>
          Retrieves and normalizes LDA lobbying, FARA foreign agent, and IRS 990 disclosure records — producing filterable tables and a markdown summary report.
        </p>
        <div className="mt-3">
          <ModelSelector value={llmModel} onChange={setLlmModel} />
        </div>
      </header>

      <ResearchPrototypeNote
        category="Policy Monitoring and Legislative Tracking"
        refs={['bitonti2023', 'digiacomo2025']}
        message="This tool supports disclosure research by collecting structured records and match confidence signals. It strengthens the intelligence-gathering layer of the prototype, but filing matches, document coverage, and narrative interpretation should still be reviewed before strategic use."
      />

      {/* Form */}
      <form onSubmit={handleSubmit} className="glass-card p-8 flex flex-col gap-6 relative overflow-hidden mb-8">
        <div className="absolute top-0 right-0 w-48 h-48 rounded-full pointer-events-none"
             style={{ background: 'rgba(109,40,217,0.06)', filter: 'blur(60px)' }} />

        {/* Entities */}
        <div>
          <label className="field-label">Entities to search</label>
          <input data-testid="input-influence-entities" type="text" value={entities} onChange={e => setEntities(e.target.value)}
            placeholder="e.g. Microsoft, OpenAI" required className="field" />
        </div>

        {/* Search scope */}
        <div>
          <label className="field-label">Search scope</label>
          <div className="flex flex-wrap gap-5 pt-1">
            {[['client','Client'],['registrant','Lobbying firm (registrant)'],['both','Both']].map(([v,l]) => (
              <label key={v} className="flex items-center gap-2 cursor-pointer">
                <input data-testid={`toggle-influence-search-field-${v}`} type="radio" name="search_field" value={v} checked={searchField===v}
                  onChange={() => setSearchField(v)} className="accent-violet-500" />
                <span style={{ fontFamily: 'Inter', fontSize: 13, color: '#D4D4D8' }}>{l}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Years */}
          <div>
            <label className="field-label">Filing Years</label>
            <label className="flex items-center gap-2 mb-3 cursor-pointer">
              <input data-testid="toggle-influence-all-years" type="checkbox" checked={allYears} onChange={e => setAllYears(e.target.checked)} className="accent-violet-500" />
              <span style={{ fontFamily: 'Inter', fontSize: 13, color: allYears ? '#A78BFA' : '#D4D4D8' }}>
                All available years
              </span>
            </label>
            {!allYears && (
              <YearDropdown selected={selectedYears} onChange={setSelectedYears} />
            )}
          </div>

          {/* Quarters */}
          <div>
            <label className="field-label">Quarters</label>
            <div className="flex gap-2 pt-1">
              {['Q1','Q2','Q3','Q4'].map(q => (
                <button data-testid={`toggle-influence-quarter-${q.toLowerCase()}`} key={q} type="button" onClick={() => toggleQuarter(q)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                  style={quarters.includes(q)
                    ? { background: 'rgba(109,40,217,0.35)', color: '#c4b5fd', border: '1px solid rgba(109,40,217,0.5)' }
                    : { background: 'rgba(255,255,255,0.04)', color: '#71717A', border: '1px solid rgba(255,255,255,0.08)' }}>
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Sources */}
          <div>
            <label className="field-label">Data Sources</label>
            <div className="flex flex-wrap gap-2 pt-1 mb-3">
              {[['lda','LDA'],['fara','FARA'],['irs990','IRS 990']].map(([v,l]) => (
                <button data-testid={`toggle-influence-source-${v}`} key={v} type="button" onClick={() => toggleSource(v)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                  style={sources.includes(v)
                    ? { background: 'rgba(109,40,217,0.35)', color: '#c4b5fd', border: '1px solid rgba(109,40,217,0.5)' }
                    : { background: 'rgba(255,255,255,0.04)', color: '#71717A', border: '1px solid rgba(255,255,255,0.08)' }}>
                  {l}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Advanced */}
        <details className="rounded-xl border border-white/8 overflow-hidden">
          <summary className="px-4 py-3 cursor-pointer bg-white/3 hover:bg-white/5 transition-colors"
            style={{ fontFamily: 'Inter', fontSize: 13, color: '#71717A' }}>
            Advanced options
          </summary>
          <div className="p-4 border-t border-white/8 grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Max results per entity</label>
              <input data-testid="input-influence-max-results" type="number" value={maxResults} onChange={e => setMaxResults(e.target.value)}
                min="10" max="5000" className="field" style={{ fontFamily: 'Inter', fontSize: 13 }} />
            </div>
            <div>
              <label className="field-label">Fuzzy match threshold (50–100)</label>
              <input data-testid="input-influence-fuzzy-threshold" type="range" min="50" max="100" value={fuzzyThreshold}
                onChange={e => setFuzzyThreshold(e.target.value)} className="w-full accent-violet-500 mt-2" />
              <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#71717A' }}>{fuzzyThreshold}</span>
            </div>
            <div className="col-span-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input data-testid="toggle-influence-dry-run" type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} className="accent-violet-500" />
                <span style={{ fontFamily: 'Inter', fontSize: 13, color: '#D4D4D8' }}>Dry run (skip API calls)</span>
              </label>
            </div>
          </div>
        </details>

        <button data-testid="submit-influence-tracker" type="submit" disabled={loading || !entities.trim()} className="btn-primary mt-2">
          {loading
            ? <><SpinnerGap size={18} className="animate-spin" /> Querying disclosure databases…</>
            : <>Search Disclosures <ArrowRight size={18} /></>}
        </button>
      </form>

      {/* Progress */}
      {job && ['pending','processing'].includes(job.status) && (
        <div data-testid="status-influence-tracker" className="glass-card p-6 mb-8 flex flex-col gap-3">
          <div className="flex justify-between">
            <span style={{ fontFamily: 'Inter', fontSize: 13, color: '#D4D4D8' }}>
              {job.message}
            </span>
            <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#A78BFA' }}>{job.progress}%</span>
          </div>
          <div className="progress-track">
            <motion.div className="progress-fill" animate={{ width: `${job.progress}%` }} transition={{ ease: 'circOut', duration: 0.4 }} />
          </div>
        </div>
      )}

      {/* Failed */}
      {job?.status === 'failed' && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/8 p-5 mb-8">
          <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#fca5a5' }}>{job.message}</p>
        </div>
      )}

      {pipelineStdout && (
        <details className="glass-card p-6 mb-6">
          <summary className="cursor-pointer text-white font-semibold">Pipeline Log</summary>
          <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{pipelineStdout}</pre>
        </details>
      )}

      {pipelineStderr && (
        <details className="glass-card p-6 mb-6">
          <summary className="cursor-pointer text-white font-semibold">Errors / Warnings</summary>
          <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-300">{pipelineStderr}</pre>
        </details>
      )}

      {/* Results */}
      <AnimatePresence>
        {hasCompletedRun && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-6">

            {(matchedNames.clients.length > 0 || matchedNames.registrants.length > 0) && (
              <div className="glass-card p-8">
                <h2 className="app-surface-title">Review Matched Entities</h2>
                <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#A1A1AA', marginBottom: 16 }}>
                  Deselect names you do not want included in the report and data tables.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="field-label">Clients (entities represented)</label>
                    <div className="mt-2 flex flex-col gap-2">
                      {matchedNames.clients.map((name) => (
                        <label key={name} className="flex items-center gap-2 text-sm text-slate-300">
                          <input
                            type="checkbox"
                            checked={effectiveSelectedClients.includes(name)}
                            onChange={() => {
                              const isAdding = !effectiveSelectedClients.includes(name);
                              setSelectedClients((prev) => {
                                const base = prev ?? effectiveSelectedClients;
                                return base.includes(name) ? base.filter((item) => item !== name) : [...base, name];
                              });
                              const assocRegs = getAssociatedRegistrants(rawCsvData, name);
                              setSelectedRegistrants((prev) => {
                                const baseRegs = prev ?? effectiveSelectedRegistrants;
                                if (isAdding) {
                                  return [...new Set([...baseRegs, ...assocRegs])];
                                } else {
                                  const remainingClients = effectiveSelectedClients.filter(c => c !== name);
                                  const stillNeeded = new Set(remainingClients.flatMap(c => getAssociatedRegistrants(rawCsvData, c)));
                                  return baseRegs.filter(r => stillNeeded.has(r) || !assocRegs.includes(r));
                                }
                              });
                            }}
                            className="accent-violet-500"
                          />
                          <span>{name} <span className="text-slate-500 text-xs">({matchedNames.clientCounts[name]})</span></span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="field-label">Lobbying firms (registrants)</label>
                    <div className="mt-2 flex flex-col gap-2">
                      {matchedNames.registrants.map((name) => (
                        <label key={name} className="flex items-center gap-2 text-sm text-slate-300">
                          <input
                            type="checkbox"
                            checked={effectiveSelectedRegistrants.includes(name)}
                            onChange={() => setSelectedRegistrants((prev) => {
                              const base = prev ?? effectiveSelectedRegistrants;
                              return base.includes(name) ? base.filter((item) => item !== name) : [...base, name];
                            })}
                            className="accent-violet-500"
                          />
                          <span>{name} <span className="text-slate-500 text-xs">({matchedNames.registrantCounts[name]})</span></span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {showReport && <Report text={reportText} />}

            {/* LDA tables */}
            {(ldaFilings.length > 0 || ldaIssues.length > 0 || ldaLobbyists.length > 0) && (
              <div>
                <h2 className="app-surface-title">LDA Data Tables</h2>
                <div className="flex flex-col gap-3">
                  <DataTable title="Filings & Spending" rows={ldaFilings}
                    headers={['Firm','Client','Year','Quarter','Type','Amount','Link']} filename="lda_filings.csv" />
                  <DataTable title="Issues & Government Entities" rows={ldaIssues}
                    headers={['Firm','Client','Issue Area','Topics','Gov. Entities']} filename="lda_issues.csv" />
                  <DataTable title="Lobbyists" rows={ldaLobbyists}
                    headers={['Lobbyist','Firm','Client','Former Gov. Position']} filename="lda_lobbyists.csv" />
                </div>
              </div>
            )}

            {/* FARA tables */}
            {(faraFPs.length > 0 || faraDocs.length > 0) && (
              <div>
                <h2 className="app-surface-title">FARA Data Tables</h2>
                <div className="flex flex-col gap-3">
                  <DataTable title="Foreign Principals" rows={faraFPs}
                    headers={['Foreign Principal','Country','Registrant','Registered','Terminated']} filename="fara_foreign_principals.csv" />
                  <DataTable title="FARA Documents" rows={faraDocs}
                    headers={['Date','Type','Registrant','Foreign Principal','Link']} filename="fara_documents.csv" />
                </div>
              </div>
            )}

            {/* IRS 990 tables */}
            {irs990Filings.length > 0 && (
              <div>
                <h2 className="app-surface-title">IRS 990 Data Tables</h2>
                <div className="flex flex-col gap-3">
                  <DataTable title="IRS 990 Filings" rows={irs990Filings}
                    headers={['Organization','Year','Type','Revenue','Expenses','Assets','PDF']} filename="irs990_filings.csv" />
                </div>
              </div>
            )}

            {!hasAnyVisibleData && (
              <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/8 p-5">
                <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#fde68a' }}>
                  No results found. This may happen if no disclosures match the entities and years selected.
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
