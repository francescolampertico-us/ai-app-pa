/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';

const STATES = ['US (Federal)', 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'];
const CUR_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: CUR_YEAR - 1999 }, (_, i) => CUR_YEAR - i);

function StatusPanel({ job }) {
  if (!job) return null;
  return (
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
  );
}

export default function LegislativeTracker() {
  const { job, loading, submitJob, downloadArtifact, downloadJson, downloadText } = useFastApiJob('legislative_tracker');

  const [activeTab, setActiveTab] = useState('Search & Discover');
  const [query, setQuery] = useState('');
  const [stateCode, setStateCode] = useState('US (Federal)');
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [maxResults, setMaxResults] = useState('10');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedBill, setSelectedBill] = useState(null);
  const [billSummary, setBillSummary] = useState('');
  const [billDetail, setBillDetail] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [watchlistReport, setWatchlistReport] = useState('');
  const initializedRef = useRef(false);

  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  useEffect(() => {
    if (job?.status !== 'completed' || !job.result_data) return;
    const action = job.result_data.action;
    if (action === 'search') {
      setSearchResults(job.result_data.results || []);
      setSelectedBill(null);
      setBillSummary('');
      setBillDetail(null);
      setActiveTab('Search & Discover');
    } else if (action === 'summarize') {
      setBillSummary(job.result_data.summary || '');
      setBillDetail(job.result_data.bill || null);
      setActiveTab('Search & Discover');
    } else if (action?.startsWith('watchlist_')) {
      setWatchlist(job.result_data.watchlist || []);
      setWatchlistReport(job.result_data.report || '');
      if (action !== 'watchlist_list') {
        setActiveTab('Watchlist');
      }
    }
  }, [job]);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    const payload = new FormData();
    payload.append('action', 'watchlist_list');
    submitJob(payload);
  }, [submitJob]);

  const stateValue = stateCode === 'US (Federal)' ? 'US' : stateCode;

  const runAction = (data) => {
    const payload = new FormData();
    Object.entries(data).forEach(([key, value]) => payload.append(key, value));
    submitJob(payload);
  };

  const handleSearch = (event) => {
    event.preventDefault();
    runAction({ action: 'search', query, state: stateValue, year, max_results: maxResults });
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-10 max-w-6xl mx-auto relative z-10">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '2px', color: 'rgba(167,139,250,0.5)', marginBottom: 10 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>tegitect · TOOL
        </div>
        <h1 className="display" style={{ fontSize: 42, color: '#fff', marginBottom: 10 }}>Legislative Tracker</h1>
        <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#71717A', lineHeight: 1.65, maxWidth: '70ch', fontWeight: 300 }}>
          Search, track, and summarize legislation across federal and state jurisdictions, then maintain a live watchlist.
        </p>
      </header>

      <div className="flex flex-wrap gap-3 mb-8">
        {['Search & Discover', 'Watchlist'].map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg border text-sm ${activeTab === tab ? 'bg-violet-500/20 border-violet-400/40 text-violet-200' : 'bg-white/5 border-white/10 text-slate-300'}`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Search & Discover' && (
        <div className="space-y-8">
          <form onSubmit={handleSearch} className="glass-card p-8 grid grid-cols-1 lg:grid-cols-[3fr_1fr_1fr_1fr] gap-4">
            <div>
              <label className="field-label">Search Keywords</label>
              <input value={query} onChange={(event) => setQuery(event.target.value)} className="field" placeholder="e.g. artificial intelligence, data privacy" required />
            </div>
            <div>
              <label className="field-label">Jurisdiction</label>
              <select value={stateCode} onChange={(event) => setStateCode(event.target.value)} className="field">
                {STATES.map((state) => <option key={state} value={state}>{state}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Year</label>
              <select value={year} onChange={(event) => setYear(event.target.value)} className="field">
                {YEARS.map(y => <option key={y} value={String(y)}>{y}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Results</label>
              <select value={maxResults} onChange={(event) => setMaxResults(event.target.value)} className="field">
                <option value="1">Best match only</option>
                <option value="5">Top 5</option>
                <option value="10">Top 10</option>
                <option value="25">Top 25</option>
                <option value="">All</option>
              </select>
            </div>
            <button type="submit" disabled={loading || !query.trim()} className="btn-primary lg:col-span-4 mt-2">
              {loading ? <><SpinnerGap size={18} className="animate-spin" /> Searching…</> : <>Search Bills <ArrowRight size={18} /></>}
            </button>
          </form>

          <StatusPanel job={job} />

          {searchResults.length > 0 && (
            <div className="space-y-4">
              <div className="glass-card p-6 overflow-x-auto">
                <table className="w-full text-sm text-left text-slate-300">
                  <thead className="text-slate-500 uppercase tracking-wider text-xs border-b border-white/10">
                    <tr>
                      <th className="py-3 pr-4">Bill</th>
                      <th className="py-3 pr-4">Title</th>
                      <th className="py-3 pr-4">State</th>
                      <th className="py-3 pr-4">Status</th>
                      <th className="py-3 pr-4">Date</th>
                      <th className="py-3 pr-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((bill) => (
                      <tr key={bill.bill_id} className={`border-b border-white/5 ${selectedBill?.bill_id === bill.bill_id ? 'bg-violet-500/10' : ''}`}>
                        <td className="py-3 pr-4">{bill.number}</td>
                        <td className="py-3 pr-4">{bill.title}</td>
                        <td className="py-3 pr-4">{bill.state}</td>
                        <td className="py-3 pr-4">{bill.status}</td>
                        <td className="py-3 pr-4">{bill.last_action_date}</td>
                        <td className="py-3 pr-4 flex flex-wrap gap-2">
                          <button type="button" onClick={() => setSelectedBill(bill)} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">Select</button>
                          <button type="button" onClick={() => runAction({ action: 'watchlist_add', bill_id: String(bill.bill_id) })} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">Track</button>
                          <button type="button" onClick={() => { setSelectedBill(bill); runAction({ action: 'summarize', bill_id: String(bill.bill_id) }); }} className="px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200">Summarize</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <button onClick={() => downloadJson(searchResults, 'search_results.json')}
                  className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm">
                  <DownloadSimple size={16} className="inline mr-2" /> Download Full Results (JSON)
                </button>
              </div>
            </div>
          )}

          {selectedBill && (
            <div className="glass-card p-8 space-y-4">
              <div>
                <h2 className="display" style={{ fontSize: 24, color: '#fff' }}>{selectedBill.number} — {selectedBill.title}</h2>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-300">
                  <span><strong className="text-white">State:</strong> {selectedBill.state}</span>
                  <span><strong className="text-white">Status:</strong> {selectedBill.status}</span>
                  <span><strong className="text-white">Date:</strong> {selectedBill.last_action_date}</span>
                  {selectedBill.url && <a href={selectedBill.url} target="_blank" rel="noreferrer" className="text-violet-300 underline">View on LegiScan</a>}
                </div>
                {selectedBill.last_action && <p className="text-slate-400 mt-3">{selectedBill.last_action}</p>}
              </div>

              {billSummary && (
                <div className="space-y-4">
                  <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4 text-violet-100 whitespace-pre-wrap">{billSummary}</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button onClick={() => downloadText(billSummary, 'bill_summary.md')}
                      className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                      <DownloadSimple size={18} /> Download Summary
                    </button>
                    <button onClick={() => downloadJson(billDetail || {}, 'bill_detail.json')}
                      className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                      <DownloadSimple size={18} /> Download Bill Detail
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'Watchlist' && (
        <div className="space-y-8">
          <div className="glass-card p-8 flex flex-wrap gap-3">
            <button onClick={() => runAction({ action: 'watchlist_list' })}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300">Reload Watchlist</button>
            <button onClick={() => runAction({ action: 'watchlist_refresh' })}
              className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200">Refresh All</button>
          </div>

          <StatusPanel job={job} />

          <div className="glass-card p-8">
            {watchlist.length > 0 ? (
              <div className="space-y-4">
                {watchlist.map((bill) => (
                  <div key={bill.bill_id} className="rounded-xl border border-white/10 bg-black/20 px-5 py-4 flex flex-col gap-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-white font-medium">{bill.number} — {bill.title}</p>
                        <p className="text-slate-400 text-sm mt-1">{bill.state} · {bill.status} · {bill.last_action_date}</p>
                        {bill.added_at && <p className="text-slate-500 text-xs mt-1">Tracked since {String(bill.added_at).slice(0, 10)}</p>}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button onClick={() => runAction({ action: 'summarize', bill_id: String(bill.bill_id) })}
                          className="px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm">Summarize</button>
                        <button onClick={() => runAction({ action: 'watchlist_remove', bill_id: String(bill.bill_id) })}
                          className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm">Remove</button>
                      </div>
                    </div>
                    {bill.url && <a href={bill.url} target="_blank" rel="noreferrer" className="text-violet-300 underline text-sm">View on LegiScan</a>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400">No bills in watchlist.</p>
            )}
          </div>

          {watchlistReport && (
            <div className="glass-card p-8">
              <pre className="whitespace-pre-wrap text-sm text-slate-300">{watchlistReport}</pre>
              <div className="mt-4">
                {artifactMap['watchlist_report.md'] && (
                  <button onClick={() => downloadArtifact(artifactMap['watchlist_report.md'])}
                    className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm">
                    <DownloadSimple size={16} className="inline mr-2" /> Download Watchlist Report
                  </button>
                )}
              </div>
            </div>
          )}

          {job?.result_data?.refresh_results?.length > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-amber-200 text-sm">
              {job.result_data.refresh_results.filter((item) => item.changed).length > 0
                ? `${job.result_data.refresh_results.filter((item) => item.changed).length} tracked bill(s) changed status on refresh.`
                : 'All tracked bills are up to date.'}
            </div>
          )}
        </div>
      )}

      <p className="mt-8 text-sm text-slate-500">
        AI-generated summaries require review before external use. Verify bill provisions, sponsors, and talking points against official sources.
      </p>
    </motion.div>
  );
}
