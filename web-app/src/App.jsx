import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import { API } from './hooks/useFastApiJob';
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
import ResearchLanding from './research/ResearchLanding';

const TOOL_UI = {
  media_clips: {
    label: 'Media Clips',
    desc: 'Daily Google News monitoring with boolean queries.',
    category: 'Policy Monitoring & Legislative Tracking',
    path: '/app/media-clips',
    section: 'intelligence',
  },
  legislative_tracker: {
    label: 'Legislative Tracker',
    desc: 'Real-time federal and state bill tracking via LegiScan.',
    category: 'Policy Monitoring & Legislative Tracking',
    path: '/app/legislative',
    section: 'intelligence',
  },
  influence_disclosure_tracker: {
    label: 'Influence Tracker',
    desc: 'LDA, FARA, and IRS 990 disclosure records normalized.',
    category: 'Policy Monitoring & Legislative Tracking',
    path: '/app/influence',
    section: 'intelligence',
  },
  background_memo_generator: {
    label: 'Background Memo',
    desc: 'Generates a first-draft background briefing on an issue, organization, or individual.',
    category: 'Policy Monitoring & Legislative Tracking',
    path: '/app/background-memo',
    section: 'intelligence',
  },
  hearing_memo_generator: {
    label: 'Hearing Memo',
    desc: 'Generates a first-draft hearing preparation memo from transcripts and source material.',
    category: 'Policy Monitoring & Legislative Tracking',
    path: '/app/memos',
    section: 'intelligence',
  },
  stakeholder_map: {
    label: 'Stakeholder Map',
    desc: 'Policy actor discovery and network graph across LDA + press.',
    category: 'Stakeholder Mapping & Network Analysis',
    path: '/app/stakeholders',
    section: 'stakeholder',
  },
  stakeholder_briefing: {
    label: 'Stakeholder Briefing',
    desc: 'Targeted briefing ahead of a meeting or hearing appearance.',
    category: 'Stakeholder Mapping & Network Analysis',
    path: '/app/stakeholder-briefing',
    section: 'stakeholder',
  },
  media_list_builder: {
    label: 'Media List',
    desc: 'Journalist discovery by beat, region, and outlet type.',
    category: 'Stakeholder Mapping & Network Analysis',
    path: '/app/media-list',
    section: 'stakeholder',
  },
  messaging_matrix: {
    label: 'Messaging Deliverables',
    desc: 'Builds reusable advocacy message outputs and draft-ready deliverables from a core position.',
    category: 'Content Generation & Drafting Support',
    path: '/app/messaging',
    section: 'output',
  },
};

const WORKFLOW_SECTIONS = [
  {
    id: 'intelligence',
    title: 'Intelligence Gathering',
    description: 'Monitoring, tracking, and briefing inputs that build the factual base for later strategic work.',
    toolIds: [
      'media_clips',
      'legislative_tracker',
      'influence_disclosure_tracker',
      'background_memo_generator',
      'hearing_memo_generator',
    ],
  },
  {
    id: 'stakeholder',
    title: 'Stakeholder and Contact Preparation',
    description: 'Tools that organize actors, map relationships, and prepare the outreach surface around an issue.',
    toolIds: [
      'stakeholder_map',
      'stakeholder_briefing',
      'media_list_builder',
    ],
  },
  {
    id: 'output',
    title: 'Output Creation',
    description: 'Where structured intelligence becomes reusable message outputs, positioning, and draft-ready advocacy materials.',
    toolIds: ['messaging_matrix'],
  },
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

function ToolCard({ ui, index }) {
  return (
    <Link
      key={ui.path}
      to={ui.path}
      className="glass group flex flex-col gap-3 p-6 transition-all hover:border-violet-500/30"
      style={{ textDecoration: 'none' }}
    >
      <div className="flex flex-wrap gap-2">
        <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 600, letterSpacing: '1.4px', textTransform: 'uppercase', color: '#c4b5fd', padding: '5px 8px', borderRadius: 999, background: 'rgba(109,40,217,0.16)', border: '1px solid rgba(109,40,217,0.26)' }}>
          {ui.category}
        </span>
        <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 600, letterSpacing: '1.4px', textTransform: 'uppercase', color: '#e4e4e7', padding: '5px 8px', borderRadius: 999, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
          Review Required
        </span>
      </div>
      <div className="flex items-start justify-between">
        <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 17, color: '#fff', lineHeight: 1.2 }}>
          {ui.label}
        </span>
        <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 700, letterSpacing: '1.5px', color: 'rgba(167,139,250,0.4)', textTransform: 'uppercase', marginTop: 3 }}>
          {String(index + 1).padStart(2, '0')}
        </span>
      </div>
      <p style={{ fontFamily: 'Inter', fontSize: 12.5, color: '#71717A', lineHeight: 1.6, fontWeight: 300 }}>
        {ui.desc}
      </p>
      <div className="section-rule mt-auto opacity-0 group-hover:opacity-100 transition-opacity" style={{ width: 32 }} />
    </Link>
  );
}

function Dashboard() {
  const [tools, setTools] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/tools`)
      .then((r) => r.json())
      .then((data) => setTools(data.filter((tool) => tool.frontend_path)))
      .catch(() => setTools([]));
  }, []);

  const toolLookup = {};
  for (const tool of tools || []) {
    toolLookup[tool.id] = tool;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="p-12 max-w-7xl mx-auto relative z-10"
    >
      <div
        className="absolute top-0 right-1/4 w-[600px] h-[400px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(109,40,217,0.12) 0%, transparent 70%)' }}
      />

      <div className="mb-16 mt-8">
        <div className="mb-6">
          <Wordmark />
        </div>
        <p className="text-zinc-500 text-base font-light leading-relaxed max-w-[60ch]">
          A research-informed system for bounded AI augmentation in Public Affairs.
          <br />
          Organized around intelligence gathering, stakeholder preparation, strategic synthesis, output creation, and human review.
        </p>
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-[1.35fr_1fr] gap-4">
          <div className="glass p-5">
            <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '1.8px', textTransform: 'uppercase', color: 'rgba(167,139,250,0.55)', marginBottom: 10 }}>
              Strategic Planning & Decision Support
            </div>
            <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#a1a1aa', lineHeight: 1.7, fontWeight: 300 }}>
              Research prototype for bounded AI augmentation in Public Affairs. Outputs require professional review before external use.
            </p>
          </div>
          <div className="glass p-5">
            <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '1.8px', textTransform: 'uppercase', color: 'rgba(167,139,250,0.55)', marginBottom: 10 }}>
              Tailored Workflow
            </div>
            <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#a1a1aa', lineHeight: 1.7, fontWeight: 300 }}>
              Built from applied research, coursework, notes, writing practice, and project-specific reference materials developed during the capstone. Remy remains a secondary orchestration layer.
            </p>
          </div>
        </div>
      </div>

      {tools === null && (
        <div className="text-slate-600 text-sm">Loading tools…</div>
      )}

      <div className="flex flex-col gap-10">
        {WORKFLOW_SECTIONS.map((section) => {
          const sectionTools = section.toolIds
            .map((id) => (toolLookup[id] && TOOL_UI[id] ? { ...TOOL_UI[id], id } : null))
            .filter(Boolean);

          if (!sectionTools.length) return null;

          return (
            <section key={section.id} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '1.8px', textTransform: 'uppercase', color: 'rgba(167,139,250,0.55)' }}>
                  {section.title}
                </div>
                <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#71717A', lineHeight: 1.7, fontWeight: 300, maxWidth: '72ch' }}>
                  {section.description}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {sectionTools.map((ui, index) => (
                  <ToolCard key={ui.id} ui={ui} index={index} />
                ))}
              </div>
            </section>
          );
        })}

        <section className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '1.8px', textTransform: 'uppercase', color: 'rgba(167,139,250,0.55)' }}>
              Strategic Support
            </div>
            <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#71717A', lineHeight: 1.7, fontWeight: 300, maxWidth: '72ch' }}>
              A secondary orchestration layer that helps users move across the toolkit without replacing the underlying module-based workflow.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <Link
              to="/app/remy"
              className="glass group flex flex-col gap-3 p-6 transition-all hover:border-violet-500/30"
              style={{ textDecoration: 'none' }}
            >
              <div className="flex flex-wrap gap-2">
                <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 600, letterSpacing: '1.4px', textTransform: 'uppercase', color: '#c4b5fd', padding: '5px 8px', borderRadius: 999, background: 'rgba(109,40,217,0.16)', border: '1px solid rgba(109,40,217,0.26)' }}>
                  Strategic Planning & Decision Support
                </span>
                <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 600, letterSpacing: '1.4px', textTransform: 'uppercase', color: '#e4e4e7', padding: '5px 8px', borderRadius: 999, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                  Secondary Orchestration Layer
                </span>
              </div>
              <div className="flex items-start justify-between">
                <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 17, color: '#fff', lineHeight: 1.2 }}>
                  Remy
                </span>
                <span style={{ fontFamily: 'Inter', fontSize: 9, fontWeight: 700, letterSpacing: '1.5px', color: 'rgba(167,139,250,0.4)', textTransform: 'uppercase', marginTop: 3 }}>
                  01
                </span>
              </div>
              <p style={{ fontFamily: 'Inter', fontSize: 12.5, color: '#71717A', lineHeight: 1.6, fontWeight: 300 }}>
                Routes work across the prototype and helps users select the right tool for a given objective.
              </p>
              <div className="section-rule mt-auto opacity-0 group-hover:opacity-100 transition-opacity" style={{ width: 32 }} />
            </Link>
          </div>
        </section>
      </div>

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

function AppLayout() {
  useEffect(() => {
    try {
      window.localStorage.setItem('strategitect_dashboard_visited', '1');
    } catch {
      // ignore storage errors
    }
  }, []);

  return (
    <div className="flex min-h-[100dvh] w-full text-white overflow-hidden" style={{ background: '#09090B' }}>
      <Sidebar />
      <main className="flex-1 overflow-y-auto relative flex flex-col">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse at top right, rgba(109,40,217,0.07) 0%, transparent 60%)' }}
        />
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ResearchLanding />} />

        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="media-clips" element={<MediaClips />} />
          <Route path="legislative" element={<LegislativeTracker />} />
          <Route path="stakeholders" element={<StakeholderMap />} />
          <Route path="memos" element={<HearingMemo />} />
          <Route path="influence" element={<InfluenceTracker />} />
          <Route path="messaging" element={<MessagingMatrix />} />
          <Route path="background-memo" element={<BackgroundMemo />} />
          <Route path="stakeholder-briefing" element={<StakeholderBriefing />} />
          <Route path="media-list" element={<MediaListBuilder />} />
          <Route path="remy" element={<Remy />} />
        </Route>

        <Route path="/media-clips" element={<Navigate to="/app/media-clips" replace />} />
        <Route path="/legislative" element={<Navigate to="/app/legislative" replace />} />
        <Route path="/stakeholders" element={<Navigate to="/app/stakeholders" replace />} />
        <Route path="/memos" element={<Navigate to="/app/memos" replace />} />
        <Route path="/influence" element={<Navigate to="/app/influence" replace />} />
        <Route path="/messaging" element={<Navigate to="/app/messaging" replace />} />
        <Route path="/background-memo" element={<Navigate to="/app/background-memo" replace />} />
        <Route path="/stakeholder-briefing" element={<Navigate to="/app/stakeholder-briefing" replace />} />
        <Route path="/media-list" element={<Navigate to="/app/media-list" replace />} />
        <Route path="/remy" element={<Navigate to="/app/remy" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
