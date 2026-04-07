import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
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

const NAV = [
  { icon: SquaresFour,       label: "Dashboard",          path: "/" },
  { icon: NewspaperClipping, label: "Media Clips",         path: "/media-clips" },
  { icon: Gavel,             label: "Legislation",         path: "/legislative" },
  { icon: MagnifyingGlass,   label: "Influence Tracker",   path: "/influence" },
  { icon: Users,             label: "Stakeholder Map",     path: "/stakeholders" },
  { icon: Files,             label: "Hearing Memos",       path: "/memos" },
  { icon: Lighthouse,        label: "Messaging Matrix",    path: "/messaging" },
  { icon: Notebook,          label: "Background Memo",     path: "/background-memo" },
  { icon: AddressBook,       label: "Stakeholder Brief",   path: "/stakeholder-briefing" },
  { icon: TreeStructure,     label: "Media List Builder",  path: "/media-list" },
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

  return (
    <div className="w-16 md:w-60 border-r border-white/5 flex flex-col justify-between py-8 px-3 z-50 shrink-0 backdrop-blur-xl bg-[#09090B]/90">
      <div className="flex flex-col gap-8">
        {/* Wordmark */}
        <div className="px-1 hidden md:block">
          <Wordmark collapsed={false} />
        </div>
        <div className="px-1 block md:hidden">
          <Wordmark collapsed={true} />
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                  isActive
                    ? 'text-white'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/4'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeSideTab"
                    className="absolute inset-0 rounded-xl"
                    style={{ background: 'rgba(109,40,217,0.15)', border: '1px solid rgba(109,40,217,0.25)' }}
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon
                  size={18}
                  weight={isActive ? "fill" : "regular"}
                  className={`relative z-10 shrink-0 ${isActive ? 'text-violet-400' : ''}`}
                />
                <span className="hidden md:block relative z-10 text-sm font-medium tracking-wide">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Remy */}
      <div className="px-1">
        <Link to="/remy" className={`flex w-full items-center gap-3 px-3 py-3 rounded-xl transition-all border ${
          currentPath === '/remy'
            ? 'text-white border-violet-500/30 bg-violet-500/10'
            : 'text-zinc-400 hover:text-white border-white/5 hover:border-violet-500/20 hover:bg-violet-500/8'
        }`} style={{ textDecoration: 'none' }}>
          <ChatCircle size={18} className="shrink-0 text-violet-400" weight="fill" />
          <span className="hidden md:block text-sm font-medium tracking-wide">Ask Remy</span>
        </Link>
      </div>
    </div>
  );
}
