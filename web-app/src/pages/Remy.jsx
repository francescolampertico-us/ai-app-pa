import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperPlaneTiltIcon as PaperPlaneTilt, SpinnerGapIcon as SpinnerGap, ArrowSquareOutIcon as ArrowSquareOut, DownloadSimpleIcon as DownloadSimple, WarningIcon as Warning } from '@phosphor-icons/react';
import { API } from '../hooks/useFastApiJob';
import ResearchPrototypeNote from '../components/ResearchPrototypeNote';
import StyledMarkdown from '../components/StyledMarkdown';
import { Link } from 'react-router-dom';

const MotionDiv = motion.div;

function normalizeFrontendPath(route) {
  if (!route) return null;
  if (route.startsWith('/app')) return route;
  if (route.startsWith('/')) return `/app${route}`;
  return `/app/${route}`;
}

function ToolEvent({ event }) {
  const ok        = event.ok !== false;
  const label     = event.tool_id || 'tool';
  const route     = normalizeFrontendPath(event.frontend_path || null);
  const artifacts = event.artifacts || [];

  return (
    <details data-testid={`remy-tool-event-${label}`} className="mt-2 rounded-xl overflow-hidden border border-white/8" open={!ok}>
      <summary className="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none"
               style={{ background: ok ? 'rgba(74,222,128,0.06)' : 'rgba(248,113,113,0.06)' }}>
        <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-emerald-400' : 'bg-red-400'}`} />
        <span style={{ fontFamily: 'monospace', fontSize: 12, color: ok ? '#86efac' : '#fca5a5' }}>
          {label} · {ok ? 'completed' : 'failed'}
        </span>
      </summary>
      <div className="px-4 pb-4 pt-2 bg-black/20 flex flex-col gap-2">
        {route && (
          <Link data-testid={`remy-tool-event-open-${label}`} to={route} className="flex items-center gap-1.5 text-violet-400 hover:text-violet-300 transition-colors"
             style={{ fontFamily: 'Inter', fontSize: 12 }}>
            <ArrowSquareOut size={13} /> Open tool page
          </Link>
        )}
        {event.error && (
          <p style={{ fontFamily: 'monospace', fontSize: 11, color: '#fca5a5' }}>{event.error}</p>
        )}
        {artifacts.map((a, i) => (
          <a data-testid={`remy-tool-event-artifact-${label}-${i}`} key={i} href={`${API}${a.url || ''}`} download={a.name}
             className="flex items-center gap-2 px-3 py-2 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-300 hover:bg-violet-500/20 transition-colors"
             style={{ fontFamily: 'Inter', fontSize: 12, textDecoration: 'none' }}>
            <DownloadSimple size={14} /> {a.name}
          </a>
        ))}
      </div>
    </details>
  );
}

function Message({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-3`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full shrink-0 flex items-center justify-center mt-0.5"
             style={{ background: 'rgba(109,40,217,0.3)', border: '1px solid rgba(109,40,217,0.4)' }}>
          <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 13, color: '#A78BFA' }}>R</span>
        </div>
      )}
      <div className={`max-w-[75%] flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-2xl ${isUser
          ? 'bg-violet-600/25 border border-violet-500/30 text-white rounded-tr-sm'
          : 'bg-white/5 border border-white/8 text-zinc-200 rounded-tl-sm'
        }`} style={{ fontFamily: 'Inter', fontSize: 14, lineHeight: 1.65, fontWeight: 300 }}>
          {isUser ? msg.content : <StyledMarkdown>{msg.content}</StyledMarkdown>}
        </div>
        {(msg.tool_events || []).map((ev, i) => <ToolEvent key={i} event={ev} />)}
      </div>
    </motion.div>
  );
}

export default function Remy() {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: "Hi — I'm Remy. Tell me the objective and I'll route you to the right tool, collect any missing inputs, and run it when ready.\n\nTry: \"Run a background memo on NATO with sections: Overview, Leadership, U.S. Relations, Policy Positions.\"",
    tool_events: [],
  }]);
  const [input, setInput]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [model, setModel]     = useState('ChangeAgent');
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    setError(null);

    const userMsg = { role: 'user', content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setLoading(true);

    const history = updated.slice(0, -1).map(m => ({ role: m.role, content: m.content }));

    try {
      const res  = await fetch(`${API}/api/remy/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history, model }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.text || '(no response)',
        tool_events: data.tool_events || [],
      }]);
    } catch {
      setError('Could not reach the Remy backend. Make sure the API server is running at localhost:8000.');
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <MotionDiv data-testid="tool-page-remy" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="flex flex-col h-full max-h-[100dvh]" style={{ height: 'calc(100dvh - 0px)' }}>

      {/* Header */}
      <div className="shrink-0 px-8 pt-8 pb-4 border-b border-white/5">
        <h1 data-testid="page-title-remy" className="app-page-title">Remy</h1>
        <div className="flex items-center gap-3 mt-2">
          <p className="app-page-intro">
            Tool-aware PA assistant that routes work, collects inputs, and executes toolkit tools.
          </p>
        </div>
      </div>

      <div className="px-8 pt-6">
        <ResearchPrototypeNote
          category="Strategic Planning & Decision Support"
          secondaryLabel="Secondary Orchestration Layer"
          refs={['bitonti2023', 'digiacomo2025', 'buhmann2025']}
          message="Remy routes work across the toolkit and helps users move through the prototype, but it is not the core research claim of the project. The primary contribution remains the module-based system and the workflow logic beneath it."
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 flex flex-col gap-5">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        </AnimatePresence>
        {loading && (
          <MotionDiv initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 items-center">
            <div className="w-7 h-7 rounded-full shrink-0 flex items-center justify-center"
                 style={{ background: 'rgba(109,40,217,0.3)', border: '1px solid rgba(109,40,217,0.4)' }}>
              <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 13, color: '#A78BFA' }}>R</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-tl-sm bg-white/5 border border-white/8">
              <SpinnerGap size={14} className="animate-spin text-violet-400" />
              <span style={{ fontFamily: 'Inter', fontSize: 13, color: '#71717A' }}>Remy is working…</span>
            </div>
          </MotionDiv>
        )}
        {error && (
          <div className="flex items-start gap-2 px-4 py-3 rounded-xl bg-red-500/8 border border-red-500/20">
            <Warning size={16} className="text-red-400 shrink-0 mt-0.5" />
            <p style={{ fontFamily: 'Inter', fontSize: 13, color: '#fca5a5' }}>{error}</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 px-8 py-5 border-t border-white/5">
        <div className="flex gap-3 items-end">
          <textarea
            data-testid="input-remy-message"
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Tell Remy the objective…"
            rows={2}
            disabled={loading}
            className="field flex-1 resize-none"
            style={{ fontFamily: 'Inter', fontSize: 14, lineHeight: 1.5 }}
          />
          <button data-testid="submit-remy" onClick={send} disabled={loading || !input.trim()}
            aria-label="Send message"
            className="shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all disabled:opacity-40"
            style={{ background: '#6D28D9', boxShadow: '0 0 20px rgba(109,40,217,0.4)' }}>
            <PaperPlaneTilt size={18} weight="fill" className="text-white" />
          </button>
        </div>
        <p style={{ fontFamily: 'Inter', fontSize: 11, color: '#3F3F46', marginTop: 6 }}>
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </MotionDiv>
  );
}
