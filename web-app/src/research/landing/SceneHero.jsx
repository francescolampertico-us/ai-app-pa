import { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, X } from 'lucide-react';
import CitationButton from './CitationButton';

const DEFINITIONS = {
  genai: {
    term: 'Generative AI',
    short: 'AI that creates its own content (images or text) based on patterns in large training data sets.',
    context: 'It differs from discriminative AI, which uses data to make predictions or categorize content.',
    refs: ['felten2023'],
  },
  pa: {
    term: 'Public Affairs',
    short: 'The strategic coordination of activities through which organizations manage institutional and stakeholder relations to influence public decisions.',
    context:
      'Lobbying and Government Relations are subdomains of Public Affairs but can be used interchangeably. Public Relations and Corporate Communication are related but distinct fields.',
    refs: ['digiacomo2025'],
  },
};

function AccentTerm({ id, onOpen, children }) {
  return (
    <button
      onClick={() => onOpen((current) => (current === id ? null : id))}
      style={{
        background: 'transparent',
        border: 0,
        padding: 0,
        color: 'var(--text-accent)',
        borderBottom: '1px solid rgba(167, 139, 250, 0.38)',
        font: 'inherit',
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  );
}

export default function SceneHero({ appPath = '/app' }) {
  const [titleState, setTitleState] = useState(0);
  const [activeDef, setActiveDef] = useState(null);
  const [hasVisitedApp, setHasVisitedApp] = useState(false);
  const [definitionStyle, setDefinitionStyle] = useState(null);
  const contentRef = useRef(null);
  const definition = useMemo(() => (activeDef ? DEFINITIONS[activeDef] : null), [activeDef]);

  useEffect(() => {
    try {
      setHasVisitedApp(window.localStorage.getItem('strategitect_dashboard_visited') === '1');
    } catch {
      setHasVisitedApp(false);
    }

    const t1 = setTimeout(() => setTitleState(1), 500);
    const t2 = setTimeout(() => setTitleState(2), 1600);
    const t3 = setTimeout(() => setTitleState(3), 2400);
    const t4 = setTimeout(() => setTitleState(4), 4200);
    const t5 = setTimeout(() => setTitleState(5), 5800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
    };
  }, []);

  useEffect(() => {
    if (!definition || !contentRef.current || typeof window === 'undefined') return;

    const updatePosition = () => {
      const rect = contentRef.current.getBoundingClientRect();
      const width = Math.min(540, window.innerWidth - 32);
      const left = Math.max(16, Math.min(rect.left + (rect.width - width) / 2, window.innerWidth - width - 16));
      const top = Math.min(rect.bottom + 48, window.innerHeight - 360);

      setDefinitionStyle({ top, left, width });
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    return () => window.removeEventListener('resize', updatePosition);
  }, [definition]);

  return (
    <section className="scene hero-scene" id="scene-hero" style={{ minHeight: '100vh', position: 'relative' }}>
      <motion.div
        style={{
          position: 'fixed',
          zIndex: 1000,
          pointerEvents: titleState >= 5 ? 'auto' : 'none',
          transformOrigin: '0 0',
          fontFamily: 'var(--font-serif)',
          fontSize: '5rem',
          letterSpacing: '-1.12px',
          lineHeight: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          whiteSpace: 'nowrap',
        }}
        initial={{ top: '45%', left: 'calc(50% + var(--nav-width) / 2)', x: '-50%', y: '-50%' }}
        animate={{
          top: titleState >= 4 ? '1.6rem' : '45%',
          left: titleState >= 4 ? '1rem' : 'calc(50% + var(--nav-width) / 2)',
          x: titleState >= 4 ? 0 : '-50%',
          y: titleState >= 4 ? 0 : '-50%',
          scale: titleState >= 4 ? 0.28 : 1,
        }}
        transition={{ duration: 1.6, ease: [0.645, 0.045, 0.355, 1] }}
      >
        <AnimatePresence>
          {titleState < 5 && (
            <motion.div
              key="morph"
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.9 }}
              style={{ display: 'flex', alignItems: 'center', whiteSpace: 'nowrap' }}
              animate={{ color: titleState >= 4 ? '#ffffff' : 'var(--text-accent)' }}
            >
              <motion.span
                animate={{
                  width: titleState >= 1 ? 0 : 'auto',
                  opacity: titleState >= 1 ? 0 : 1,
                  paddingRight: titleState >= 1 ? 0 : '0.4em',
                }}
                style={{ overflow: 'hidden', display: 'inline-flex', whiteSpace: 'nowrap' }}
                transition={{ duration: 0.6, ease: 'easeInOut' }}
              >
                The
              </motion.span>

              <motion.div
                style={{ display: 'flex', position: 'relative' }}
                animate={{ x: titleState >= 2 ? '3.08em' : 0, paddingRight: titleState >= 3 ? 0 : '0.4em' }}
                transition={{ duration: 2.2, ease: [0.23, 1, 0.32, 1] }}
              >
                <motion.span
                  animate={{ width: titleState >= 3 ? 0 : 'auto', opacity: titleState >= 3 ? 0 : 1 }}
                  style={{ display: 'inline-flex', overflow: 'hidden', whiteSpace: 'nowrap' }}
                  transition={{ duration: 1.4, ease: 'easeInOut' }}
                >
                  Arch
                </motion.span>
                <span>itect</span>
                <motion.span
                  animate={{ width: titleState >= 3 ? 0 : 'auto', opacity: titleState >= 3 ? 0 : 1 }}
                  style={{ display: 'inline-flex', overflow: 'hidden', whiteSpace: 'nowrap' }}
                  transition={{ duration: 1.4, ease: 'easeInOut' }}
                >
                  ure
                </motion.span>
              </motion.div>

              <motion.span
                animate={{
                  width: titleState >= 1 ? 0 : 'auto',
                  opacity: titleState >= 1 ? 0 : 1,
                  paddingRight: titleState >= 1 ? 0 : '0.4em',
                }}
                style={{ overflow: 'hidden', display: 'inline-flex', whiteSpace: 'nowrap' }}
                transition={{ duration: 0.6, ease: 'easeInOut' }}
              >
                of
              </motion.span>

              <motion.div
                style={{ display: 'flex', position: 'relative' }}
                animate={{ x: titleState >= 2 ? '-1.85em' : 0 }}
                transition={{ duration: 1.4, ease: [0.23, 1, 0.32, 1] }}
              >
                <span>Strateg</span>
                <motion.span
                  animate={{ width: titleState >= 3 ? 0 : 'auto', opacity: titleState >= 3 ? 0 : 1 }}
                  style={{ display: 'inline-flex', overflow: 'hidden', whiteSpace: 'nowrap' }}
                  transition={{ duration: 1.4, ease: 'easeInOut' }}
                >
                  y
                </motion.span>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {titleState >= 5 && (
            <motion.div
              key="logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1 }}
              style={{ position: 'absolute', top: 0, left: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}
            >
              <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'stretch' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', whiteSpace: 'nowrap', letterSpacing: '-1.12px' }}>
                  <span style={{ color: '#fff' }}>Str</span>
                  <span style={{ color: 'var(--text-accent)', fontStyle: 'italic', fontSize: '1.05em' }}>α</span>
                  <span style={{ color: '#fff' }}>tegitect</span>
                </div>
                <div style={{ height: '4px', background: 'var(--text-accent)', borderRadius: '2px', marginTop: '0.25em', marginBottom: '0.4em' }} />
              </div>
              <div
                style={{
                  fontSize: '0.3em',
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  color: 'var(--text-accent)',
                  fontWeight: 500,
                  fontFamily: 'var(--font-sans)',
                }}
              >
                Architecture for Public Affairs Strategy
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {titleState >= 5 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              top: '45%',
              left: 0,
              right: 0,
              margin: '0 auto',
              zIndex: 10,
              fontFamily: 'var(--font-serif)',
              fontSize: '4.85rem',
              letterSpacing: '-1.12px',
              width: 'min(1200px, calc(100vw - 6rem))',
              textAlign: 'center',
              lineHeight: 1.08,
              pointerEvents: 'none',
            }}
          >
            <span className="text-gradient">The Architecture of Strategy</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div
        ref={contentRef}
        className="fade-in-up"
        style={{
          position: 'absolute',
          top: '63%',
          left: 0,
          right: 0,
          margin: '0 auto',
          textAlign: 'center',
          width: '100%',
          maxWidth: '1200px',
          zIndex: 10,
          opacity: titleState >= 5 ? 1 : 0,
          pointerEvents: titleState >= 5 ? 'auto' : 'none',
        }}
      >
        <h2
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '1.5rem',
            color: 'var(--text-secondary)',
            fontWeight: 400,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            marginBottom: '2.25rem',
          }}
        >
          Integrating <AccentTerm id="genai" onOpen={setActiveDef}>Generative AI</AccentTerm> into{' '}
          <AccentTerm id="pa" onOpen={setActiveDef}>Public Affairs</AccentTerm> Practice
        </h2>

        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <a
            href={appPath}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.7rem',
              padding: '1rem 2rem',
              borderRadius: '999px',
              textDecoration: 'none',
              fontFamily: 'var(--font-sans)',
              fontSize: '0.82rem',
              letterSpacing: '0.16em',
              textTransform: 'uppercase',
              color: '#f8fafc',
              background: 'rgba(255,255,255,0.08)',
              border: '1px solid rgba(167, 139, 250, 0.35)',
              boxShadow: '0 0 28px rgba(167, 139, 250, 0.12)',
            }}
          >
            Skip to Dashboard
            <ArrowRight size={15} />
          </a>
          {hasVisitedApp && (
            <span
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.78rem',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'var(--text-accent)',
              }}
            >
              Returning visit
            </span>
          )}
        </div>

      </div>

      {definition && definitionStyle && typeof document !== 'undefined'
        ? createPortal(
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 15 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className="glass-card"
                style={{
                  position: 'fixed',
                  top: definitionStyle.top,
                  left: definitionStyle.left,
                  width: definitionStyle.width,
                  padding: '2.5rem',
                  textAlign: 'left',
                  zIndex: 1200,
                  background:
                    'radial-gradient(circle at 50% 0%, rgba(124, 58, 237, 0.18), transparent 52%), linear-gradient(180deg, rgba(12, 18, 34, 0.985), rgba(9, 12, 24, 0.985))',
                  border: '1px solid rgba(167, 139, 250, 0.28)',
                  boxShadow: '0 30px 70px rgba(0,0,0,0.62), 0 0 40px rgba(167, 139, 250, 0.08)',
                  borderRadius: '16px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    pointerEvents: 'none',
                    background:
                      'linear-gradient(135deg, rgba(167, 139, 250, 0.06), transparent 36%, transparent 64%, rgba(96, 165, 250, 0.04))',
                  }}
                />
                <button
                  onClick={() => setActiveDef(null)}
                  style={{
                    position: 'absolute',
                    top: '1.25rem',
                    right: '1.25rem',
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    cursor: 'pointer',
                    zIndex: 2,
                  }}
                >
                  <X size={20} />
                </button>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', position: 'relative', zIndex: 1 }}>
                  <h3
                    style={{
                      fontFamily: 'var(--font-serif)',
                      fontSize: '1.75rem',
                      color: 'var(--text-accent)',
                    }}
                  >
                    {definition.term}
                  </h3>
                  <CitationButton refs={definition.refs} />
                </div>
                <p
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '1.05rem',
                    lineHeight: '1.6',
                    color: '#f8fafc',
                    marginBottom: '1.5rem',
                    fontWeight: 400,
                    position: 'relative',
                    zIndex: 1,
                  }}
                >
                  {definition.short}
                </p>
                <div
                  style={{
                    padding: '1.25rem',
                    background: 'linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.025))',
                    borderRadius: '10px',
                    borderLeft: '3px solid var(--text-accent)',
                    position: 'relative',
                    zIndex: 1,
                  }}
                >
                  <strong
                    style={{
                      color: '#94a3b8',
                      display: 'block',
                      marginBottom: '0.6rem',
                      fontSize: '0.75rem',
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase',
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    Context
                  </strong>
                  <span
                    style={{
                      fontSize: '0.9rem',
                      color: '#cbd5e1',
                      fontFamily: 'var(--font-sans)',
                      lineHeight: 1.55,
                      display: 'block',
                    }}
                  >
                    {definition.context}
                  </span>
                </div>
              </motion.div>
            </AnimatePresence>,
            document.body,
          )
        : null}

      <div style={{ position: 'absolute', bottom: '2rem', left: 0, right: 0, margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', opacity: 0.6, zIndex: 5 }}>
        <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.8rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#94a3b8' }}>
          Scroll to Begin Review
        </span>
        <motion.div
          animate={{ height: [40, 70, 40] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
          style={{ width: '1px', background: 'linear-gradient(to bottom, var(--text-accent), transparent)' }}
        />
      </div>
      <div style={{ position: 'absolute', width: '100%', height: '100%', background: 'radial-gradient(circle at center, rgba(167, 139, 250, 0.08) 0%, transparent 65%)', pointerEvents: 'none', zIndex: 0 }} />
    </section>
  );
}
