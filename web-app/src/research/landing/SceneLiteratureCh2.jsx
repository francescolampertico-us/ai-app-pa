import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import CitationButton from './CitationButton';

const animationProps = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-100px' },
  transition: { duration: 0.6 },
};

const gains = [
  {
    value: '40%',
    label: 'faster',
    copy: 'Reduction in completion time on realistic professional writing tasks.',
    refs: ['noy2023'],
    glowStyle: { top: '-50px', left: '-50px' },
  },
  {
    value: '18%',
    label: 'higher quality',
    copy: 'Improvement in the judged quality of professional writing outputs.',
    refs: ['noy2023'],
    glowStyle: { bottom: '-50px', right: '-50px' },
  },
  {
    value: '60%',
    label: 'ready to use',
    copy: 'Share of outputs judged good enough without further editing.',
    refs: ['mertens2026'],
    glowStyle: { top: '-50px', right: '-50px' },
  },
];

export default function SceneLiteratureCh2() {
  const [activeFrontier, setActiveFrontier] = useState('inside');

  const insideActive = activeFrontier === 'inside';
  const outsideActive = activeFrontier === 'outside';

  return (
    <section className="scene section-main" id="scene-ch2">
      <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
        <motion.div {...animationProps}>
          <div
            style={{
              color: 'var(--text-accent)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: '4rem',
              fontSize: '1rem',
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              paddingBottom: '2rem',
            }}
          >
            CHAPTER 02: Performance in Professional Communication
          </div>
        </motion.div>

        <motion.div {...animationProps} transition={{ duration: 0.6, delay: 0.15 }}>
          <h3 className="subsection-heading" style={{ marginBottom: '1rem' }}>
            Measured Gains on Text-Based Tasks
          </h3>
          <p
            className="body-large"
            style={{
              marginBottom: '3rem',
              maxWidth: '820px',
            }}
          >
            GenAI delivers its strongest gains on bounded, text-based tasks with clear outputs and evaluation criteria.
            <CitationButton refs={['noy2023', 'mertens2026']} />
          </p>
        </motion.div>

        <motion.div
          {...animationProps}
          transition={{ duration: 0.6, delay: 0.2 }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem', marginBottom: '6rem' }}
        >
          {gains.map((gain) => (
            <motion.article
              key={gain.label}
              whileHover={{ y: -5, boxShadow: '0 10px 30px rgba(167, 139, 250, 0.2)' }}
              className="glass-card"
              style={{
                padding: '3rem 2rem',
                textAlign: 'center',
                position: 'relative',
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.05)',
                borderRadius: '16px',
                background: 'rgba(255,255,255,0.02)',
                cursor: 'pointer',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  width: '100px',
                  height: '100px',
                  background: 'var(--grad-glow)',
                  borderRadius: '50%',
                  ...gain.glowStyle,
                }}
              />
              <div
                style={{
                  fontFamily: 'var(--font-serif)',
                  fontSize: '4rem',
                  color: 'var(--text-primary)',
                  marginBottom: '1rem',
                }}
              >
                {gain.value}
              </div>
              <div
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '1.25rem',
                  color: 'var(--text-accent)',
                  marginBottom: '0.5rem',
                  fontWeight: 600,
                }}
              >
                {gain.label}
              </div>
              <p
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.875rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.4,
                }}
              >
                {gain.copy}
                <CitationButton refs={gain.refs} />
              </p>
            </motion.article>
          ))}
        </motion.div>

        <motion.div {...animationProps} transition={{ duration: 0.6, delay: 0.4 }} style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4rem' }}>
          <h3 className="subsection-heading" style={{ marginBottom: '0.4rem' }}>
            Conditional Performance Gains
          </h3>
          <div
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-accent)',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '1.25rem',
            }}
          >
            The jagged technological frontier
          </div>
          <p
            className="body-large"
            style={{
              marginBottom: '2.5rem',
              maxWidth: '780px',
            }}
          >
            Generative AI does not improve performance uniformly across professional tasks. Its strongest gains appear
            when tasks fit current model capabilities, while performance can weaken when tasks fall beyond them.
            <CitationButton refs={['dellacqua2023', 'workday2025']} />
          </p>

          <div
            style={{
              position: 'relative',
              width: '100%',
              borderRadius: '16px',
              border: '1px solid rgba(255,255,255,0.06)',
              background: 'rgba(255,255,255,0.02)',
              overflow: 'hidden',
              minHeight: '380px',
              cursor: 'default',
            }}
          >
            <svg
              viewBox="0 0 1000 380"
              preserveAspectRatio="none"
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 1 }}
            >
              <defs>
                <clipPath id="inside-clip-diagonal">
                  <polygon points="0,380 0,60 150,20 300,150 480,90 650,260 850,180 1000,380" />
                </clipPath>
                <clipPath id="outside-clip-diagonal">
                  <polygon points="0,0 1000,0 1000,380 850,180 650,260 480,90 300,150 150,20 0,60" />
                </clipPath>
              </defs>

              <motion.rect
                x="0"
                y="0"
                width="1000"
                height="380"
                fill="rgba(167,139,250,0.12)"
                clipPath="url(#inside-clip-diagonal)"
                animate={{ opacity: insideActive ? 1 : 0.4 }}
              />
              <motion.rect
                x="0"
                y="0"
                width="1000"
                height="380"
                fill="rgba(100,116,139,0.06)"
                clipPath="url(#outside-clip-diagonal)"
                animate={{ opacity: outsideActive ? 1 : 0.4 }}
              />
              <polyline
                points="0,60 150,20 300,150 480,90 650,260 850,180 1000,380"
                fill="none"
                stroke="rgba(167,139,250,0.4)"
                strokeWidth="2.5"
                strokeDasharray="8 6"
              />
            </svg>

            <button
              type="button"
              onClick={() => setActiveFrontier('inside')}
              style={{
                position: 'absolute',
                inset: 0,
                clipPath: 'polygon(0 100%, 0 15.79%, 15% 5.26%, 30% 39.47%, 48% 23.68%, 65% 68.42%, 85% 47.37%, 100% 100%)',
                zIndex: 5,
                cursor: 'pointer',
                background: 'transparent',
                border: 0,
              }}
              aria-label="Highlight tasks inside the frontier"
            />
            <button
              type="button"
              onClick={() => setActiveFrontier('outside')}
              style={{
                position: 'absolute',
                inset: 0,
                clipPath: 'polygon(0 0, 100% 0, 100% 100%, 85% 47.37%, 65% 68.42%, 48% 23.68%, 30% 39.47%, 15% 5.26%, 0 15.79%)',
                zIndex: 5,
                cursor: 'pointer',
                background: 'transparent',
                border: 0,
              }}
              aria-label="Highlight tasks outside the frontier"
            />

            <motion.div
              animate={{
                opacity: outsideActive ? 0.3 : 1,
                scale: insideActive ? 1.02 : 1,
              }}
              style={{
                position: 'absolute',
                bottom: '3rem',
                left: '3rem',
                width: '45%',
                zIndex: 11,
                pointerEvents: 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '0.4rem' }}>
                <div
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: 'var(--text-accent)',
                    boxShadow: insideActive ? '0 0 15px var(--text-accent)' : 'none',
                  }}
                />
                <span
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '1rem',
                    color: 'var(--text-accent)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    fontWeight: 600,
                    textShadow: insideActive ? '0 0 10px rgba(167,139,250,0.4)' : 'none',
                  }}
                >
                  Inside the frontier
                </span>
              </div>
              <p
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '1rem',
                  color: '#fff',
                  lineHeight: 1.5,
                  margin: 0,
                  fontWeight: 400,
                  textShadow: insideActive ? '0 0 20px rgba(255,255,255,0.2)' : 'none',
                }}
              >
                AI improves speed, task completion, and output quality.
                <span style={{ pointerEvents: 'auto', display: 'inline-block' }}>
                  <CitationButton refs={['noy2023', 'mertens2026']} />
                </span>
              </p>
            </motion.div>

            <motion.div
              animate={{
                opacity: insideActive ? 0.3 : 1,
                scale: outsideActive ? 1.02 : 1,
              }}
              style={{
                position: 'absolute',
                top: '3rem',
                right: '3rem',
                width: '45%',
                zIndex: 11,
                textAlign: 'right',
                pointerEvents: 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.8rem', marginBottom: '0.4rem' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '1rem',
                    color: '#cbd5e1',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    fontWeight: 600,
                    textShadow: outsideActive ? '0 0 10px rgba(255,255,255,0.3)' : 'none',
                  }}
                >
                  Outside the frontier
                </span>
                <div
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: '#94a3b8',
                    boxShadow: outsideActive ? '0 0 15px #fff' : 'none',
                  }}
                />
              </div>
              <p
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '1rem',
                  color: '#fff',
                  lineHeight: 1.5,
                  margin: 0,
                  fontWeight: 400,
                  textShadow: outsideActive ? '0 0 20px rgba(255,255,255,0.2)' : 'none',
                }}
              >
                AI output is inaccurate, less useful, and degrades human performance.
                <span style={{ pointerEvents: 'auto', display: 'inline-block' }}>
                  <CitationButton refs={['dellacqua2023', 'workday2025']} />
                </span>
              </p>
            </motion.div>

            <AnimatePresence>
              <motion.div
                key={activeFrontier}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: insideActive
                    ? 'radial-gradient(circle at 20% 80%, rgba(167,139,250,0.12), transparent 45%)'
                    : 'radial-gradient(circle at 85% 15%, rgba(255,255,255,0.08), transparent 40%)',
                  pointerEvents: 'none',
                  zIndex: 2,
                }}
              />
            </AnimatePresence>
          </div>

          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '1.1rem',
              color: '#64748b',
              marginTop: '1.25rem',
              fontStyle: 'italic',
              lineHeight: 1.6,
            }}
          >
            Not every task benefits equally. Better results depend on choosing tasks that fit current model strengths.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
