import { motion } from 'framer-motion';
import CitationButton from './CitationButton';

const ADOPTION = [
  ['Help with brainstorming', 57],
  ['Content generation', 54],
  ['Bill analysis and summary', 54],
  ['Proofreading', 44],
  ['Data analysis and insights', 38],
  ['Impact of new legislation', 33],
  ['Discovering trends', 20],
  ['Data visualization', 18],
  ['Reporting', 17],
  ['Stakeholder mapping', 15],
];

const CURRENT_APPLICATIONS = [
  {
    title: 'Policy Monitoring and Legislative Tracking',
    text:
      'Tracks bills, regulations, and institutional signals relevant to the organization. Includes legislative tracking, relevance assessment, and monitoring of policy change.',
    refs: ['digiacomo2025', 'bitonti2023'],
  },
  {
    title: 'Stakeholder Mapping and Network Analysis',
    text:
      'Maps policymakers, intermediaries, coalitions, and institutional relationships around a policy issue. Includes stakeholder profiling, relationship mapping, and the identification of allies, opponents, and potential champions.',
    refs: ['digiacomo2025', 'bitonti2023'],
  },
  {
    title: 'Sentiment Analysis and Public Opinion Tracking',
    text:
      'Monitors media, online discourse, and wider issue salience to detect public mood, emerging pressure, and relational risk around a policy topic. Includes sentiment analysis, opinion mining, and issue tracking across digital channels.',
    refs: ['digiacomo2025', 'duberry2022'],
  },
  {
    title: 'Content Generation and Drafting Support',
    text:
      'Supports the preparation of first drafts and working materials for advocacy and institutional engagement. Includes policy briefs, lobbying letters, position papers, and meeting preparation, while leaving final persuasion and relationship management to human professionals.',
    refs: ['digiacomo2025', 'bitonti2023', 'lebenbauer2024'],
  },
];

const EMERGING = [
  {
    title: 'Predictive Policy Modeling',
    text:
      'Uses AI to forecast likely policy trajectories and support anticipatory planning around bills, regulations, and institutional developments.',
    refs: ['digiacomo2025', 'bitonti2023'],
  },
  {
    title: 'Real-Time Issue Tracking and Response',
    text:
      'Links continuous monitoring to faster analysis and strategic reaction as issues evolve across institutional and digital environments.',
    refs: ['digiacomo2025', 'duberry2022'],
  },
  {
    title: 'Simulating Policymaker Behavior through Digital Twins',
    text:
      'Uses modeled profiles of policymakers to test messaging strategies, anticipate policy reactions, and refine advocacy efforts before real-world engagement.',
    refs: ['digiacomo2025', 'primaryData2026'],
  },
  {
    title: 'AI-Generated Content and Personalization at Scale',
    text:
      'Extends drafting support into mass personalization and large-scale message tailoring, adapting calls to action for different audiences and advocacy contexts.',
    refs: ['digiacomo2025', 'yue2024'],
  },
];

const LIMITS = [
  {
    title: 'Limited Research Base',
    text:
      'The literature on AI in Public Affairs remains small, fragmented, and early-stage, with relatively few studies focused directly on PA, government relations, or lobbying.',
    footer: 'Field maturity: early',
    refs: ['bitonti2023', 'charles2022'],
  },
  {
    title: 'Limited Real-World Testing',
    text:
      'Most existing studies do not evaluate AI tools in actual policy cases or compare their performance systematically against traditional lobbying methods.',
    footer: 'Empirical evidence: limited',
    refs: ['bitonti2023', 'buhmann2025'],
  },
  {
    title: 'No Shared Integration Framework',
    text:
      'The field still lacks a widely shared technical or operational framework for integrating AI into Public Affairs workflows, roles, and professional routines.',
    footer: 'Frameworks: not yet consolidated',
    refs: ['digiacomo2025', 'lock2025'],
  },
];

const animProps = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.6 },
};

export default function SceneLiteratureCh1() {
  return (
    <section className="scene section-main" id="scene-ch1">
      <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
        <motion.div {...animProps}>
          <h2 className="section-title" style={{ marginBottom: '5rem' }}>Literature Review</h2>
        </motion.div>

        <motion.div {...animProps}>
          <div
            style={{
              color: 'var(--text-accent)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: '4rem',
              fontSize: '1rem',
            }}
          >
            Chapter 01: Artificial Intelligence in Public Affairs and Related Fields
          </div>
        </motion.div>

        <motion.div {...animProps} transition={{ duration: 0.6, delay: 0.1 }} style={{ marginBottom: '5rem' }}>
          <h3 className="subsection-heading" style={{ marginBottom: '1.2rem' }}>
            Where GenAI is currently being integrated
            <CitationButton refs={['fiscalnote2026']} />
          </h3>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1.18rem', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '2.5rem', maxWidth: '70ch' }}>
            Help with brainstorming and content generation dominate initial adoption.
          </p>
          <div style={{ display: 'grid', gap: '1.35rem' }}>
            {ADOPTION.map(([label, value], index) => (
              <div
                key={label}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1.55fr 2.2fr 0.45fr',
                  gap: '1.2rem',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', color: '#94a3b8' }}>{label}</span>
                <div
                  style={{
                    height: '18px',
                    borderRadius: '999px',
                    background: 'rgba(255,255,255,0.07)',
                    overflow: 'hidden',
                  }}
                >
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${value}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.75, delay: index * 0.04 }}
                    style={{
                      height: '100%',
                      borderRadius: '999px',
                      background:
                        value >= 44
                          ? 'linear-gradient(90deg, rgba(167,139,250,0.86), rgba(196,181,253,0.96))'
                          : 'rgba(167,139,250,0.45)',
                    }}
                  />
                </div>
                <span style={{ fontFamily: 'var(--font-serif)', fontSize: '1.35rem', color: '#fff' }}>{value}%</span>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div {...animProps} transition={{ duration: 0.6, delay: 0.18 }} style={{ marginBottom: '4rem' }}>
          <h3 className="subsection-heading">
            GenAI Applications in Public Affairs
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '1.6rem', marginBottom: '2rem' }}>
            {CURRENT_APPLICATIONS.map((item, index) => (
              <motion.article
                key={item.title}
                whileHover={{ y: -5, boxShadow: '0 10px 30px rgba(167, 139, 250, 0.16)' }}
                style={{
                  padding: '2.25rem 2rem',
                  minHeight: '320px',
                  border: index === 3 ? '1px solid rgba(167,139,250,0.24)' : '1px solid rgba(255,255,255,0.05)',
                  borderRadius: '16px',
                  background: 'rgba(255,255,255,0.02)',
                  boxShadow: index === 3 ? '0 22px 52px rgba(76, 29, 149, 0.16)' : 'none',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.55rem', lineHeight: 1.24, margin: '0 0 1.35rem', color: '#fff' }}>
                  {item.title}
                </h4>
                <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  {item.text}
                  <CitationButton refs={item.refs} />
                </p>
              </motion.article>
            ))}
          </div>

          <motion.div
            whileHover={{ y: -4 }}
            style={{
              padding: '2.6rem 2.4rem',
              border: '1px solid rgba(167,139,250,0.18)',
              borderRadius: '20px',
              background: 'rgba(20,13,33,0.82)',
              textAlign: 'center',
            }}
          >
            <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.7rem', margin: '0 0 1rem', color: '#fff' }}>
              Strategic Planning and Decision Support
            </h4>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', color: '#d6d3f1', lineHeight: 1.65, margin: 0 }}>
              Brings together policy monitoring, stakeholder intelligence, sentiment tracking, and drafted materials to
              support prioritization, scenario analysis, timing, and strategic choice.
              <CitationButton refs={['bitonti2023', 'digiacomo2025', 'buhmann2025']} />
            </p>
          </motion.div>
        </motion.div>

        <motion.div {...animProps} transition={{ duration: 0.6, delay: 0.26 }} style={{ marginBottom: '5rem' }}>
          <h3 className="subsection-heading">
            Emerging Applications
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '1.3rem' }}>
            {EMERGING.map((item) => (
              <motion.article
                key={item.title}
                whileHover={{ y: -4 }}
                style={{
                  padding: '2rem 1.7rem',
                  minHeight: '320px',
                  border: '1px solid rgba(255,255,255,0.05)',
                  borderRadius: '16px',
                  background: 'rgba(255,255,255,0.02)',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <h4 style={{ fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: '1rem', lineHeight: 1.45, margin: '0 0 1.1rem', color: '#e2e8f0' }}>
                  {item.title}
                </h4>
                <p style={{ fontFamily: 'var(--font-sans)', fontSize: '0.92rem', color: '#7f8ca3', lineHeight: 1.65, margin: 0 }}>
                  {item.text}
                  <CitationButton refs={item.refs} />
                </p>
              </motion.article>
            ))}
          </div>
        </motion.div>

        <motion.div {...animProps} transition={{ duration: 0.6, delay: 0.34 }}>
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '4rem' }}>
            <h3 className="subsection-heading" style={{ marginBottom: '2.4rem' }}>
              Current Limits of the Literature
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '2.2rem' }}>
              {LIMITS.map((item) => (
                <div
                  key={item.title}
                  style={{
                    display: 'grid',
                    gridTemplateRows: '1fr auto',
                    gap: '0.9rem',
                  }}
                >
                  <div
                    style={{
                      minHeight: '248px',
                      display: 'flex',
                      flexDirection: 'column',
                      paddingBottom: '0.35rem',
                      borderBottom: '1px solid rgba(167,139,250,0.24)',
                    }}
                  >
                    <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.65rem', lineHeight: 1.18, margin: '0 0 1rem', color: '#fff' }}>
                      {item.title}
                    </h4>
                    <p style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                      {item.text}
                      <CitationButton refs={item.refs} />
                    </p>
                  </div>
                  <div
                    style={{
                    display: 'flex',
                      alignItems: 'center',
                      fontFamily: 'var(--font-sans)',
                      fontSize: '1.08rem',
                      color: 'var(--text-accent)',
                    }}
                  >
                    {item.footer}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
