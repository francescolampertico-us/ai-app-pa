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
        color: '#a78bfa',
        borderBottom: '2px solid rgba(167, 139, 250, 0.32)',
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
  const [definitionStyle, setDefinitionStyle] = useState(null);
  const contentRef = useRef(null);
  const subtitleRef = useRef(null);
  const definition = useMemo(() => (activeDef ? DEFINITIONS[activeDef] : null), [activeDef]);

  useEffect(() => {
    const t1 = setTimeout(() => setTitleState(1), 500);
    const t2 = setTimeout(() => setTitleState(2), 1500);
    const t3 = setTimeout(() => setTitleState(3), 2150);
    const t4 = setTimeout(() => setTitleState(4), 3950);
    const t5 = setTimeout(() => setTitleState(5), 5050);

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
      const subtitleRect = subtitleRef.current?.getBoundingClientRect() ?? rect;
      const width = Math.min(388, window.innerWidth - 32);
      const left = Math.max(16, Math.min(rect.left + (rect.width - width) / 2 - 8, window.innerWidth - width - 16));
      const top = Math.min(subtitleRect.bottom + 10, window.innerHeight - 280);

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
          top: titleState >= 4 ? '2.3rem' : '45%',
          left: titleState >= 4 ? '2.45rem' : 'calc(50% + var(--nav-width) / 2)',
          x: titleState >= 4 ? 0 : '-50%',
          y: titleState >= 4 ? 0 : '-50%',
          scale: titleState >= 4 ? 0.352 : 1,
        }}
        transition={{ duration: 1.6, ease: [0.645, 0.045, 0.355, 1] }}
      >
        <AnimatePresence>
          {titleState < 5 && (
            <motion.div
              key="morph"
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.82, ease: [0.22, 1, 0.36, 1] }}
              style={{ display: 'flex', alignItems: 'center', whiteSpace: 'nowrap', color: '#d8d5ff' }}
            >
              <motion.span
                animate={{
                  width: titleState >= 1 ? 0 : 'auto',
                  opacity: titleState >= 1 ? 0 : 1,
                  paddingRight: titleState >= 1 ? 0 : '0.4em',
                }}
                style={{ overflow: 'hidden', display: 'inline-flex', whiteSpace: 'nowrap' }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                The
              </motion.span>

              <motion.div
                style={{ display: 'flex', position: 'relative' }}
                animate={{ x: titleState >= 2 ? '3.08em' : 0, paddingRight: titleState >= 3 ? 0 : '0.4em' }}
                transition={{ duration: 2.2, ease: [0.22, 1, 0.36, 1] }}
              >
                <motion.span
                  animate={{ width: titleState >= 3 ? 0 : 'auto', opacity: titleState >= 3 ? 0 : 1 }}
                  style={{ display: 'inline-flex', overflow: 'hidden', whiteSpace: 'nowrap' }}
                  transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
                >
                  Arch
                </motion.span>
                <span>itect</span>
                <motion.span
                  animate={{ width: titleState >= 3 ? 0 : 'auto', opacity: titleState >= 3 ? 0 : 1 }}
                  style={{ display: 'inline-flex', overflow: 'hidden', whiteSpace: 'nowrap' }}
                  transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
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
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                of
              </motion.span>

              <motion.div
                style={{ display: 'flex', position: 'relative' }}
                animate={{ x: titleState >= 2 ? '-1.85em' : 0 }}
                transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
              >
                <span>Strateg</span>
                <motion.span
                  animate={{ width: titleState >= 3 ? 0 : 'auto', opacity: titleState >= 3 ? 0 : 1 }}
                  style={{ display: 'inline-flex', overflow: 'hidden', whiteSpace: 'nowrap' }}
                  transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
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
                <div style={{ height: '6px', width: '2.2em', background: 'var(--text-accent)', borderRadius: '2px', marginTop: '0.25em', marginBottom: '0.42em' }} />
              </div>
              <div
                style={{
                  fontSize: '0.35em',
                  letterSpacing: '0.11em',
                  textTransform: 'uppercase',
                  color: 'rgba(167,139,250,0.55)',
                  fontWeight: 500,
                  fontFamily: 'var(--font-sans)',
                }}
              >
                Architecture for PA Strategy
              </div>
              <div
                style={{
                  fontSize: '0.28em',
                  letterSpacing: '0.08em',
                  color: 'rgba(167,139,250,0.38)',
                  fontWeight: 400,
                  fontFamily: 'var(--font-sans)',
                  marginTop: '0.5em',
                }}
              >
                Francesco Lampertico · AU · 2026
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {titleState >= 5 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.4, ease: 'easeOut', delay: 0.3 }}
            style={{
              position: 'absolute',
              top: '38%',
              left: 0,
              right: 0,
              margin: '0 auto',
              zIndex: 10,
              fontFamily: 'var(--font-sans)',
              fontSize: '0.78rem',
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: 'rgba(167,139,250,0.45)',
              textAlign: 'center',
              pointerEvents: 'none',
            }}
          >
            Francesco Lampertico, 2026
          </motion.div>
        )}
      </AnimatePresence>

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
          ref={subtitleRef}
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '1.5rem',
            color: 'var(--text-secondary)',
            fontWeight: 400,
            letterSpacing: '0.01em',
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
                padding: '1.65rem 1.75rem 1.75rem',
                textAlign: 'left',
                zIndex: 1200,
                background: 'linear-gradient(180deg, rgba(19, 24, 43, 0.985), rgba(17, 22, 40, 0.99))',
                border: '1px solid rgba(167, 139, 250, 0.22)',
                boxShadow: '0 26px 60px rgba(0,0,0,0.48)',
                borderRadius: '22px',
              }}
            >
              <button
                onClick={() => setActiveDef(null)}
                style={{
                  position: 'absolute',
                  top: '1.2rem',
                  right: '1.2rem',
                  background: 'transparent',
                  border: 'none',
                  color: '#e5e7eb',
                  cursor: 'pointer',
                  zIndex: 2,
                  opacity: 0.9,
                }}
              >
                <X size={18} />
              </button>
              <div style={{ width: '100%', paddingLeft: '1rem', position: 'relative', zIndex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.8rem' }}>
                  <h3
                    style={{
                      fontFamily: 'var(--font-serif)',
                      fontSize: '1.34rem',
                      color: '#a78bfa',
                      lineHeight: 1.1,
                      margin: 0,
                    }}
                  >
                    {definition.term}
                  </h3>
                  <CitationButton refs={definition.refs} />
                </div>
                <p
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.88rem',
                    lineHeight: '1.46',
                    color: '#f8fafc',
                    marginBottom: '0.9rem',
                    fontWeight: 400,
                    marginTop: 0,
                  }}
                >
                  {definition.short}
                </p>
                <div
                  style={{
                    width: 'calc(100% - 0.5rem)',
                    marginLeft: '-0.2rem',
                    padding: '0.95rem 1rem',
                    background: 'rgba(255,255,255,0.04)',
                    borderRadius: '12px',
                  }}
                >
                  <strong
                    style={{
                      color: '#f8fafc',
                      display: 'block',
                      marginBottom: '0.5rem',
                      fontSize: '0.7rem',
                      letterSpacing: '0.16em',
                      textTransform: 'uppercase',
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    Context
                  </strong>
                  <span
                    style={{
                      fontSize: '0.8rem',
                      color: '#cbd5e1',
                      fontFamily: 'var(--font-sans)',
                      lineHeight: 1.42,
                      display: 'block',
                    }}
                  >
                    {definition.context}
                  </span>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>,
          document.body,
        )
        : null}

      <div style={{ position: 'absolute', bottom: '0.1rem', left: 0, right: 0, margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', opacity: 0.6, zIndex: 5 }}>
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
