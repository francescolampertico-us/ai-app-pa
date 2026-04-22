import { motion } from 'framer-motion';

const OBJECTIVES = [
  'To identify the core functions and pressures within Public Affairs practice for which Generative AI is most relevant.',
  'To analyze how Generative AI can be systematically integrated into those functions in a profession-specific manner.',
  'To develop an application through which this integration can be translated into practice.',
];

export default function SceneRQ() {
  return (
    <section className="scene section-flow" id="scene-rq">
      <div style={{ width: '100%', maxWidth: '1260px', margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="section-title" style={{ marginBottom: '2.2rem' }}>
            Research Question &amp; Objectives
          </h2>

          <div
            style={{
              maxWidth: '1210px',
              margin: '0 auto 1.45rem',
              padding: '1.35rem 2rem 1.45rem',
              borderRadius: '30px',
              border: '1px solid rgba(167,139,250,0.2)',
              background: 'linear-gradient(180deg, rgba(23,16,36,0.88), rgba(16,11,26,0.88))',
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.02)',
            }}
          >
            <h2
              className="card-title-editorial"
              style={{
                fontSize: 'clamp(1.52rem, 1.95vw, 2.15rem)',
                lineHeight: 1.22,
                letterSpacing: '-0.04em',
                textAlign: 'center',
                margin: 0,
                marginInline: 'auto',
              }}
            >
              “How can Generative Artificial Intelligence be systematically integrated into day-to-day Public Affairs
              practice?”
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '1rem' }}>
            {OBJECTIVES.map((objective, index) => (
              <motion.article
                key={objective}
                whileHover={{ y: -4, boxShadow: '0 10px 30px rgba(167, 139, 250, 0.14)' }}
                style={{
                  minHeight: '248px',
                  padding: '1.45rem 1.35rem 1.4rem',
                  borderRadius: '22px',
                  border: '1px solid rgba(255,255,255,0.05)',
                  background: 'rgba(255,255,255,0.02)',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div
                  className="card-metric"
                  style={{
                    fontSize: '1.45rem',
                    marginBottom: '1.35rem',
                  }}
                >
                  0{index + 1}
                </div>
                <p className="card-body-soft" style={{ maxWidth: '27ch' }}>
                  {objective}
                </p>
              </motion.article>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
