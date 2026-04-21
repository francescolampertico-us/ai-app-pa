import { useState } from 'react';
import { motion } from 'framer-motion';
import CitationButton from './CitationButton';

const animationProps = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-100px' },
  transition: { duration: 0.6 },
};

const agencyRow = [
  { col: 5, title: 'Essential', copy: 'Human involvement is indispensable for task completion.' },
  { col: 4, title: 'Considerable', copy: 'The human drives the task, while AI assists continuously.' },
  { col: 3, title: 'Moderate', copy: 'Human and AI work in equal partnership.' },
  { col: 2, title: 'Limited', copy: 'AI drives the task, with only limited human oversight.' },
  { col: 1, title: 'No Collaboration', copy: 'AI handles the task entirely on its own.' },
];

export default function SceneLiteratureCh3() {
  const [hoverCol, setHoverCol] = useState(null);

  const getCellBg = (targetCols) => {
    if (!hoverCol) return 'var(--bg-void)';
    return targetCols.includes(hoverCol) ? 'rgba(167, 139, 250, 0.15)' : 'var(--bg-void)';
  };

  const getBorderColor = (targetCols) => {
    if (!hoverCol) return 'rgba(255,255,255,0.05)';
    return targetCols.includes(hoverCol) ? 'rgba(167, 139, 250, 0.5)' : 'rgba(255,255,255,0.05)';
  };

  return (
    <section className="scene section-main" id="scene-ch3" style={{ display: 'block' }}>
      <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
        <motion.div {...animationProps}>
          <div
            style={{
              color: 'var(--text-accent)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: '6rem',
              fontSize: '1rem',
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              paddingBottom: '2rem',
            }}
          >
            CHAPTER 03: Task Allocation Between Humans and AI
          </div>
        </motion.div>

        <motion.div {...animationProps} transition={{ delay: 0.2, duration: 0.6 }} style={{ marginBottom: '8rem' }}>
          <h3 className="subsection-heading" style={{ marginBottom: '4rem' }}>
            The Human-AI Task Division Typology
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(200px, 1.5fr) repeat(5, 1fr)',
              gap: '4px',
              background: 'transparent',
              padding: '1rem',
            }}
            onMouseLeave={() => setHoverCol(null)}
          >
            <div style={{ padding: '0.25rem 1rem 0.5rem' }} />
            <div
              style={{
                gridColumn: 'span 5',
                textAlign: 'center',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.82rem',
                letterSpacing: '0.16em',
                textTransform: 'uppercase',
                color: '#94a3b8',
                padding: '0.25rem 1rem 0.75rem',
              }}
            >
              Degree of Collaboration
            </div>

            <div style={{ padding: '1rem' }} />
            {[5, 4, 3, 2, 1].map((h) => (
              <motion.div
                key={h}
                onMouseEnter={() => setHoverCol(h)}
                style={{
                  background: getCellBg([h]),
                  border: `1px solid ${getBorderColor([h])}`,
                  padding: '1rem',
                  textAlign: 'center',
                  fontFamily: 'var(--font-serif)',
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: hoverCol === h ? '#fff' : 'var(--text-accent)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                }}
              >
                H{h}
              </motion.div>
            ))}

            <div style={{ padding: '1.5rem 1rem' }}>
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                Human Agency Scale
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: '#94a3b8' }}>
                (Shao et al., 2025)
                <CitationButton refs={['shao2025']} />
              </div>
            </div>
            {agencyRow.map((item) => (
              <motion.div
                key={item.col}
                onMouseEnter={() => setHoverCol(item.col)}
                style={{
                  background: getCellBg([item.col]),
                  border: `1px solid ${getBorderColor([item.col])}`,
                  padding: '1.5rem 1rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                }}
              >
                <strong
                  style={{
                    display: 'block',
                    fontFamily: 'var(--font-serif)',
                    fontSize: '1.125rem',
                    marginBottom: '0.5rem',
                    color: hoverCol === item.col ? '#fff' : 'var(--text-primary)',
                  }}
                >
                  {item.title}
                </strong>
                <span
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.875rem',
                    color: hoverCol === item.col ? '#e2e8f0' : '#94a3b8',
                    lineHeight: 1.5,
                    display: 'block',
                  }}
                >
                  {item.copy}
                </span>
              </motion.div>
            ))}

            <div style={{ padding: '1.5rem 1rem' }}>
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                Task &amp; Behavior Typology
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: '#94a3b8' }}>
                (Mollick, 2024 / Dell&apos;Acqua et al., 2026)
                <CitationButton refs={['mollick2024', 'dellacqua2023']} />
              </div>
            </div>
            <motion.div
              onMouseEnter={() => setHoverCol(5)}
              style={{
                gridColumn: 'span 1',
                background: getCellBg([5]),
                border: `1px solid ${getBorderColor([5])}`,
                padding: '1.5rem 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.3s',
              }}
            >
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', fontWeight: 'bold', color: hoverCol === 5 ? '#fff' : 'var(--text-primary)' }}>
                Just Me Tasks
              </div>
            </motion.div>

            <div
              style={{
                gridColumn: 'span 3',
                border: '1px solid rgba(255,255,255,0.05)',
                borderRadius: '8px',
                display: 'flex',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div
                onMouseEnter={() => setHoverCol(4)}
                style={{
                  flex: 1,
                  background: getCellBg([4]),
                  transition: 'all 0.3s',
                  cursor: 'pointer',
                  borderRight: '1px solid rgba(255,255,255,0.05)',
                  borderBottom: `1px solid ${getBorderColor([4])}`,
                  borderTop: `1px solid ${getBorderColor([4])}`,
                }}
              />
              <div
                onMouseEnter={() => setHoverCol(3)}
                style={{
                  flex: 1,
                  background: getCellBg([3]),
                  transition: 'all 0.3s',
                  cursor: 'pointer',
                  borderRight: '1px solid rgba(255,255,255,0.05)',
                  borderBottom: `1px solid ${getBorderColor([3])}`,
                  borderTop: `1px solid ${getBorderColor([3])}`,
                }}
              />
              <div
                onMouseEnter={() => setHoverCol(2)}
                style={{
                  flex: 1,
                  background: getCellBg([2]),
                  transition: 'all 0.3s',
                  cursor: 'pointer',
                  borderBottom: `1px solid ${getBorderColor([2])}`,
                  borderTop: `1px solid ${getBorderColor([2])}`,
                }}
              />
              <motion.div
                animate={{ x: hoverCol === 4 ? '-100%' : hoverCol === 2 ? '100%' : '0%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                style={{
                  position: 'absolute',
                  width: '33.33%',
                  height: '100%',
                  left: '33.33%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '1.125rem',
                    fontWeight: 'bold',
                    color: [4, 3, 2].includes(hoverCol) ? '#fff' : 'var(--text-primary)',
                  }}
                >
                  Delegated Tasks
                </div>
              </motion.div>
            </div>

            <motion.div
              onMouseEnter={() => setHoverCol(1)}
              style={{
                gridColumn: 'span 1',
                background: getCellBg([1]),
                border: `1px solid ${getBorderColor([1])}`,
                padding: '1.5rem 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.3s',
              }}
            >
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', fontWeight: 'bold', color: hoverCol === 1 ? '#fff' : 'var(--text-primary)' }}>
                Automated Tasks
              </div>
            </motion.div>

            <div style={{ padding: '1.5rem 1rem' }}>
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                Delegation-Pairing Spectrum
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: '#94a3b8' }}>
                (Ray, 2025)
                <CitationButton refs={['ray2025']} />
              </div>
            </div>

            <motion.div
              onMouseEnter={() => setHoverCol(5)}
              style={{
                gridColumn: 'span 1',
                background: getCellBg([5]),
                border: `1px solid ${getBorderColor([5])}`,
                padding: '1.5rem 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.3s',
              }}
            >
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', fontWeight: 'bold', color: hoverCol === 5 ? '#fff' : 'var(--text-primary)' }}>
                Expert Consultation
              </div>
            </motion.div>

            <div
              style={{
                gridColumn: 'span 2',
                border: '1px solid rgba(255,255,255,0.05)',
                borderRadius: '8px',
                display: 'flex',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div
                onMouseEnter={() => setHoverCol(4)}
                style={{
                  flex: 1,
                  background: getCellBg([4]),
                  transition: 'all 0.3s',
                  cursor: 'pointer',
                  borderRight: '1px solid rgba(255,255,255,0.05)',
                  borderBottom: `1px solid ${getBorderColor([4])}`,
                  borderTop: `1px solid ${getBorderColor([4])}`,
                }}
              />
              <div
                onMouseEnter={() => setHoverCol(3)}
                style={{
                  flex: 1,
                  background: getCellBg([3]),
                  transition: 'all 0.3s',
                  cursor: 'pointer',
                  borderBottom: `1px solid ${getBorderColor([3])}`,
                  borderTop: `1px solid ${getBorderColor([3])}`,
                }}
              />
              <motion.div
                animate={{ x: hoverCol === 4 ? '-50%' : hoverCol === 3 ? '50%' : '0%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                style={{
                  position: 'absolute',
                  width: '50%',
                  height: '100%',
                  left: '25%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '1.125rem',
                    fontWeight: 'bold',
                    color: [4, 3].includes(hoverCol) ? '#fff' : 'var(--text-primary)',
                  }}
                >
                  Active Pairing
                </div>
              </motion.div>
            </div>

            <motion.div
              onMouseEnter={() => setHoverCol(2)}
              style={{
                gridColumn: 'span 1',
                background: getCellBg([2]),
                border: `1px solid ${getBorderColor([2])}`,
                padding: '1.5rem 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.3s',
              }}
            >
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', fontWeight: 'bold', color: hoverCol === 2 ? '#fff' : 'var(--text-primary)' }}>
                Guided Delegation
              </div>
            </motion.div>

            <motion.div
              onMouseEnter={() => setHoverCol(1)}
              style={{
                gridColumn: 'span 1',
                background: getCellBg([1]),
                border: `1px solid ${getBorderColor([1])}`,
                padding: '1.5rem 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.3s',
              }}
            >
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', fontWeight: 'bold', color: hoverCol === 1 ? '#fff' : 'var(--text-primary)' }}>
                Full Delegation
              </div>
            </motion.div>
          </div>
        </motion.div>

        <motion.div {...animationProps} transition={{ delay: 0.4, duration: 0.6 }} style={{ marginBottom: '8rem' }}>
          <h3 className="subsection-heading" style={{ marginBottom: '2rem' }}>Two Collaboration Styles</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            <motion.div
              whileHover={{ y: -5, boxShadow: '0 10px 30px rgba(167, 139, 250, 0.2)' }}
              style={{
                padding: '2.5rem',
                border: '1px solid rgba(255,255,255,0.05)',
                borderRadius: '16px',
                background: 'rgba(255,255,255,0.02)',
                cursor: 'pointer',
              }}
            >
              <h4 className="panel-heading" style={{ color: 'var(--text-accent)', marginBottom: '1rem' }}>Centaur</h4>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', color: '#fff', fontWeight: 600, marginBottom: '1rem' }}>
                A strategic division of labor.
                <CitationButton refs={['dellacqua2023', 'mollick2024']} />
              </p>
              <p style={{ fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                The human switches between human-led and AI-led sub-tasks based on their relative strengths.
              </p>
            </motion.div>

            <motion.div
              whileHover={{ y: -5, boxShadow: '0 10px 30px rgba(167, 139, 250, 0.2)' }}
              style={{
                padding: '2.5rem',
                border: '1px solid rgba(255,255,255,0.05)',
                borderRadius: '16px',
                background: 'rgba(255,255,255,0.02)',
                cursor: 'pointer',
              }}
            >
              <h4 className="panel-heading" style={{ color: 'var(--text-accent)', marginBottom: '1rem' }}>Cyborg</h4>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1.125rem', color: '#fff', fontWeight: 600, marginBottom: '1rem' }}>
                A fluid integration of human and AI work.
                <CitationButton refs={['dellacqua2023', 'mollick2024']} />
              </p>
              <p style={{ fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                The human and the AI move back and forth within the same task at the micro-level.
              </p>
            </motion.div>
          </div>
        </motion.div>

        <motion.div {...animationProps} transition={{ delay: 0.6, duration: 0.6 }}>
          <h3 className="subsection-heading" style={{ marginBottom: '4rem' }}>What Shapes Task Allocation</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4rem', marginBottom: '3rem' }}>
            <div style={{ textAlign: 'center' }}>
              <h4 className="panel-heading" style={{ marginBottom: '0.5rem' }}>Feasibility</h4>
              <p style={{ fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                What AI can do well.
                <CitationButton refs={['mollick2024', 'shao2025']} />
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <h4 className="panel-heading" style={{ marginBottom: '0.5rem' }}>Desire</h4>
              <p style={{ fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                What workers want to delegate.
                <CitationButton refs={['mollick2024', 'shao2025']} />
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <h4 className="panel-heading" style={{ marginBottom: '0.5rem' }}>Morality</h4>
              <p style={{ fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                What should remain human.
                <CitationButton refs={['mollick2024', 'friis2025']} />
              </p>
            </div>
          </div>

          <div
            style={{
              padding: '2rem 3rem',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.05)',
              textAlign: 'left',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1.05rem', color: 'var(--text-secondary)', margin: 0 }}>
                Poor allocation creates productivity drag.
                <CitationButton refs={['workday2025']} />
              </p>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1.05rem', color: '#cbd5e1', margin: 0, fontWeight: 500 }}>
                Successful allocation uses AI to spot patterns and strengthen outcomes.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
