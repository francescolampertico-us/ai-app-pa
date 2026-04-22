import { motion } from 'framer-motion';

const PHASES = [
  {
    phase: 'PHASE 1',
    title: 'Problem Framing and Needs Assessment',
    method: 'Semi-structured Expert Interviews',
    body: 'Semi-structured interviews with Public Affairs professionals, using tailored questions and follow-up prompts. Focused on workflows, current AI use, gaps in practice, and areas where AI could offer the greatest support. Used to define the problem space and identify the workflow needs most relevant to AI support.',
    details: {
      interviewBase: [
        {
          name: 'Laura Uttley',
          role: 'Vice President of Policy & Government Relations',
          organization: 'Woodwell Climate Research Center'
        },
        {
          name: 'Anthony LaFauce',
          role: 'Managing Director',
          organization: 'Clyde'
        },
        {
          name: 'Mike Panetta',
          role: 'Partner',
          organization: 'Beekeeper Group'
        },
        {
          name: 'Jeffrey Shapiro',
          role: 'Partner',
          organization: 'Tiber Creek Group'
        },
        {
          name: 'Craig Johnson',
          role: 'Founder & Managing Partner; Co-Founder & Co-CEO',
          organization: 'Unfiltered Media; Change Agent'
        }
      ],
      notes:
        'The capstone was also shaped by supplementary field notes drawn from informal conversations with Public Affairs professionals, professors, colleagues, and peers, as well as direct exposure to work in the field. These notes informed the framing and orientation of the project, but were kept distinct from the formal interview evidence.'
    }
  },
  {
    phase: 'PHASE 2',
    title: 'Task Prioritization and Requirements Definition',
    method: 'Qualitative Transcript Analysis and Literature Review',
    body: 'Review of interview transcripts and relevant literature. Focused on recurring workflow needs, professional bottlenecks, and literature-supported use cases for AI in Public Affairs. Used to define the target tasks and the requirements guiding application design.',
  },
  {
    phase: 'PHASE 3',
    title: 'Prototype Development and System Integration',
    method: 'Modular Design and Software Development',
    body: 'Development of individual tool prototypes based on the selected tasks. Focused on functions, inputs, outputs, workflow logic, and the integration of modules into a single application. Used to produce a working system for testing and evaluation.',
  },
  {
    phase: 'PHASE 4',
    title: 'Testing and Iterative Refinement',
    method: 'Prototype Testing and Output Review',
    body: 'Qualitative testing of the integrated application through representative task scenarios. Focused on interface usability, system performance, and the quality of generated results, reviewed against professional deliverables. Used to improve the application’s alignment with Public Affairs expectations and needs.',
  },
];

export default function SceneMethodology() {
  const getInterviewCardStyle = (index, total) => {
    if (total === 5) {
      if (index < 3) return { gridColumn: 'span 2' };
      if (index === 3) return { gridColumn: '2 / span 2' };
      if (index === 4) return { gridColumn: '4 / span 2' };
    }

    return { gridColumn: 'span 2' };
  };

  return (
    <section className="scene section-flow" id="scene-methodology">
      <div className="section-inner">
        <h2 className="section-title">Methodology</h2>
        <div className="timeline">
          {PHASES.map((item, index) => (
            <div key={item.phase} className="timeline-row">
              <div className="timeline-rail">
                <div className="timeline-dot" />
                {index < PHASES.length - 1 && <div className="timeline-line" />}
              </div>
              <motion.article whileHover={{ y: -4 }} className="glass-card timeline-card">
                <div className="section-kicker">{item.phase}</div>
                <h3 className="panel-heading" style={{ marginBottom: '0.85rem' }}>{item.title}</h3>
                <div className="timeline-method">Methodology Used: {item.method}</div>
                <p>{item.body}</p>
                {item.details ? (
                  <details
                    style={{
                      marginTop: '1rem',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: '16px',
                      background: 'rgba(255,255,255,0.025)',
                      overflow: 'hidden'
                    }}
                  >
                    <summary
                      style={{
                        cursor: 'pointer',
                        listStyle: 'none',
                        padding: '0.95rem 1rem',
                        fontFamily: 'var(--font-sans)',
                        fontSize: '0.88rem',
                        fontWeight: 600,
                        color: '#e2e8f0'
                      }}
                    >
                      <div>Interview Base and Supplementary Notes</div>
                      <div
                        style={{
                          marginTop: '0.35rem',
                          fontSize: '0.72rem',
                          fontWeight: 500,
                          letterSpacing: '0.12em',
                          textTransform: 'uppercase',
                          color: '#a78bfa'
                        }}
                      >
                        Click to expand
                      </div>
                    </summary>
                    <div style={{ padding: '0 1rem 1rem' }}>
                      <div
                        style={{
                          fontFamily: 'var(--font-sans)',
                          fontSize: '0.76rem',
                          letterSpacing: '0.14em',
                          textTransform: 'uppercase',
                          color: '#a78bfa',
                          marginBottom: '0.7rem'
                        }}
                      >
                        Interview Base
                      </div>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(6, minmax(0, 1fr))',
                          gap: '0.75rem',
                          marginBottom: '1rem'
                        }}
                      >
                        {item.details.interviewBase.map((person, personIndex) => (
                          <div
                            key={person.name}
                            style={{
                              ...getInterviewCardStyle(personIndex, item.details.interviewBase.length),
                              border: '1px solid rgba(255,255,255,0.08)',
                              background: 'rgba(255,255,255,0.03)',
                              borderRadius: '14px',
                              padding: '0.85rem 0.9rem',
                              boxShadow: 'inset 0 0 12px rgba(167, 139, 250, 0.04)'
                            }}
                          >
                            <div className="card-person-name">{person.name}</div>
                            <div className="card-person-role">{person.role}</div>
                            <div className="card-person-org">{person.organization}</div>
                          </div>
                        ))}
                      </div>
                      <div
                        style={{
                          fontFamily: 'var(--font-sans)',
                          fontSize: '0.76rem',
                          letterSpacing: '0.14em',
                          textTransform: 'uppercase',
                          color: '#a78bfa',
                          marginTop: '1rem',
                          marginBottom: '0.7rem'
                        }}
                      >
                        Supplementary Notes
                      </div>
                      <p className="card-body-strong" style={{ fontSize: '0.92rem', lineHeight: 1.7 }}>{item.details.notes}</p>
                    </div>
                  </details>
                ) : null}
              </motion.article>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
