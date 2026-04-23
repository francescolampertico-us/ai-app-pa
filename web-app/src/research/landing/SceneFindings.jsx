import { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronRight } from 'lucide-react';
import CitationButton from './CitationButton';

const FINDINGS = [
  {
    id: 'finding-01',
    label: 'Finding 01',
    title: 'Barriers to Adoption',
    summary:
      'AI adoption remains constrained less by technical possibility than by professional culture, pricing incentives, and client trust.',
    detail:
      'Interviewees described resistance that goes beyond whether the tools work. In public affairs, adoption is shaped by a profession built on relationships, a pricing model that does not always reward speed, and client expectations that still privilege visible human labor over AI-assisted efficiency.',
    quotes: [
      {
        text:
          '“For decades, personal knowledge has been your commodity… there’s already this sort of pushback when it comes to integrating AI, when your value proposition is the relationships that you have.”',
        attribution: 'Managing Director, Clyde',
        refs: ['managerClyde2026'],
      },
      {
        text:
          '“Several clients in the last 24 months have added a rider to their contracts that expressly bans our use of AI products… they want to know that the premium price they’re paying for human lobbyists… are actually the ones servicing their account.”',
        attribution: 'Partner, Tiber Creek Group',
        refs: ['partnerTiber2026'],
      },
    ],
    refs: ['primaryData2026'],
  },
  {
    id: 'finding-02',
    label: 'Finding 02',
    title: 'Current Use',
    summary: 'AI currently adds the most value in synthesis and first drafts.',
    detail:
      'Professionals described using AI mainly to summarize information, reduce research time, and produce draft material they could then review and refine. In the interviews, its role appeared less as autonomous judgment and more as support for the early stages of analytical and writing work.',
    quotes: [
      {
        text:
          '“I always need a starter dough. I don’t care if it’s for a press release or a speech. I’m a good editor, and if you give me a paragraph, I can build it out into twenty. But I need that first piece, almost like a prompt.”',
        attribution: 'Partner, Tiber Creek Group',
        refs: ['partnerTiber2026'],
      },
      {
        text:
          '“I’ll use it as the draft to get started. Having it synthesize an article or summarize the related research that we’ve done is really helpful… it gives me a place to start. Then I’ll go back in and dig into the journals.”',
        attribution: 'Vice President of Policy and Government Relations, Woodwell Climate Research Center',
        refs: [],
      },
    ],
    refs: ['primaryData2026'],
  },
  {
    id: 'finding-03',
    label: 'Finding 03',
    title: 'Limits in Practice',
    summary: 'Professionals still face significant practical constraints when attempting to use AI in high-stakes work.',
    detail:
      'The interviews point to recurring challenges in verifying accuracy, recovering missing context, protecting sensitive information, and determining how far AI can be trusted in work that still requires human judgment.',
    quotes: [
      {
        text:
          '“One thing was wrong. This is not a ‘bat .300 and get to the Hall of Fame’ type of job. You have to be right. They’re paying you to be right.”',
        attribution: 'Partner, Tiber Creek Group',
        refs: ['partnerTiber2026'],
      },
      {
        text:
          '“I think AI never gets us anything that’s ready to launch or ready to show the client as a final deliverable… They’re rough drafts.”',
        attribution: 'Partner, Beekeeper Group',
        refs: ['partnerBeekeeper2026'],
      },
    ],
    refs: ['primaryData2026'],
  },
  {
    id: 'finding-04',
    label: 'Finding 04',
    title: 'Future Opportunities',
    summary: 'The next frontier for AI lies in helping practitioners test strategy before real-world deployment.',
    detail:
      'Beyond drafting and summarization, the most promising directions were linked to testing messages, simulating stakeholder reactions, and shaping reputation in AI-mediated information environments. These uses move AI beyond support work and into strategic preparation, while still keeping human judgment at the center.',
    quotes: [
      {
        text:
          '“They’ve created political duplicates of public figures. If you want to know what Mark Rubio’s opinion is on something, they’ve got a digital duplicate that’s about 81% accurate… that speeds up the process and gets you to the next level faster.”',
        attribution: 'Managing Director, Clyde',
        refs: ['managerClyde2026'],
      },
      {
        text:
          '“You filter each of those issues through those emotions into a matrix of a hundred different ads, and then you see which one sticks.”',
        attribution: 'Founder and Managing Partner, Unfiltered Media; Founder and Co-CEO, Change Agent',
        refs: [],
      },
    ],
    refs: ['primaryData2026'],
  },
];

export default function SceneFindings() {
  const [activeFinding, setActiveFinding] = useState(null);

  return (
    <section className="scene section-main" id="scene-findings">
      <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="section-title" style={{ marginBottom: '5rem' }}>Interview Findings</h2>
        </motion.div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: '1.6rem',
            marginBottom: '2rem',
            alignItems: 'start',
          }}
        >
          {FINDINGS.map((item) => {
            const expanded = activeFinding === item.id;
            return (
              <motion.button
                key={item.id}
                type="button"
                onClick={() => setActiveFinding(expanded ? null : item.id)}
                whileHover={{ y: -4 }}
                style={{
                  textAlign: 'left',
                  width: '100%',
                  height: 'auto',
                  alignSelf: 'start',
                  minHeight: expanded ? 'auto' : '320px',
                  padding: expanded ? '2rem 2rem 1.8rem' : '2rem',
                  borderRadius: '28px',
                  border: expanded ? '1px solid rgba(167,139,250,0.24)' : '1px solid rgba(255,255,255,0.05)',
                  background: 'rgba(20,13,33,0.88)',
                  color: 'inherit',
                  cursor: 'pointer',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    top: '2rem',
                    right: '2rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {expanded ? <ChevronDown size={28} color="#94a3b8" /> : <ChevronRight size={28} color="#94a3b8" />}
                </div>

                <div style={{ paddingRight: '3.4rem' }}>
                  <div
                    className="card-label-accent"
                    style={{
                      marginBottom: expanded ? '1.4rem' : '1.75rem',
                      display: 'inline-flex',
                      gap: '0.55rem',
                      alignItems: 'baseline',
                      fontVariantNumeric: 'tabular-nums',
                      lineHeight: 1,
                    }}
                  >
                    <span>Finding</span>
                    <span
                      style={{
                        display: 'inline-block',
                        minWidth: '2.35ch',
                        textAlign: 'left',
                        lineHeight: 1,
                        transform: 'translateY(-0.1em)',
                      }}
                    >
                      {item.label.slice(-2)}
                    </span>
                  </div>

                  <h3
                    className="panel-heading"
                    style={{
                      fontSize: '2.1rem',
                      lineHeight: 1.08,
                      margin: '0 0 1.55rem',
                    }}
                  >
                    {item.title}
                  </h3>

                  <p
                    className="card-body-soft"
                    style={{
                      fontSize: expanded ? '1rem' : '0.98rem',
                      lineHeight: 1.62,
                      margin: expanded ? '0 0 2.1rem' : 0,
                      maxWidth: expanded ? 'none' : '29ch',
                      minHeight: expanded ? 'auto' : '8.1rem',
                    }}
                  >
                    {item.summary}
                  </p>
                </div>

                {expanded ? (
                  <div>
                    <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '2rem' }} />
                    <p className="card-body-soft" style={{ fontSize: '1rem', lineHeight: 1.7, margin: '0 0 2rem' }}>
                      {item.detail}
                      <CitationButton refs={item.refs} />
                    </p>

                    <div style={{ display: 'grid', gap: '1.6rem' }}>
                      {item.quotes.map((quote) => (
                        <div
                          key={quote.text}
                          style={{
                            padding: '1.8rem 1.8rem 1.5rem',
                            borderRadius: '26px',
                            background: 'rgba(12,10,24,0.46)',
                            borderLeft: '3px solid rgba(167,139,250,0.6)',
                          }}
                        >
                          <div className="card-quote">
                            {quote.text}
                          </div>
                          <div className="card-attribution">
                            — {quote.attribution}
                            <CitationButton refs={quote.refs} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </motion.button>
            );
          })}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6, delay: 0.1 }}
          style={{
            marginTop: '2.2rem',
            padding: '2.2rem 2.4rem 2.6rem',
            borderRadius: '34px',
            border: '1px solid rgba(167,139,250,0.18)',
            background: 'rgba(20,13,33,0.88)',
          }}
        >
          <div className="card-label-accent" style={{ marginBottom: '1.7rem' }}>
            Underlying Theme
          </div>
          <h3
            className="panel-heading"
            style={{
              fontSize: '2.1rem',
              lineHeight: 1.08,
              margin: '0 0 1.5rem',
            }}
          >
            Personalization as a condition of value
          </h3>
          <p className="card-body-soft" style={{ fontSize: '1rem', lineHeight: 1.62 }}>
            AI becomes more valuable when it is tailored to professional context. Practitioners did not describe the
            greatest value in generic outputs alone, but in systems that could reflect specific writing styles, client
            preferences, internal knowledge, stakeholder context, and evolving strategic needs.
            <CitationButton refs={['primaryData2026', 'managerClyde2026', 'vpWoodwell2026', 'founderChangeAgent2026']} />
          </p>
        </motion.div>
      </div>
    </section>
  );
}
