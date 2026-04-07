import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion } from 'framer-motion';
import Sidebar from './components/layout/Sidebar';
import HearingMemo from './pages/HearingMemo';
import MediaClips from './pages/MediaClips';
import LegislativeTracker from './pages/LegislativeTracker';
import StakeholderMap from './pages/StakeholderMap';
import InfluenceTracker from './pages/InfluenceTracker';
import MessagingMatrix from './pages/MessagingMatrix';
import BackgroundMemo from './pages/BackgroundMemo';
import StakeholderBriefing from './pages/StakeholderBriefing';
import MediaListBuilder from './pages/MediaListBuilder';
import Remy from './pages/Remy';

const TOOLS = [
  { label: 'Media Clips',          desc: 'Daily Google News monitoring with boolean queries.',                path: '/media-clips' },
  { label: 'Legislative Tracker',  desc: 'Real-time federal and state bill tracking via LegiScan.',          path: '/legislative' },
  { label: 'Influence Tracker',    desc: 'LDA, FARA, and IRS 990 disclosure records normalized.',            path: '/influence' },
  { label: 'Stakeholder Map',      desc: 'Policy actor discovery and network graph across LDA + press.',      path: '/stakeholders' },
  { label: 'Hearing Memo',         desc: 'Congressional transcript → structured house-style memo.',           path: '/memos' },
  { label: 'Messaging Matrix',     desc: 'Message House + talking points + press statement + social.',       path: '/messaging' },
  { label: 'Background Memo',      desc: 'Deep-dive research pipeline into individuals and organizations.',   path: '/background-memo' },
  { label: 'Stakeholder Brief',    desc: 'Targeted briefing ahead of a meeting or hearing appearance.',       path: '/stakeholder-briefing' },
  { label: 'Media List Builder',   desc: 'Journalist discovery by beat, region, and outlet type.',           path: '/media-list' },
];

function Wordmark() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 28, color: '#fff', lineHeight: 1.05, letterSpacing: '-0.01em' }}>
        Str<span style={{ color: '#A78BFA' }}>α</span>tegitect
      </span>
      <div style={{ height: 1.5, width: 52, background: '#A78BFA', margin: '6px 0 5px' }} />
      <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 8, fontWeight: 500, letterSpacing: '0.9px', textTransform: 'uppercase', color: 'rgba(167,139,250,0.55)' }}>
        Architecture for Public Affairs Strategy
      </span>
    </div>
  );
}

function Dashboard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="p-12 max-w-7xl mx-auto relative z-10"
    >
      {/* Glow */}
      <div className="absolute top-0 right-1/4 w-[600px] h-[400px] rounded-full pointer-events-none"
           style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.12) 0%, transparent 70%)' }} />

      {/* Header */}
      <div className="mb-16 mt-8">
        <div className="mb-6">
          <Wordmark />
        </div>
        <p className="text-zinc-500 text-base font-light leading-relaxed max-w-[55ch]">
          A precision intelligence toolkit for public affairs professionals.<br/>
          Ten tools. One pipeline. Zero fabrication.
        </p>
      </div>

      {/* Tool grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {TOOLS.map((tool, i) => (
          <a key={tool.path} href={tool.path}
             className="glass group flex flex-col gap-3 p-6 transition-all hover:border-violet-500/30"
             style={{ textDecoration: 'none' }}>
            <div className="flex items-start justify-between">
              <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 17, color: '#fff', lineHeight: 1.2 }}>
                {tool.label}
              </span>
              <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 700, letterSpacing: '1.5px', color: 'rgba(167,139,250,0.4)', textTransform: 'uppercase', marginTop: 3 }}>
                {String(i + 1).padStart(2, '0')}
              </span>
            </div>
            <p style={{ fontFamily: 'Inter', fontSize: 12.5, color: '#71717A', lineHeight: 1.6, fontWeight: 300 }}>
              {tool.desc}
            </p>
            <div className="section-rule mt-auto opacity-0 group-hover:opacity-100 transition-opacity" style={{ width: 32 }} />
          </a>
        ))}
      </div>

      {/* Footer mark */}
      <div className="mt-20 pt-8 border-t border-white/5 flex items-center gap-3">
        <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 13, color: 'rgba(255,255,255,0.2)' }}>
          Str<span style={{ color: 'rgba(167,139,250,0.4)' }}>α</span>tegitect
        </span>
        <span style={{ fontFamily: 'Inter', fontSize: 9, color: 'rgba(255,255,255,0.12)', letterSpacing: '1px', textTransform: 'uppercase', fontWeight: 500 }}>
          Architecture for Public Affairs Strategy
        </span>
      </div>
    </motion.div>
  );
}

export default function App() {
  return (
    <Router>
      <div className="flex min-h-[100dvh] w-full text-white overflow-hidden" style={{ background: '#09090B' }}>
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative flex flex-col">
          <div className="absolute inset-0 pointer-events-none"
               style={{ background: 'radial-gradient(ellipse at top right, rgba(109,40,217,0.07) 0%, transparent 60%)' }} />
          <Routes>
            <Route path="/"                     element={<Dashboard />} />
            <Route path="/media-clips"          element={<MediaClips />} />
            <Route path="/legislative"          element={<LegislativeTracker />} />
            <Route path="/stakeholders"         element={<StakeholderMap />} />
            <Route path="/memos"                element={<HearingMemo />} />
            <Route path="/influence"            element={<InfluenceTracker />} />
            <Route path="/messaging"            element={<MessagingMatrix />} />
            <Route path="/background-memo"      element={<BackgroundMemo />} />
            <Route path="/stakeholder-briefing" element={<StakeholderBriefing />} />
            <Route path="/media-list"           element={<MediaListBuilder />} />
            <Route path="/remy"                 element={<Remy />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
