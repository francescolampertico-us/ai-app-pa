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
          '“DC’s run by a lot of people who don’t know tech. They have spent their entire adult lives making just insane buckets of money on just being able to call someone.”',
        attribution: 'Founder and Managing Partner, Unfiltered Media; Co-Founder and Co-CEO, Change Agent',
        refs: ['founderChangeAgent2026'],
      },
      {
        text:
          '“Several clients in the last 24 months have added a rider to their contracts that expressly bans our use of AI products... they want to know that the premium price they’re paying for human lobbyists... are actually the ones servicing their account.”',
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
          '“We have created custom research tools that can do, we have estimated, 40 to 60 hours of work in one hour to sit down and basically produce the amount of work that a couple of people would do.”',
        attribution: 'Managing Director, Clyde',
        refs: ['managerClyde2026'],
      },
      {
        text:
          '“I’ll use it as like the draft to get started. You know, synthesize this article... summarizing the research that we’ve done related to certain things is really helpful... it helps give me a place to start.”',
        attribution: 'Vice President of Policy & Government Relations, Woodwell Climate Research Center',
        refs: ['vpWoodwell2026'],
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
          '“One thing was wrong. Like, I’m, this is not a, you know, bat 300 and get to the Hall of Fame type of job. Like you have to be right. They’re paying you to be right.”',
        attribution: 'Partner, Tiber Creek Group',
        refs: ['partnerTiber2026'],
      },
      {
        text:
          '“That is a high risk, right? Because my value as a senior communicator, my value is the counsel I give.”',
        attribution: 'Managing Director, Clyde',
        refs: ['managerClyde2026'],
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
          '“We’ve also invested heavily in market differentiation tools in the GEO space... how do you begin to change what the AI says about your client? ... the biggest battle we have is AI reputation.”',
        attribution: 'Managing Director, Clyde',
        refs: ['managerClyde2026'],
      },
      {
        text:
          '“You filter each of those issues through those emotions into a matrix of like a hundred different ads and then you see which one sticks.”',
        attribution: 'Founder and Managing Partner, Unfiltered Media; Co-Founder and Co-CEO, Change Agent',
        refs: ['founderChangeAgent2026'],
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
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                  <div
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.95rem',
                      letterSpacing: '0.16em',
                      textTransform: 'uppercase',
                      color: 'var(--text-accent)',
                      marginBottom: expanded ? '1.6rem' : '2rem',
                    }}
                  >
                    {item.label}
                  </div>
                  {expanded ? <ChevronDown size={28} color="#94a3b8" /> : <ChevronRight size={28} color="#94a3b8" />}
                </div>

                <h3
                  className="panel-heading"
                  style={{
                    fontSize: expanded ? '2.35rem' : '2.1rem',
                    lineHeight: 1.08,
                    margin: '0 0 1.7rem',
                  }}
                >
                  {item.title}
                </h3>

                <p
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: expanded ? '1.05rem' : '1rem',
                    lineHeight: 1.6,
                    color: '#f8fafc',
                    margin: expanded ? '0 0 2.1rem' : 0,
                    maxWidth: expanded ? 'none' : '28ch',
                  }}
                >
                  {item.summary}
                </p>

                {expanded ? (
                  <div>
                    <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '2rem' }} />
                    <p
                      style={{
                        fontFamily: 'var(--font-sans)',
                        fontSize: '1rem',
                        lineHeight: 1.7,
                        color: 'var(--text-secondary)',
                        margin: '0 0 2rem',
                      }}
                    >
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
                          <div
                            style={{
                              fontFamily: 'var(--font-serif)',
                              fontSize: '1rem',
                              lineHeight: 1.55,
                              color: '#e5e7eb',
                              marginBottom: '1.2rem',
                            }}
                          >
                            {quote.text}
                          </div>
                          <div
                            style={{
                              fontFamily: 'var(--font-sans)',
                              fontSize: '0.92rem',
                              lineHeight: 1.5,
                              color: '#71829f',
                            }}
                          >
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
          <div
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.95rem',
              letterSpacing: '0.16em',
              textTransform: 'uppercase',
              color: 'var(--text-accent)',
              marginBottom: '1.7rem',
            }}
          >
            Underlying Theme
          </div>
          <h3 className="subsection-heading" style={{ margin: '0 0 1.5rem' }}>
            Personalization as a condition of value
          </h3>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '1.05rem',
              lineHeight: 1.7,
              color: 'var(--text-secondary)',
              margin: 0,
            }}
          >
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
