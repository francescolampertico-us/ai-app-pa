import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon as ArrowLeft,
  SquaresFourIcon as SquaresFour,
  FilesIcon as Files,
  UsersIcon as Users,
  GavelIcon as Gavel,
  NewspaperClippingIcon as NewspaperClipping,
  MagnifyingGlassIcon as MagnifyingGlass,
  LighthouseIcon as Lighthouse,
  NotebookIcon as Notebook,
  AddressBookIcon as AddressBook,
  TreeStructureIcon as TreeStructure,
  ChatCircleIcon as ChatCircle,
} from '@phosphor-icons/react';

const DASHBOARD_ITEM = { icon: SquaresFour, label: 'Dashboard', path: '/app' };

const NAV_SECTIONS = [
  {
    title: 'Intelligence Gathering',
    items: [
      { icon: NewspaperClipping, label: 'Media Clips', path: '/app/media-clips' },
      { icon: Gavel, label: 'Legislative Tracker', path: '/app/legislative' },
      { icon: MagnifyingGlass, label: 'Influence Tracker', path: '/app/influence' },
      { icon: Notebook, label: 'Background Memo', path: '/app/background-memo' },
      { icon: Files, label: 'Hearing Memo', path: '/app/memos' },
    ],
  },
  {
    title: 'Stakeholder and Contact Preparation',
    items: [
      { icon: Users, label: 'Stakeholder Map', path: '/app/stakeholders' },
      { icon: AddressBook, label: 'Stakeholder Briefing', path: '/app/stakeholder-briefing' },
      { icon: TreeStructure, label: 'Media List', path: '/app/media-list' },
    ],
  },
  {
    title: 'Output Creation',
    items: [
      { icon: Lighthouse, label: 'Messaging Deliverables', path: '/app/messaging' },
    ],
  },
  {
    title: 'Strategic Support',
    items: [
      { icon: ChatCircle, label: 'Ask Remy', path: '/app/remy', accent: true },
    ],
  },
];

function Wordmark({ collapsed }) {
  if (collapsed) {
    return (
      <div className="flex items-center justify-center w-10 h-10">
        <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: '#fff', lineHeight: 1 }}>
          Str<span style={{ color: '#A78BFA' }}>α</span>
        </span>
      </div>
    );
  }
  return (
    <div className="flex flex-col px-2">
      <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: '#fff', lineHeight: 1.1, letterSpacing: '-0.01em' }}>
        Str<span style={{ color: '#A78BFA' }}>α</span>tegitect
      </span>
      <div style={{ height: 1.5, width: 44, background: '#A78BFA', margin: '5px 0 4px' }} />
      <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 7, fontWeight: 500, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'rgba(167,139,250,0.55)' }}>
        Architecture for PA Strategy
      </span>
    </div>
  );
}

export default function Sidebar() {
  const location = useLocation();
  const currentPath = location.pathname;

  const renderNavItem = (item) => {
    const Icon = item.icon;
    const isActive = currentPath === item.path;

    return (
      <Link
        key={item.path}
        to={item.path}
        className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
          isActive
            ? 'text-white'
            : item.accent
              ? 'text-zinc-300 hover:text-white hover:bg-violet-500/10'
              : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/4'
        }`}
      >
        {isActive && (
          <motion.div
            layoutId="activeSideTab"
            className="absolute inset-0 rounded-xl"
            style={{ background: item.accent ? 'rgba(109,40,217,0.18)' : 'rgba(109,40,217,0.15)', border: '1px solid rgba(109,40,217,0.25)' }}
            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
          />
        )}
        <Icon
          size={18}
          weight={isActive || item.accent ? 'fill' : 'regular'}
          className={`relative z-10 shrink-0 ${isActive || item.accent ? 'text-violet-400' : ''}`}
        />
        <span className="hidden md:block relative z-10 text-sm font-medium tracking-wide">
          {item.label}
        </span>
      </Link>
    );
  };

  return (
    <div className="w-16 md:w-72 border-r border-white/5 flex flex-col py-8 px-3 z-50 shrink-0 backdrop-blur-xl bg-[#09090B]/90">
      <div className="flex flex-col gap-6 min-h-0 flex-1 overflow-y-auto pr-1">
        {/* Wordmark */}
        <div className="px-1 hidden md:block">
          <Wordmark collapsed={false} />
        </div>
        <div className="px-1 block md:hidden">
          <Wordmark collapsed={true} />
        </div>

        <Link
          to="/"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-white/8 text-zinc-300 hover:text-white hover:border-violet-500/25 hover:bg-violet-500/8 transition-all"
          style={{ textDecoration: 'none' }}
        >
          <ArrowLeft size={18} className="shrink-0 text-violet-400" />
          <span className="hidden md:block text-sm font-medium tracking-wide">Back to Research</span>
        </Link>

        <nav className="flex flex-col gap-5">
          <div className="flex flex-col gap-1">
            {renderNavItem(DASHBOARD_ITEM)}
          </div>

          {NAV_SECTIONS.map((section) => (
            <div key={section.title} className="flex flex-col gap-1.5">
              <div className="hidden md:block px-3 pt-1 pb-1">
                <div style={{ fontFamily: 'Inter', fontSize: 10, fontWeight: 600, letterSpacing: '1.8px', textTransform: 'uppercase', color: 'rgba(161,161,170,0.55)' }}>
                  {section.title}
                </div>
              </div>
              <div className="flex flex-col gap-1">
                {section.items.map(renderNavItem)}
              </div>
            </div>
          ))}
        </nav>
      </div>
    </div>
  );
}
