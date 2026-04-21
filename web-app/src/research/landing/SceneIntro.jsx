import { motion } from 'framer-motion';
import CitationButton from './CitationButton';

const cardStyle = {
  padding: '2rem',
  border: '1px solid rgba(255,255,255,0.05)',
  borderRadius: '16px',
  background: 'rgba(255,255,255,0.02)',
  cursor: 'pointer',
};

const animProps = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-50px' },
  transition: { duration: 0.6 },
};

const hoverProps = {
  whileHover: { y: -5, boxShadow: '0 10px 30px rgba(167, 139, 250, 0.2)' },
};

const problemCards = [
  { stat: '53%', subtitle: 'Unstable landscape', text: 'say political instability is the top challenge', refs: ['quorum2025'] },
  { stat: '51%', subtitle: 'High volume', text: 'say issue volume is a major concern', refs: ['fiscalnote2026'] },
  { stat: '38%', subtitle: 'Capacity constraints', text: 'say their team size is too small', refs: ['fiscalnote2026'] },
];

const promiseCards = [
  { stat: '65%', subtitle: 'Text capability', text: 'success rate on text-based tasks', refs: ['mertens2026'] },
  { stat: '26–36%', subtitle: 'Time reclaimed', text: 'estimated productivity gain in communications functions', refs: ['bcg2025'] },
  { stat: '80%', subtitle: 'Built for augmentation', text: 'of communications work is primed for AI support', refs: ['bcg2025'] },
];

export default function SceneIntro() {
  return (
    <section className="scene section-main" id="scene-intro">
      <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
        <motion.div {...animProps}>
          <h2 className="section-title" style={{ marginBottom: '5rem' }}>Introduction</h2>
        </motion.div>

        <motion.div {...animProps} style={{ marginBottom: '5rem' }}>
          <h3 className="subsection-heading">The Problem</h3>
          <p
            className="body-large"
            style={{
              marginBottom: '2rem',
            }}
          >
            Public affairs professionals operate in a fast-paced political environment defined by instability,
            information overload, and rapid change. Teams must keep up with a constant flow of legislative and
            regulatory developments, often with limited staff and resources. As a result, too much time is spent on
            monitoring, reporting, and other recurring tasks, rather than on strategy itself.
            <CitationButton refs={['bitonti2023', 'fiscalnote2026', 'oecd2021', 'quorum2025', 'votervoice2025']} />
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
            {problemCards.map((item) => (
              <motion.article key={item.subtitle} {...hoverProps} style={cardStyle}>
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.875rem',
                    color: '#64748b',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '0.75rem',
                  }}
                >
                  {item.subtitle}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-serif)',
                    color: 'var(--text-accent)',
                    fontSize: '2.9rem',
                    marginBottom: '0.65rem',
                    lineHeight: 1,
                  }}
                >
                  {item.stat}
                </div>
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                  {item.text}
                  <CitationButton refs={item.refs} />
                </div>
              </motion.article>
            ))}
          </div>
        </motion.div>

        <motion.div {...animProps} style={{ marginBottom: '5rem' }}>
          <h3 className="subsection-heading">The Promise</h3>
          <p
            className="body-large"
            style={{
              marginBottom: '2rem',
            }}
          >
            Generative AI has the capacity to analyze large volumes of text, transform unstructured information into
            actionable insight, and support the drafting of briefs, statements, and advocacy materials. These
            capabilities are especially relevant to Public Affairs, a profession built on reading, writing, synthesis,
            and adaptation.
            <CitationButton refs={['bitonti2023', 'bcg2025', 'eloundou2023', 'noy2023']} />
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
            {promiseCards.map((item) => (
              <motion.article key={item.subtitle} {...hoverProps} style={cardStyle}>
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.875rem',
                    color: '#64748b',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '0.75rem',
                  }}
                >
                  {item.subtitle}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-serif)',
                    color: 'var(--text-accent)',
                    fontSize: '2.9rem',
                    marginBottom: '0.65rem',
                    lineHeight: 1,
                  }}
                >
                  {item.stat}
                </div>
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                  {item.text}
                  <CitationButton refs={item.refs} />
                </div>
              </motion.article>
            ))}
          </div>
        </motion.div>

        <motion.div {...animProps} style={{ marginBottom: '5rem' }}>
          <h3 className="subsection-heading">The Gap</h3>
          <p
            className="body-large"
            style={{
              marginBottom: '2rem',
            }}
          >
            In Public Affairs, generative AI adoption remains fragmented and uneven across teams and organizations. Its
            use is often ad hoc and heavily dependent on individual initiative. It rarely rests on shared standards,
            ethical frameworks, or practical playbooks.
            <CitationButton refs={['buhmann2025', 'rettig2023', 'section2026', 'yue2024']} />
          </p>

          <div style={{ display: 'flex', gap: '12rem', alignItems: 'stretch', justifyContent: 'center' }}>
            <motion.article
              {...hoverProps}
              style={{
                ...cardStyle,
                display: 'flex',
                alignItems: 'center',
                gap: '2rem',
                flex: 'none',
                maxWidth: '420px',
              }}
            >
              <div style={{ position: 'relative', width: '140px', height: '140px', flexShrink: 0 }}>
                <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                  <circle cx="18" cy="18" r="16" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3" />
                  <motion.circle
                    initial={{ strokeDasharray: '0, 100' }}
                    whileInView={{ strokeDasharray: '53.8, 100' }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.5, ease: 'easeOut' }}
                    cx="18"
                    cy="18"
                    r="16"
                    fill="none"
                    stroke="var(--text-accent)"
                    strokeWidth="3"
                  />
                </svg>
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '18px',
                    fontWeight: 600,
                  }}
                >
                  53.8%
                </div>
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                of government affairs professionals report using AI in their work, while 46.2% do not.
                <CitationButton refs={['quorum2025']} />
              </div>
            </motion.article>

            <motion.article
              {...hoverProps}
              style={{
                ...cardStyle,
                padding: '1.25rem',
                flex: 'none',
                width: '420px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.875rem',
                  color: '#64748b',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  textAlign: 'center',
                  paddingBottom: '0.75rem',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                Implementation Caution
              </div>

              <div style={{ padding: '0.5rem 0' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.68rem',
                    color: '#94a3b8',
                    fontStyle: 'italic',
                    textAlign: 'center',
                    marginBottom: '0.15rem',
                  }}
                >
                  Actively seeking AI tools
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem' }}>
                  <span style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', color: 'rgba(167,139,250,0.4)', lineHeight: 1 }}>57%</span>
                  <span style={{ color: '#94a3b8', fontSize: '1.6rem' }}>↘</span>
                  <span style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', color: 'var(--text-accent)', lineHeight: 1 }}>41%</span>
                </div>
              </div>

              <div style={{ height: '1px', background: 'rgba(255,255,255,0.05)' }} />

              <div style={{ padding: '0.5rem 0 0' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.68rem',
                    color: '#94a3b8',
                    fontStyle: 'italic',
                    textAlign: 'center',
                    marginBottom: '0.15rem',
                  }}
                >
                  Open but cautious about implementation
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem' }}>
                  <span style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', color: 'rgba(167,139,250,0.4)', lineHeight: 1 }}>25%</span>
                  <span style={{ color: '#94a3b8', fontSize: '1.6rem' }}>↗</span>
                  <span style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', color: 'var(--text-accent)', lineHeight: 1 }}>46%</span>
                </div>
              </div>

              <div style={{ textAlign: 'center' }}>
                <CitationButton refs={['fiscalnote2026']} />
              </div>
            </motion.article>
          </div>
        </motion.div>

        <motion.div {...animProps} style={{ marginBottom: '5rem' }}>
          <h3 className="subsection-heading">The Response</h3>
          <p
            className="body-large"
            style={{
              margin: 0,
            }}
          >
            This project examines how Generative AI can be systematically integrated into Public Affairs practice. It
            shows how it can support professionals facing information overload, rapid political change, and demand for
            timely strategy. This possibility is not merely described, but made concrete through the development of an
            application that can be tested in use.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
