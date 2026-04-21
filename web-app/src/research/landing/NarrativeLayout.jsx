import { motion } from 'framer-motion';

const SECTIONS = [
  { id: 'scene-hero', index: 'I', label: 'The Architecture of Strategy' },
  { id: 'scene-intro', index: 'II', label: 'Introduction' },
  { id: 'scene-rq', index: 'III', label: 'Research Question & Objectives' },
  { id: 'scene-ch1', index: 'IV', label: 'Literature Review' },
  { id: 'scene-methodology', index: 'V', label: 'Methodology' },
  { id: 'scene-findings', index: 'VI', label: 'Interview Findings' },
  { id: 'scene-system-design', index: 'VII', label: 'From Research to Prototype' },
  { id: 'scene-limitations', index: 'VIII', label: 'Limitations' },
  { id: 'scene-conclusion', index: 'IX', label: 'Conclusion' },
  { id: 'scene-references', index: 'X', label: 'References' },
  { id: 'scene-appendix', index: 'XI', label: 'Appendix' },
];

export default function NarrativeLayout({ children, activeScene }) {
  const navHidden = activeScene === 'scene-hero';

  return (
    <div className="cinematic-container">
      <aside className={`vertical-nav${navHidden ? ' is-hidden' : ''}`}>
        <div className="toc-shell">
          <div className="toc-kicker">Table of Content</div>
          <div className="toc-list">
            {SECTIONS.map((section) => {
              const isActive = activeScene === section.id;
              return (
                <div key={section.id} className={`toc-section${isActive ? ' is-active' : ''}`}>
                  {isActive && <motion.div layoutId="research-nav-indicator" className="toc-indicator" />}
                  <div className="toc-heading-row">
                    <span className="toc-index">{section.index}</span>
                    <a className="toc-heading-link" href={`#${section.id}`}>
                      {section.label}
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </aside>
      <main className="scroll-stage" id="scroll-container">
        {children}
      </main>
    </div>
  );
}
