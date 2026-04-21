import { motion } from 'framer-motion';

const LIMITATIONS = [
  ['Limited Interview Sample', 'The qualitative phase was based on a small number of professionals, so the findings are exploratory rather than broadly generalizable.'],
  ['Researcher Involvement', "Task selection, tool design, and output assessment were shaped by the researcher's interpretation, introducing a degree of subjectivity."],
  ['Situated Personalization', 'The system is tailored to one author’s coursework, notes, writing practice, and workflow habits. That improves coherence, but it also limits direct generalizability.'],
  ['Sentiment Analysis Not Yet Implemented', 'The literature identifies sentiment analysis and public opinion tracking as relevant to Public Affairs work, but that layer is not yet part of the current prototype.'],
  ['Future Opportunities Remain Outside Scope', 'Predictive modeling, digital twins, and AI-mediated reputation analysis are identified by the literature, but remain future opportunities rather than implemented modules.'],
  ['Uneven Module Maturity', 'The project demonstrates a coherent system logic, but not every module has been validated to the same depth or under the same range of practical conditions.'],
  ['No Quantitative Benchmarking', 'Outputs were not evaluated through a formal scoring system or statistical comparison.'],
  ['Limited External Validation', 'The application was not tested systematically across a broad group of external practitioners, so wider validation remains necessary.'],
  ['Not Yet Tested at Organizational Scale', 'The prototype demonstrates integration at the level of an individual workflow. It has not yet been validated across teams, shared knowledge systems, approval structures, or governance processes.'],
];

const REFERENCES = [
  {
    text: 'Bitonti, A. (2023). Tools of digital innovation in public affairs management: A practice-oriented analysis. Journal of Public Affairs, 24(1), e2888.',
    url: 'https://doi.org/10.1002/pa.2888',
  },
  {
    text: 'Boston Consulting Group. (2025). The GenAI transformation of the communications function.',
    url: 'https://www.bcg.com/news/13october2025-how-ai-is-transforming-communications-function',
  },
  {
    text: 'Buhmann, A., Zerfass, A., Laborde, A., Moreno, A., Romenti, S., Tench, R., & Siegel, C. (2026). “We’re right in the foothills”: The adoption of artificial intelligence in corporate communication departments. Corporate Communications: An International Journal. Advance online publication.',
    url: 'https://doi.org/10.1108/CCIJ-09-2025-0296',
  },
  {
    text: 'Charles, V., Rana, N. P., & Carter, L. (2022). Artificial intelligence for data-driven decision-making and governance in public affairs. Government Information Quarterly, 39, 101742.',
    url: 'https://doi.org/10.1016/j.giq.2022.101742',
  },
  {
    text: 'Dell’Acqua, F., McFowland, E., Mollick, E. R., Lifshitz-Assaf, H., Kellogg, K. C., Rajendran, S., Krayer, L., Candelon, F., & Lakhani, K. R. (2026). Navigating the jagged technological frontier: Field experimental evidence of the effects of artificial intelligence on knowledge worker productivity and quality. Organization Science, 37(2), 403–423.',
    url: 'https://doi.org/10.1287/orsc.2025.21838',
  },
  {
    text: 'DiGiacomo, G. (2025). Public affairs management for business: Managerial tools for successful lobbying. Routledge.',
    url: 'https://doi.org/10.4324/9781003647829',
  },
  {
    text: 'Duberry, J. (2022). Artificial intelligence and democracy: Risks and promises of AI-mediated citizen-government relations. Edward Elgar Publishing.',
    url: 'https://doi.org/10.4337/9781788977319',
  },
  {
    text: 'Eloundou, T., Manning, S., Mishkin, P., & Rock, D. (2023). GPTs are GPTs: An early look at the labor market impact potential of large language models. arXiv.',
    url: 'https://arxiv.org/abs/2303.10130',
  },
  {
    text: 'Felten, E., Raj, M., & Seamans, R. (2023). How will language models like ChatGPT affect occupations and industries? arXiv.',
    url: 'https://doi.org/10.48550/arXiv.2303.01157',
  },
  {
    text: 'FiscalNote. (2026, January 20). The 2026 state of government affairs report.',
    url: 'https://fiscalnote.com/reports/2026-state-of-government-affairs-report',
  },
  {
    text: 'Friis, S., & Riley, J. W. (2025). Performance or principle: Resistance to artificial intelligence in the U.S. labor market (Harvard Business School Working Paper No. 26-017).',
    url: 'https://doi.org/10.2139/ssrn.5560401',
  },
  {
    text: 'Khalifa, M., & Albadawy, M. (2024). Using artificial intelligence in academic writing and research: An essential productivity tool. Computer Methods and Programs in Biomedicine Update, 5, 100145.',
    url: 'https://doi.org/10.1016/j.cmpbup.2024.100145',
  },
  {
    text: 'Lebenbauer, K. (2024). Artificial intelligence in public affairs. MAP Education and Humanities, 5.',
    url: 'https://doi.org/10.53880/2744-2373.2024.5.61',
  },
  {
    text: 'Lock, I., Hoffmann, L. B., Burgers, C., & Araujo, T. (2025). Types, methods, and evaluations of artificial intelligence (AI) in public communication research in the early phases of adoption: A systematic review. Annals of the International Communication Association, 49(2).',
    url: 'https://doi.org/10.1093/anncom/wlaf005',
  },
  {
    text: 'Mertens, M., Kuzee, A., Harris, B. S., Lyu, H., Li, W., Rosenfeld, J., Anto, M., Fleming, M., & Thompson, N. (2026). Crashing waves vs. rising tides: Preliminary findings on AI automation from thousands of worker evaluations of labor market tasks. arXiv.',
    url: 'https://arxiv.org/abs/2602.07238',
  },
  {
    text: 'Mollick, E. (2024). Co-intelligence: Living and working with AI. Portfolio/Penguin.',
    url: '',
  },
  {
    text: 'Noy, S., & Zhang, W. (2023). Experimental evidence on the productivity effects of generative artificial intelligence. Science, 381(6654), 187–192.',
    url: 'https://doi.org/10.1126/science.adh2586',
  },
  {
    text: 'Organisation for Economic Co-operation and Development. (2021). Lobbying in the 21st century: Transparency, integrity and access. OECD Publishing.',
    url: 'https://doi.org/10.1787/c6d8eff8-en',
  },
  {
    text: 'Quorum. (2025). 2025 state of government affairs.',
    url: 'https://www.quorum.us/reports/state-of-government-affairs-2025/',
  },
  {
    text: 'Ray, P. P. (2025). A review on vibe coding: Fundamentals, state-of-the-art, challenges and future directions. TechRxiv.',
    url: 'https://doi.org/10.36227/techrxiv.24712365',
  },
  {
    text: 'Rettig, C., & Mickeleit, T. (2023). There is no shortcut to AI. Or is there? How German communications professionals are navigating the AI revolution. In A. Adi (Ed.), Artificial intelligence in public relations and communications: Cases, reflections, and predictions (pp. 63–72). Quadriga University of Applied Sciences.',
    url: 'https://research.gold.ac.uk/id/eprint/34141/2/Adi,%20Ana%20-%20Ed%20-%20Artificial_Intelligence_in_Public_Relations__Communications_2023.p',
  },
  {
    text: 'Section. (2026, January). The AI proficiency report.',
    url: 'https://www.sectionai.com/ai/the-ai-proficiency-report',
  },
  {
    text: 'Shao, Y., Zope, H., Jiang, Y., Pei, J., Nguyen, D., Brynjolfsson, E., & Yang, D. (2025). Future of work with AI agents: Auditing automation and augmentation potential across the U.S. workforce. arXiv.',
    url: 'https://arxiv.org/abs/2506.06576',
  },
  {
    text: 'VoterVoice. (2025). The 2025 state of advocacy.',
    url: 'https://info.votervoice.net/resources/2025-state-of-advocacy-report',
  },
  {
    text: 'Yue, C. A., Men, L. R., Davis, D. Z., Mitson, R., Zhou, A., & Al Rawi, A. (2024). Public relations meets artificial intelligence: Assessing utilization and outcomes. Journal of Public Relations Research, 36(6), 513–534.',
    url: 'https://doi.org/10.1080/1062726X.2024.2400622',
  },
];

export default function SceneLimitations({ appPath = '/app' }) {
  return (
    <>
      <section className="scene section-flow" id="scene-limitations">
        <div className="section-inner">
          <h2 className="section-title">Limitations</h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
              gap: '2rem',
              alignItems: 'stretch',
            }}
          >
            {LIMITATIONS.map(([title, text], index) => {
              return (
                <motion.article
                  key={title}
                  whileHover={{ y: -4 }}
                  style={{
                    minHeight: '350px',
                    padding: '2.25rem 2.4rem 2.3rem',
                    borderRadius: '28px',
                    border: '1px solid rgba(255,255,255,0.05)',
                    background: 'rgba(255,255,255,0.02)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'baseline',
                      gap: '1rem',
                      marginBottom: '1.8rem',
                    }}
                  >
                    <div
                      style={{
                        color: 'var(--text-accent)',
                        fontSize: '1rem',
                        fontFamily: 'var(--font-sans)',
                        fontWeight: 300,
                        lineHeight: 1,
                        letterSpacing: '-0.01em',
                      }}
                    >
                      {String(index + 1).padStart(2, '0')}.
                    </div>
                    <h3
                      style={{
                        margin: 0,
                        fontFamily: 'var(--font-serif)',
                        fontSize: '1.28rem',
                        lineHeight: 1.42,
                        color: '#e7e5e4',
                      }}
                    >
                      {title}
                    </h3>
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.98rem',
                      lineHeight: 1.72,
                      color: '#94a3b8',
                      maxWidth: '24ch',
                    }}
                  >
                    {text}
                  </p>
                </motion.article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="scene section-flow" id="scene-conclusion">
        <div className="section-inner">
          <h2 className="section-title">Conclusion</h2>
          <div
            className="glass-card conclusion-card"
            style={{
              padding: '3.9rem 4.2rem 4rem',
              background: 'linear-gradient(180deg, rgba(13, 9, 21, 0.98), rgba(11, 9, 18, 0.99))',
              border: '1px solid rgba(167, 139, 250, 0.1)',
              borderRadius: '36px',
            }}
          >
            <h3
              className="subsection-heading"
              style={{
                fontSize: 'clamp(2.05rem, 2.8vw, 2.6rem)',
                marginBottom: '2.2rem',
              }}
            >
              A method for integration, not replacement
            </h3>
            <div style={{ display: 'grid', gap: '1.95rem', maxWidth: '70rem' }}>
              <p className="body-large" style={{ fontSize: '1.18rem', lineHeight: 1.78 }}>
                This project does not argue that Generative AI can replace Public Affairs professionals. Its
                contribution is to show what integration actually means in practice: identifying specific needs,
                designing targeted tools, placing them in a usable workflow, tailoring them to working style and
                context, and producing value where monitoring, synthesis, structured intelligence, and first-draft
                preparation are already central to the work.
              </p>
              <p className="body-large" style={{ fontSize: '1.18rem', lineHeight: 1.78 }}>
                The prototype is defensible because it remains scoped, review-required, research-informed, and situated
                in real working practice. Its strongest contribution lies not in automating judgment, but in clarifying
                how AI can support strategy while accountability, persuasion, contextual interpretation, and trust
                remain human-led.
              </p>
              <p className="body-large" style={{ fontSize: '1.18rem', lineHeight: 1.78 }}>
                A natural next step for future research is to move this model from the level of a personal workflow to
                the level of organizational use. That would mean testing how the same integration logic performs across
                teams, shared knowledge bases, approval systems, institutional styles, and governance structures,
                rather than within one tailored prototype alone.
              </p>
            </div>
            <a
              href={appPath}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 'fit-content',
                marginTop: '2.35rem',
                padding: '1.15rem 1.95rem',
                borderRadius: '999px',
                background: '#f8fafc',
                color: '#111827',
                textDecoration: 'none',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.84rem',
                letterSpacing: '0.19em',
                textTransform: 'uppercase',
              }}
            >
              Explore the Research Prototype
            </a>
          </div>
        </div>
      </section>

      <section className="scene section-flow" id="scene-references">
        <div className="section-inner">
          <h2 className="section-title">References</h2>
          <div
            className="glass-card conclusion-card"
            style={{
              padding: '2.7rem 3rem 2.9rem',
              background: 'linear-gradient(180deg, rgba(14, 9, 22, 0.94), rgba(10, 8, 16, 0.98))',
              border: '1px solid rgba(167, 139, 250, 0.08)',
            }}
          >
            <div style={{ display: 'grid', gap: '0.55rem' }}>
              {REFERENCES.map((entry) => (
                <p
                  key={entry.text}
                  style={{
                    margin: 0,
                    paddingLeft: '2.25rem',
                    textIndent: '-2.25rem',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.99rem',
                    lineHeight: 1.88,
                    color: '#d4d4d8',
                  }}
                >
                  {entry.text}
                  {entry.url && (
                    <>
                      {' '}
                      <a
                        href={entry.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          color: '#c4b5fd',
                          textDecoration: 'underline',
                          textUnderlineOffset: '3px',
                          textDecorationColor: 'rgba(196, 181, 253, 0.45)',
                          fontFamily: 'var(--font-sans)',
                          wordBreak: 'break-word',
                        }}
                      >
                        {entry.url}
                      </a>
                    </>
                  )}
                </p>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="scene section-flow" id="scene-appendix">
        <div className="section-inner">
          <h2 className="section-title">Appendix</h2>
          <div className="glass-card conclusion-card" style={{ padding: '2.35rem 2.5rem 2.4rem' }}>
            <h3 className="panel-heading" style={{ marginBottom: '1rem', fontSize: 'clamp(1.2rem, 1.5vw, 1.55rem)' }}>
              Project Materials
            </h3>
            <p className="body-medium" style={{ margin: 0 }}>
              Repository for the capstone prototype and landing page:
            </p>
            <a
              href="https://github.com/francescolampertico-us/ai-app-pa"
              target="_blank"
              rel="noreferrer"
              className="hero-button"
              style={{
                width: 'fit-content',
                marginTop: '0.8rem',
                padding: '0.82rem 1.2rem',
                fontSize: '0.72rem',
              }}
            >
              Open GitHub Repository
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
