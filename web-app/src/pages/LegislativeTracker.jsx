/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRightIcon as ArrowRight, DownloadSimpleIcon as DownloadSimple, SpinnerGapIcon as SpinnerGap } from '@phosphor-icons/react';
import { useFastApiJob } from '../hooks/useFastApiJob';
import ModelSelector from '../components/ModelSelector';
import StyledMarkdown from '../components/StyledMarkdown';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';
import ToolTourButton from '../components/tour/ToolTourButton';
import { TOOL_TOUR_IDS } from '../components/tour/tourDefinitions';

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
  const [searchMode, setSearchMode] = useState('broad'); // 'broad' | 'exact'
  const [query, setQuery] = useState('');
  const [stateCode, setStateCode] = useState('US (Federal)');
  const [year, setYear] = useState('');
  const [maxResults, setMaxResults] = useState('10');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedBill, setSelectedBill] = useState(null);
  const [billSummary, setBillSummary] = useState('');
  const [billCaveats, setBillCaveats] = useState([]);
  const [billDetail, setBillDetail] = useState(null);
  const [summaryStatus, setSummaryStatus] = useState('');
  const [sourceTextStatus, setSourceTextStatus] = useState('');
  const [sourceStatus, setSourceStatus] = useState('');
  const [extractionStatus, setExtractionStatus] = useState('');
  const [verificationStatus, setVerificationStatus] = useState('');
  const [extractionCoverage, setExtractionCoverage] = useState(null);
  const [coverageMode, setCoverageMode] = useState('');
  const [evidenceCoverage, setEvidenceCoverage] = useState(null);
  const [validationFlags, setValidationFlags] = useState([]);
  const [unsupportedClaims, setUnsupportedClaims] = useState([]);
  const [summaryLevel, setSummaryLevel] = useState('');
  const [pendingSummaryLevel, setPendingSummaryLevel] = useState('');
  const [watchlist, setWatchlist] = useState([]);
  const [watchlistReport, setWatchlistReport] = useState('');
  const [llmModel, setLlmModel] = useState('ChangeAgent');
  const [watchlistBusyBillId, setWatchlistBusyBillId] = useState(null);
  const initializedRef = useRef(false);
  const selectedBillRef = useRef(null);

  const artifactMap = useMemo(
    () => (job?.artifacts || []).reduce((acc, artifact) => ({ ...acc, [artifact.name]: artifact }), {}),
    [job?.artifacts],
  );

  useEffect(() => {
    if (!job?.result_data) return;
    const action = job.result_data.action;
    if (action === 'search') {
      if (job.status !== 'completed') return;
      setSearchResults(job.result_data.results || []);
      setSelectedBill(null);
      setBillSummary('');
      setBillCaveats([]);
      setBillDetail(null);
      setSummaryStatus('');
      setSourceTextStatus('');
      setSourceStatus('');
      setExtractionStatus('');
      setVerificationStatus('');
      setExtractionCoverage(null);
      setCoverageMode('');
      setEvidenceCoverage(null);
      setValidationFlags([]);
      setUnsupportedClaims([]);
      setSummaryLevel('');
      setPendingSummaryLevel('');
      setWatchlistBusyBillId(null);
      setActiveTab('Search & Discover');
    } else if (action === 'summarize') {
      const bill = job.result_data.bill || null;
      setBillSummary(job.result_data.summary || '');
      setBillCaveats(job.result_data.caveats || []);
      setBillDetail(bill);
      setSummaryStatus(job.result_data.summary_status || '');
      setSourceTextStatus(job.result_data.source_text_status || '');
      setSourceStatus(job.result_data.source_status || '');
      setExtractionStatus(job.result_data.extraction_status || '');
      setVerificationStatus(job.result_data.verification_status || '');
      setExtractionCoverage(job.result_data.extraction_coverage || null);
      setCoverageMode(job.result_data.coverage_mode || '');
      setEvidenceCoverage(job.result_data.evidence_coverage || null);
      setValidationFlags(job.result_data.validation_flags || []);
      setUnsupportedClaims(job.result_data.unsupported_claims || []);
      setSummaryLevel(job.result_data.summary_level || '');
      setPendingSummaryLevel('');
      setWatchlistBusyBillId(null);
      if (bill) setSelectedBill(bill);
      setActiveTab('Search & Discover');
    } else if (action?.startsWith('watchlist_')) {
      if (job.status !== 'completed') return;
      setWatchlist(job.result_data.watchlist || []);
      setWatchlistReport(job.result_data.report || '');
      setWatchlistBusyBillId(null);
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
  const isLongBillSummary =
    summaryLevel === 'detailed' &&
    ((evidenceCoverage?.total_chunks ?? 0) >= 6 || (extractionCoverage?.total_sections ?? 0) >= 6);
  const showDetailedWaitNotice =
    loading && (
      pendingSummaryLevel === 'detailed' ||
      summaryLevel === 'detailed' ||
      (job?.message || '').toLowerCase().includes('detailed bill summary')
    );

  const resetSelectedBillState = (bill) => {
    setSelectedBill(bill);
    setBillSummary('');
    setBillCaveats([]);
    setBillDetail(null);
    setSummaryStatus('');
    setSourceTextStatus('');
    setSourceStatus('');
    setExtractionStatus('');
    setVerificationStatus('');
    setExtractionCoverage(null);
    setCoverageMode('');
    setEvidenceCoverage(null);
    setValidationFlags([]);
    setUnsupportedClaims([]);
    setSummaryLevel('');
    setPendingSummaryLevel('');
  };

  const scrollToSelectedBill = () => {
    window.requestAnimationFrame(() => {
      selectedBillRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  const startSummaryFromRow = (bill, level) => {
    resetSelectedBillState(bill);
    setPendingSummaryLevel(level);
    runAction({ action: 'summarize', bill_id: String(bill.bill_id), summary_level: level });
    scrollToSelectedBill();
  };

  const runAction = (data) => {
    const payload = new FormData();
    Object.entries({ ...data, llm_model: llmModel }).forEach(([key, value]) => payload.append(key, value));
    submitJob(payload);
  };

  const runWatchlistAction = (data) => {
    if (loading) return;
    setWatchlistBusyBillId(data.bill_id ? String(data.bill_id) : null);
    runAction(data);
  };

  const handleSearch = (event) => {
    event.preventDefault();
    runAction({
      action: 'search',
      query,
      state: stateValue,
      year,
      max_results: maxResults,
      title_only: searchMode === 'exact' ? 'true' : 'false',
    });
  };

  return (
    <motion.div data-testid="tool-page-legislative-tracker" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="app-page-shell app-page-shell-wide">
      <header className="page-header relative">
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.1) 0%, transparent 70%)' }} />
        <h1 data-testid="page-title-legislative-tracker" data-tour="legislative-tracker-title-heading" className="app-page-title">Legislative Tracker</h1>
        <p className="app-page-intro" style={{ maxWidth: '70ch' }}>
          Search, track, and summarize legislation across federal and state jurisdictions, then maintain a live watchlist.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <ModelSelector value={llmModel} onChange={setLlmModel} />
          <div data-tour="tour-button-legislative-tracker"><ToolTourButton tourId={TOOL_TOUR_IDS.legislativeTracker} /></div>
        </div>
      </header>

      <ResearchPrototypeNote
        category="Policy Monitoring and Legislative Tracking"
        refs={['nay2023', 'digiacomo2025', 'bitonti2023']}
        message="This tool supports recurring monitoring and legislative synthesis, which the research identifies as a strong fit for AI augmentation. Search results and summaries may still be incomplete or source-constrained, so they should be treated as review-required inputs to strategy rather than final analysis."
      />

      <div data-tour="legislative-tracker-tabs" className="flex flex-wrap gap-3 mb-8">
        {['Search & Discover', 'Watchlist'].map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg border text-sm ${activeTab === tab ? 'bg-violet-500/20 border-violet-400/40 text-violet-200' : 'bg-white/5 border-white/10 text-slate-300'}`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Search & Discover' && (
        <div className="space-y-8">
          <form onSubmit={handleSearch} className="glass-card p-8 flex flex-col gap-5">
            {/* Search mode toggle */}
            <div data-tour="legislative-tracker-search-mode" className="flex gap-6">
              {[['broad', 'Broad Search'], ['exact', 'Exact Title Match']].map(([mode, label]) => (
                <label key={mode} className="flex items-center gap-2 cursor-pointer">
                  <input data-testid={`toggle-legislative-search-mode-${mode}`} type="radio" checked={searchMode === mode} onChange={() => setSearchMode(mode)} className="accent-violet-500" />
                  <span className="text-sm text-slate-300">{label}</span>
                </label>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[3fr_1fr_1fr_1fr] gap-4">
              <div>
                <label className="field-label">{searchMode === 'exact' ? 'Exact Bill Title' : 'Keywords / Topic'}</label>
                <input
                  data-testid="input-legislative-query"
                  data-tour="legislative-tracker-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  className="field"
                  placeholder={searchMode === 'exact' ? 'e.g. Inflation Reduction Act' : 'e.g. artificial intelligence, data privacy'}
                  required
                />
              </div>
              <div data-tour="legislative-tracker-jurisdiction">
                <label className="field-label">Jurisdiction</label>
                <select data-testid="input-legislative-state" value={stateCode} onChange={(event) => setStateCode(event.target.value)} className="field">
                  {STATES.map((state) => <option key={state} value={state}>{state}</option>)}
                </select>
              </div>
              <div data-tour="legislative-tracker-year">
                <label className="field-label">Year</label>
                <select data-testid="input-legislative-year" value={year} onChange={(event) => setYear(event.target.value)} className="field">
                  <option value="">All years</option>
                  {YEARS.map(y => <option key={y} value={String(y)}>{y}</option>)}
                </select>
              </div>
              <div data-tour="legislative-tracker-results-limit">
                <label className="field-label">Results</label>
                <select data-testid="input-legislative-max-results" value={maxResults} onChange={(event) => setMaxResults(event.target.value)} className="field">
                  <option value="1">Best match only</option>
                  <option value="5">Top 5</option>
                  <option value="10">Top 10</option>
                  <option value="25">Top 25</option>
                  <option value="">All</option>
                </select>
              </div>
              <button data-testid="submit-legislative-search" data-tour="legislative-tracker-submit" type="submit" disabled={loading || !query.trim()} className="btn-primary lg:col-span-4 mt-1">
                {loading ? <><SpinnerGap size={18} className="animate-spin" /> Searching…</> : <>Search Bills <ArrowRight size={18} /></>}
              </button>
            </div>
          </form>

          {searchResults.length > 0 && (
            <div data-tour="legislative-tracker-results" className="space-y-4">
              <div className="glass-card p-6 overflow-x-auto">
                <table className="w-full text-sm text-left text-slate-300">
                  <thead className="text-slate-500 uppercase tracking-wider text-xs border-b border-white/10">
                    <tr>
                      <th className="py-3 pr-4">Bill</th>
                      <th className="py-3 pr-4">Title</th>
                      <th className="py-3 pr-4">Jurisdiction</th>
                      <th className="py-3 pr-4">Status</th>
                      <th className="py-3 pr-4">Date</th>
                      <th className="py-3 pr-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((bill) => (
                      <tr key={bill.bill_id} className={`border-b border-white/5 ${selectedBill?.bill_id === bill.bill_id ? 'bg-violet-500/10' : ''}`}>
                        <td className="py-3 pr-4">
                          <button
                            type="button"
                            onClick={() => resetSelectedBillState(bill)}
                            className="text-left text-inherit hover:text-violet-200 transition-colors cursor-pointer"
                          >
                            {bill.number}
                          </button>
                        </td>
                        <td className="py-3 pr-4">
                          <button
                            type="button"
                            onClick={() => resetSelectedBillState(bill)}
                            className="text-left text-inherit hover:text-violet-200 transition-colors cursor-pointer"
                          >
                            {bill.title}
                          </button>
                        </td>
                        <td className="py-3 pr-4">{bill.state === 'US' ? 'Federal' : bill.state}</td>
                        <td className="py-3 pr-4">{bill.status}</td>
                        <td className="py-3 pr-4">{bill.last_action_date}</td>
                        <td className="py-3 pr-4 flex flex-wrap gap-2">
                          <button
                            data-testid={`preview-legislative-bill-${bill.bill_id}`}
                            type="button"
                            disabled={loading}
                            onClick={() => startSummaryFromRow(bill, 'preview')}
                            className="px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-400/40 text-violet-200 text-sm hover:bg-violet-500/40 hover:border-violet-400/70 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Preview
                          </button>
                          <button
                            data-testid={`detailed-legislative-bill-${bill.bill_id}`}
                            type="button"
                            disabled={loading}
                            onClick={() => startSummaryFromRow(bill, 'detailed')}
                            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-200 text-sm hover:bg-white/10 hover:border-white/20 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Detailed
                          </button>
                          <button
                            data-testid={`track-legislative-bill-${bill.bill_id}`}
                            type="button"
                            disabled={loading}
                            onClick={() => runWatchlistAction({ action: 'watchlist_add', bill_id: String(bill.bill_id) })}
                            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm hover:bg-white/10 hover:border-white/20 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {loading && watchlistBusyBillId === String(bill.bill_id) ? 'Tracking…' : 'Track'}
                          </button>
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

          <div data-tour="legislative-tracker-output" data-testid="status-legislative-tracker">
            {job ? <StatusPanel job={job} /> : null}
          </div>
          {showDetailedWaitNotice && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-3 text-amber-200 text-sm">
              Detailed summaries for longer bills can take a few minutes.
            </div>
          )}

          {selectedBill && (
            <div data-tour="legislative-tracker-output" ref={selectedBillRef} className="glass-card p-8 space-y-5">
              <div>
                <h2 className="display" style={{ fontSize: 24, color: '#fff' }}>{selectedBill.number} — {selectedBill.title}</h2>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-300">
                  <span><strong className="text-white">Jurisdiction:</strong> {selectedBill.state === 'US' ? 'Federal (US)' : selectedBill.state}</span>
                  <span><strong className="text-white">Status:</strong> {selectedBill.status}</span>
                  <span><strong className="text-white">Date:</strong> {selectedBill.last_action_date}</span>
                  {selectedBill.url && <a href={selectedBill.url} target="_blank" rel="noreferrer" className="text-violet-300 underline">View on LegiScan</a>}
                </div>
                {selectedBill.last_action && <p className="text-slate-400 mt-2 text-sm">{selectedBill.last_action}</p>}
              </div>

              {/* Sponsors — from billDetail (populated after summarize) */}
              {(() => {
                const sponsors = billDetail?.sponsors || billDetail?.bill?.sponsors || [];
                if (!sponsors.length) return null;
                const primary = sponsors.filter(s => s.sponsorship_type_id === 1 || s.type === 1);
                const cosponsors = sponsors.filter(s => s.sponsorship_type_id !== 1 && s.type !== 1);
                return (
                  <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-4 space-y-2 text-sm">
                    {primary.length > 0 && (
                      <p className="text-slate-300"><strong className="text-white">Sponsor{primary.length > 1 ? 's' : ''}:</strong> {primary.map(s => `${s.name}${s.party ? ` (${s.party})` : ''}`).join(', ')}</p>
                    )}
                    {cosponsors.length > 0 && (
                      <p className="text-slate-300"><strong className="text-white">Cosponsors ({cosponsors.length}):</strong> {cosponsors.map(s => `${s.name}${s.party ? ` (${s.party})` : ''}`).join(', ')}</p>
                    )}
                  </div>
                );
              })()}

              <div className="flex flex-wrap gap-3">
                <button
                  data-testid="submit-legislative-preview-summary"
                  onClick={() => {
                    setPendingSummaryLevel('preview');
                    runAction({ action: 'summarize', bill_id: String(selectedBill.bill_id), summary_level: 'preview' });
                    scrollToSelectedBill();
                  }}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm">
                  {loading && pendingSummaryLevel === 'preview' ? <><SpinnerGap size={16} className="animate-spin" /> Loading preview…</> : <>Quick Preview <ArrowRight size={16} /></>}
                </button>
                <button
                  data-testid="submit-legislative-detailed-summary"
                  onClick={() => {
                    setPendingSummaryLevel('detailed');
                    runAction({ action: 'summarize', bill_id: String(selectedBill.bill_id), summary_level: 'detailed' });
                    scrollToSelectedBill();
                  }}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-200 text-sm">
                  {loading && pendingSummaryLevel === 'detailed' ? <><SpinnerGap size={16} className="animate-spin" /> Scanning full text…</> : <>Detailed Summary <ArrowRight size={16} /></>}
                </button>
              </div>

              {(summaryStatus || billSummary || billCaveats.length > 0) && (
                <div className="space-y-4">
                  <div className="app-output-header !mb-0">Bill Summary</div>
                  {summaryStatus === 'preview_ready' && (
                    <div className="rounded-xl border border-sky-500/40 bg-sky-500/10 px-5 py-3 text-sky-200 text-sm">
                      Quick preview generated from bill metadata. Use Detailed Summary to scan the full text.
                    </div>
                  )}
                  {summaryStatus === 'verified' && (
                    <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-5 py-3 text-emerald-200 text-sm">
                      Verified source summary generated from official bill text.
                    </div>
                  )}
                  {summaryStatus === 'verified' && isLongBillSummary && (
                    <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-5 py-3 text-amber-200 text-sm">
                      This was generated from a long bill. Use the summary as a guide, but manually check the underlying text for section-specific details, exceptions, thresholds, and dates.
                    </div>
                  )}
                  {summaryStatus === 'blocked_missing_source' && (
                    <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-5 py-3 text-amber-200 text-sm">
                      Verified summary unavailable because the tool could not obtain complete usable bill text.
                    </div>
                  )}
                  {summaryStatus === 'blocked_verification' && (
                    <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-5 py-3 text-red-200 text-sm">
                      Verified summary unavailable because the generated lines could not be fully traced back to the bill text.
                    </div>
                  )}
                  {summaryStatus === 'failed_system' && (
                    <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-5 py-3 text-red-200 text-sm">
                      Summary generation failed due to a system or extraction error.
                    </div>
                  )}
                  {(sourceTextStatus || sourceStatus || extractionStatus || verificationStatus || extractionCoverage || evidenceCoverage) && (
                    <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-3 text-sm text-slate-300 flex flex-wrap gap-4">
                      {summaryLevel && <span><strong className="text-white">Summary Level:</strong> {summaryLevel}</span>}
                      {sourceTextStatus && <span><strong className="text-white">Text Coverage:</strong> {sourceTextStatus}</span>}
                      {sourceStatus && <span><strong className="text-white">Source Status:</strong> {sourceStatus.replaceAll('_', ' ')}</span>}
                      {extractionStatus && <span><strong className="text-white">Extraction Status:</strong> {extractionStatus.replaceAll('_', ' ')}</span>}
                      {verificationStatus && <span><strong className="text-white">Verification Status:</strong> {verificationStatus.replaceAll('_', ' ')}</span>}
                      {coverageMode && <span><strong className="text-white">Render Mode:</strong> {coverageMode.replaceAll('_', ' ')}</span>}
                      {extractionCoverage && <span><strong className="text-white">Extraction:</strong> {extractionCoverage.extracted_sections ?? 0}/{extractionCoverage.total_sections ?? 0} sections</span>}
                      {evidenceCoverage && <span><strong className="text-white">Evidence:</strong> {(evidenceCoverage.fact_count ?? evidenceCoverage.provision_count ?? 0)} fact(s), {(evidenceCoverage.parsed_chunks ?? 0)}/{(evidenceCoverage.total_chunks ?? 0)} chunk(s) parsed</span>}
                    </div>
                  )}
                  {validationFlags.length > 0 && (
                    <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-3 space-y-1">
                      <p className="text-slate-300 text-xs font-semibold uppercase tracking-wider mb-1">Validation Flags</p>
                      <div className="flex flex-wrap gap-2">
                        {validationFlags.map((flag) => (
                          <span key={flag} className="px-2 py-1 rounded-md border border-white/10 bg-white/5 text-slate-300 text-xs font-mono">
                            {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {unsupportedClaims.length > 0 && (
                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-3 space-y-1">
                      <p className="text-red-200 text-xs font-semibold uppercase tracking-wider mb-1">Unsupported Claims</p>
                      {unsupportedClaims.map((claim, i) => (
                        <p key={`${claim}-${i}`} className="text-red-100 text-sm">{claim}</p>
                      ))}
                    </div>
                  )}
                  {billCaveats.length > 0 && (
                    <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-5 py-3 space-y-1">
                      <p className="text-amber-300 text-xs font-semibold uppercase tracking-wider mb-1">Analysis Notes</p>
                      {billCaveats.map((c, i) => (
                        <p key={i} className="text-amber-200 text-sm">{c}</p>
                      ))}
                    </div>
                  )}
                  {(summaryStatus === 'verified' || summaryStatus === 'preview_ready') && billSummary && (
                    <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-5 py-4">
                      <StyledMarkdown>{billSummary}</StyledMarkdown>
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button
                      data-testid="download-legislative-summary"
                      onClick={() => downloadText(job?.result_data?.report_markdown || billSummary || '', summaryStatus === 'verified' ? 'verified_bill_summary.md' : summaryStatus === 'preview_ready' ? 'bill_preview.md' : 'summary_diagnostics.md')}
                      disabled={!job?.result_data?.report_markdown && !billSummary}
                      className="flex items-center justify-center gap-2 py-4 px-6 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors">
                      <DownloadSimple size={18} /> {summaryStatus === 'verified' ? 'Download Verified Summary' : summaryStatus === 'preview_ready' ? 'Download Preview' : 'Download Diagnostics'}
                    </button>
                    <button data-testid="download-legislative-bill-detail" onClick={() => downloadJson(billDetail || {}, 'bill_detail.json')}
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
        <div data-tour="legislative-tracker-watchlist-panel" className="space-y-8">
          <div className="glass-card p-8 flex flex-wrap gap-3">
            <button data-testid="submit-legislative-watchlist-list" disabled={loading} onClick={() => runAction({ action: 'watchlist_list' })}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed">Reload Watchlist</button>
            <button data-testid="submit-legislative-watchlist-refresh" disabled={loading} onClick={() => runAction({ action: 'watchlist_refresh' })}
              className="px-4 py-2 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 disabled:opacity-50 disabled:cursor-not-allowed">Refresh All</button>
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
                        <p className="text-slate-400 text-sm mt-1">{bill.state === 'US' ? 'Federal (US)' : bill.state} · {bill.status} · {bill.last_action_date}</p>
                        {bill.added_at && <p className="text-slate-500 text-xs mt-1">Tracked since {String(bill.added_at).slice(0, 10)}</p>}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button disabled={loading} onClick={() => { setSelectedBill(bill); setActiveTab('Search & Discover'); runAction({ action: 'summarize', bill_id: String(bill.bill_id), summary_level: 'preview' }); }}
                          className="px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-400/30 text-violet-200 text-sm disabled:opacity-50 disabled:cursor-not-allowed">Preview</button>
                        <button
                          disabled={loading}
                          onClick={() => runWatchlistAction({ action: 'watchlist_remove', bill_id: String(bill.bill_id) })}
                          className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {loading && watchlistBusyBillId === String(bill.bill_id) ? 'Removing…' : 'Remove'}
                        </button>
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
        Verified source summaries are limited to claims supported by official bill text and bill-record metadata. If the tool cannot maintain traceability, it will refuse to produce a normal summary.
      </p>
    </motion.div>
  );
}
