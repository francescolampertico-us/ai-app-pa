import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

const BOARD_WIDTH = 1520;
const BOARD_HEIGHT = 970;

const WORKFLOW_LAYOUT = {
  strategic: { left: 840, top: 352.25, width: 240, minHeight: 150 },
  messaging: { x: 1200, y: 317, width: 230 },
  personalization: { x: 1200, y: 428, width: 270, height: 76 },
  remyArrowEndY: 450,
  outputSplitX: 1145,
  outputArrowEndX: 1200,
};

function tokenStyle(state) {
  if (state === 'missing') {
    return {
      border: '1px dashed rgba(245, 158, 11, 0.45)',
      background: 'rgba(245, 158, 11, 0.08)',
      color: '#fde68a',
    };
  }
  if (state === 'future') {
    return {
      border: '1px dashed rgba(56, 189, 248, 0.45)',
      background: 'rgba(56, 189, 248, 0.08)',
      color: '#bae6fd',
    };
  }
  return {
    border: '1px solid rgba(167, 139, 250, 0.3)',
    background: 'rgba(167, 139, 250, 0.12)',
    color: '#e9d5ff',
  };
}

const stages = [
  {
    id: 'literature',
    label: '01 Literature Defines the Domains',
    description:
      'The literature identifies the main application areas for Generative AI in Public Affairs before any prototype choices are made.',
  },
  {
    id: 'findings',
    label: '02 Findings Refine the Domains',
    description:
      'The interview findings refine those same areas by showing where current value is strongest, where judgment remains central, and what stays future-facing.',
  },
  {
    id: 'tools',
    label: '03 Tools Populate the Domains',
    description:
      'The prototype selects tools only after the literature areas and interview constraints are clear.',
  },
  {
    id: 'workflow',
    label: '04 Tools Become Workflow',
    description:
      'The same tools then move into the workflow, where intelligence gathering, preparation, strategic synthesis, and output creation become operational.',
  },
  {
    id: 'tailoring',
    label: '05 Outputs Adapt to Practice',
    description:
      'Generic output becomes more usable when it is adapted through style guides, conventions, notes, and working habits.',
  },
  {
    id: 'prototype',
    label: '06 Prototype Goes Live',
    description: 'The resulting system becomes the working prototype that can be entered and used.',
  },
];

const bucketCards = [
  {
    id: 'policy',
    title: 'Policy Monitoring and Legislative Tracking',
    findings: [
      'Strong current value in synthesis and research compression',
      'Review required because accuracy remains critical',
    ],
    x: 70,
    y: 340,
    width: 290,
    height: 270,
  },
  {
    id: 'stakeholder',
    title: 'Stakeholder Mapping and Network Analysis',
    findings: [
      'Useful for preparation around actors, relationships, and contact surfaces',
      'Still judgment-heavy and relationship-sensitive in practice',
    ],
    x: 385,
    y: 340,
    width: 290,
    height: 270,
  },
  {
    id: 'sentiment',
    title: 'Sentiment Analysis and Public Opinion Tracking',
    findings: [
      'Literature-supported, but not prioritized in the current prototype',
      'Remains visible as an unimplemented layer',
    ],
    state: 'missing',
    x: 700,
    y: 340,
    width: 290,
    height: 270,
  },
  {
    id: 'content',
    title: 'Content Generation and Drafting Support',
    findings: [
      'Strongest current value appears in first drafts and prepared materials',
      'Usefulness rises when outputs can be adapted to context and style',
    ],
    x: 1015,
    y: 340,
    width: 290,
    height: 270,
  },
];

const futureItems = [
  {
    id: 'realtime',
    label: 'Real-Time Issue Tracking and Response',
    board: { x: 70, y: 232, width: 290 },
    workflow: { x: 680, y: 106, width: 220 },
  },
  {
    id: 'predictive',
    label: 'Predictive Policy Modeling',
    board: { x: 385, y: 232, width: 290 },
    workflow: { x: 925, y: 106, width: 210 },
  },
  {
    id: 'twins',
    label: 'Simulating Policymaker Behavior through Digital Twins',
    board: { x: 700, y: 232, width: 290 },
    workflow: { x: 1160, y: 106, width: 260 },
  },
  {
    id: 'personalization',
    label: 'AI-Generated Content and Personalization at Scale',
    board: { x: 1015, y: 232, width: 290 },
    workflow: WORKFLOW_LAYOUT.personalization,
  },
];

const toolNodes = [
  { id: 'media_clips', label: 'Media Clips', state: 'implemented', bucket: { x: 95, y: 455, width: 240 }, workflow: { x: 70, y: 186, width: 220 } },
  { id: 'leg_tracker', label: 'Legislative Tracker', state: 'implemented', bucket: { x: 95, y: 515, width: 240 }, workflow: { x: 70, y: 271, width: 220 } },
  { id: 'influence_tracker', label: 'Influence Tracker', state: 'implemented', bucket: { x: 95, y: 575, width: 240 }, workflow: { x: 70, y: 356, width: 220 } },
  { id: 'background_memo', label: 'Background Memo', state: 'implemented', bucket: { x: 95, y: 635, width: 240 }, workflow: { x: 70, y: 441, width: 220 } },
  { id: 'hearing_memo', label: 'Hearing Memo', state: 'implemented', bucket: { x: 95, y: 695, width: 240 }, workflow: { x: 70, y: 526, width: 220 } },
  { id: 'stakeholder_map', label: 'Stakeholder Map', state: 'implemented', bucket: { x: 410, y: 455, width: 240 }, workflow: { x: 480, y: 271, width: 220 } },
  { id: 'stakeholder_briefing', label: 'Stakeholder Briefing', state: 'implemented', bucket: { x: 410, y: 535, width: 240 }, workflow: { x: 480, y: 356, width: 220 } },
  { id: 'media_list_builder', label: 'Media List', state: 'implemented', bucket: { x: 410, y: 615, width: 240 }, workflow: { x: 480, y: 506, width: 220 } },
  { id: 'sentiment_missing', label: 'Sentiment Analysis / Public Opinion Tracking', state: 'missing', bucket: { x: 725, y: 565, width: 240 }, workflow: { x: 70, y: 621, width: 220 } },
  { id: 'messaging_matrix', label: 'Messaging Deliverables', state: 'implemented', bucket: { x: 1040, y: 570, width: 240 }, workflow: WORKFLOW_LAYOUT.messaging },
  { id: 'remy_support', label: 'Remy support', state: 'implemented', bucket: { x: 1096, y: 84, width: 184 }, workflow: { x: 868, y: 592, width: 184 } },
];

const reviewItems = ['Source Checks', 'Verification Outputs', 'Manual Revision', 'Professional Judgment'];

function FlowPath({ d, color, width = 2.5, dashed = false, arrow, visible }) {
  return (
    <motion.path
      initial={false}
      animate={{ pathLength: visible ? 1 : 0, opacity: visible ? 0.7 : 0 }}
      transition={{ duration: 0.65, ease: 'easeInOut' }}
      d={d}
      stroke={color}
      strokeWidth={width}
      fill="none"
      strokeDasharray={dashed ? '6 6' : 'none'}
      markerEnd={arrow ? `url(#arrow-${arrow})` : undefined}
    />
  );
}

function SectionLabel({ text, x, y, width, visible, dimmed }) {
  return (
    <motion.div
      initial={false}
      animate={{ opacity: visible ? (dimmed ? 0.2 : 1) : 0, y: visible ? 0 : 6 }}
      transition={{ duration: 0.35 }}
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width,
        textAlign: 'center',
        fontFamily: 'var(--font-sans)',
        fontSize: '0.76rem',
        letterSpacing: '0.16em',
        textTransform: 'uppercase',
        color: '#94a3b8',
        zIndex: 6,
        pointerEvents: 'none',
      }}
    >
      {text}
    </motion.div>
  );
}

function BucketCard({ bucket, stageIndex, faded }) {
  const expandedHeight =
    stageIndex === 2
      ? bucket.id === 'policy'
        ? 505
        : bucket.id === 'stakeholder'
          ? 410
          : 310
      : bucket.height;

  return (
    <motion.div
      initial={false}
      animate={{ opacity: faded ? 0 : 1, scale: faded ? 0.985 : 1 }}
      transition={{ duration: 0.45 }}
      style={{
        position: 'absolute',
        left: bucket.x,
        top: bucket.y,
        width: bucket.width,
        minHeight: expandedHeight,
        padding: '1.35rem',
        borderRadius: '20px',
        border: bucket.state === 'missing' ? '1px dashed rgba(245, 158, 11, 0.35)' : '1px solid rgba(255,255,255,0.08)',
        background: bucket.state === 'missing' ? 'rgba(245, 158, 11, 0.04)' : 'rgba(255,255,255,0.02)',
        boxShadow: '0 18px 40px rgba(0,0,0,0.22)',
        zIndex: 3,
        overflow: 'hidden',
      }}
    >
      <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', color: '#fff', lineHeight: 1.3, marginBottom: stageIndex <= 1 ? '0.9rem' : '0.75rem', textAlign: 'center' }}>
        {bucket.title}
      </div>
      {stageIndex === 1 && (
        <div style={{ display: 'grid', gap: '0.6rem' }}>
          {bucket.findings.map((note) => (
            <div
              key={note}
              style={{
                padding: '0.72rem 0.8rem',
                borderRadius: '12px',
                border: bucket.state === 'missing' ? '1px dashed rgba(245, 158, 11, 0.25)' : '1px solid rgba(255,255,255,0.06)',
                background: bucket.state === 'missing' ? 'rgba(245, 158, 11, 0.05)' : 'rgba(255,255,255,0.03)',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.86rem',
                color: bucket.state === 'missing' ? '#fde68a' : '#d8dee9',
                lineHeight: 1.5,
              }}
            >
              {note}
            </div>
          ))}
        </div>
      )}
      {stageIndex === 2 && (
        <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.78rem', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#c4b5fd', textAlign: 'center' }}>
          Selected tools
        </div>
      )}
    </motion.div>
  );
}

function BoardNode({ item, stageIndex, workflowMode, dimmed }) {
  const target = workflowMode ? item.workflow : item.bucket;
  const visible = item.state === 'future' ? true : stageIndex >= 2;
  const baseOpacity = visible ? 1 : 0;

  return (
    <motion.div
      initial={false}
      animate={{
        left: target.x,
        top: target.y,
        width: target.width,
        minHeight: target.height || 56,
        opacity: dimmed ? baseOpacity * 0.15 : baseOpacity,
        scale: visible ? 1 : 0.92,
      }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      style={{
        position: 'absolute',
        padding: '0.8rem 0.95rem',
        borderRadius: '16px',
        fontFamily: 'var(--font-sans)',
        fontSize: item.state === 'future' ? '0.88rem' : '0.92rem',
        lineHeight: 1.45,
        display: 'flex',
        alignItems: 'center',
        justifyContent: item.state === 'future' ? 'center' : 'flex-start',
        textAlign: item.state === 'future' ? 'center' : 'left',
        boxShadow: '0 18px 40px rgba(0,0,0,0.3)',
        zIndex: 22,
        backdropFilter: 'blur(10px)',
        ...tokenStyle(item.state),
      }}
    >
      {item.label}
    </motion.div>
  );
}

export default function SceneSystemDesign({ appPath = '/app' }) {
  const [activeStage, setActiveStage] = useState(0);
  const boardViewportRef = useRef(null);
  const [boardScale, setBoardScale] = useState(1);

  const workflowVisible = activeStage >= 3;
  const tailoringVisible = activeStage === 4;
  const prototypeVisible = activeStage >= 5;

  const strategicTarget = workflowVisible
    ? { ...WORKFLOW_LAYOUT.strategic, padding: '0', compact: true }
    : { left: 70, top: 62, width: 1235, minHeight: 96, padding: '0.9rem 1.3rem 0.95rem', compact: false };

  useEffect(() => {
    const element = boardViewportRef.current;
    if (!element || typeof ResizeObserver === 'undefined') return undefined;

    const updateScale = () => {
      const width = element.clientWidth;
      if (!width) return;
      const nextScale = width >= 1100 ? Math.min(1, width / BOARD_WIDTH) : 1;
      setBoardScale(nextScale);
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const futureNodes = useMemo(
    () =>
      futureItems.map((item) => ({
        id: item.id,
        label: item.label,
        state: 'future',
        bucket: item.board,
        workflow: item.workflow,
      })),
    [],
  );

  const allNodes = useMemo(() => [...toolNodes, ...futureNodes], [futureNodes]);

  return (
    <section className="scene section-main" id="scene-system-design">
      <div style={{ width: '100%', maxWidth: '1360px', margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
          <h2 className="section-title">From Research to Prototype</h2>
          <div style={{ color: 'var(--text-accent)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '2.5rem', fontSize: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '2rem' }}>
            Integrating Generative AI into Public Affairs
          </div>
          <div style={{ display: 'grid', gap: '1.1rem', marginBottom: '2.6rem', maxWidth: '82ch' }}>
            <p className="section-lead">
              The board below shows how the research was translated into a prototype: literature defines the main areas,
              findings refine them, tools are selected, those tools are embedded into workflow, and the resulting system
              is adapted to practice.
            </p>
            <p className="section-note" style={{ color: '#e2e8f0' }}>
              The system is meant to support professional work, not replace professional judgment.
            </p>
          </div>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(185px, 1fr))', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {stages.map((stage, idx) => {
            const active = idx === activeStage;
            const completed = idx < activeStage;
            return (
              <button
                key={stage.id}
                onClick={() => setActiveStage(idx)}
                style={{
                  padding: '1rem 1.1rem',
                  borderRadius: '14px',
                  border: active ? '1px solid rgba(167, 139, 250, 0.42)' : '1px solid rgba(255,255,255,0.08)',
                  background: active ? 'rgba(167, 139, 250, 0.12)' : completed ? 'rgba(255,255,255,0.035)' : 'rgba(255,255,255,0.02)',
                  color: active ? '#f5f3ff' : '#cbd5e1',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8rem',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  lineHeight: 1.5,
                  textAlign: 'left',
                  cursor: 'pointer',
                }}
              >
                {stage.label}
              </button>
            );
          })}
        </div>

        <div style={{ minHeight: '3.25rem', marginBottom: '1.75rem' }}>
          <AnimatePresence mode="wait">
            <motion.p
              key={stages[activeStage].id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', color: 'var(--text-secondary)', lineHeight: 1.65, maxWidth: '78ch', margin: 0 }}
            >
              {stages[activeStage].description}
            </motion.p>
          </AnimatePresence>
        </div>

        <div
          ref={boardViewportRef}
          className="schematic-container"
          style={{ overflowX: boardScale < 1 ? 'visible' : 'auto', paddingBottom: '1rem', margin: '0 -1rem', paddingLeft: '1rem', paddingRight: '1rem' }}
        >
          <div style={{ position: 'relative', width: `${BOARD_WIDTH * boardScale}px`, height: `${BOARD_HEIGHT * boardScale}px` }}>
            <div
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                width: `${BOARD_WIDTH}px`,
                height: `${BOARD_HEIGHT}px`,
                transform: `scale(${boardScale})`,
                transformOrigin: 'top left',
                borderRadius: '28px',
                border: '1px solid rgba(255,255,255,0.06)',
                background: 'linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015))',
                boxShadow: 'inset 0 0 100px rgba(0,0,0,0.5)',
                overflow: 'hidden',
              }}
            >
              <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)', backgroundSize: '40px 40px', pointerEvents: 'none' }} />

              <motion.div
                initial={false}
                animate={{
                  left: strategicTarget.left,
                  top: strategicTarget.top,
                  width: strategicTarget.width,
                  minHeight: strategicTarget.minHeight,
                  padding: strategicTarget.padding,
                  opacity: activeStage === 5 ? 0.25 : 1,
                }}
                transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                style={{
                  position: 'absolute',
                  borderRadius: '18px',
                  border: '1px solid rgba(167, 139, 250, 0.35)',
                  background: 'var(--grad-glow)',
                  boxShadow: '0 10px 40px rgba(167, 139, 250, 0.08)',
                  zIndex: 19,
                  overflow: 'hidden',
                }}
              >
                <AnimatePresence mode="wait">
                  {workflowVisible ? (
                    <motion.div
                      key="strategic-compact"
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.25 }}
                      style={{
                        position: 'absolute',
                        inset: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        textAlign: 'center',
                        fontFamily: 'var(--font-sans)',
                        fontSize: '0.92rem',
                        lineHeight: 1.45,
                        color: '#f5f3ff',
                      }}
                    >
                      Strategic Synthesis
                    </motion.div>
                  ) : (
                    <motion.div
                      key="strategic-wide"
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.25 }}
                    >
                      <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.35rem', color: '#fff', marginBottom: '0.45rem', lineHeight: 1.2 }}>
                        Strategic Synthesis
                      </div>
                      <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.95rem', color: '#f8fafc', lineHeight: 1.6, maxWidth: '62ch' }}>
                        {activeStage <= 1
                          ? 'At the literature and findings level, this remains the umbrella that brings the other functions together while keeping strategy and accountability human-led.'
                          : 'In the prototype, these functions feed monitoring inputs, stakeholder preparation, and draft-ready materials into a strategic center under review-required conditions.'}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

              {bucketCards.map((bucket) => (
                <BucketCard key={bucket.id} bucket={bucket} stageIndex={Math.min(activeStage, 2)} faded={workflowVisible || activeStage === 5} />
              ))}

              <motion.div
                initial={false}
                animate={{ opacity: workflowVisible || activeStage === 5 ? 0 : 1 }}
                transition={{ duration: 0.45 }}
                style={{
                  position: 'absolute',
                  left: 70,
                  top: 36,
                  width: 1180,
                  zIndex: 5,
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.78rem',
                  letterSpacing: '0.16em',
                  textTransform: 'uppercase',
                  color: '#c4b5fd',
                  textAlign: 'left',
                }}
              >
                Strategic Planning and Decision Support
              </motion.div>

              <div style={{ position: 'absolute', left: 70, top: 210, width: 1180, zIndex: 5 }}>
                <motion.div
                  initial={false}
                  animate={{ opacity: workflowVisible || activeStage === 5 ? 0.18 : 1 }}
                  transition={{ duration: 0.45 }}
                  style={{ fontFamily: 'var(--font-sans)', fontSize: '0.78rem', letterSpacing: '0.16em', textTransform: 'uppercase', color: '#7dd3fc', marginBottom: '0.9rem', textAlign: 'left' }}
                >
                  Future Opportunities
                </motion.div>
              </div>

              <motion.div
                initial={false}
                animate={{ opacity: workflowVisible || activeStage === 5 ? 0 : 1 }}
                transition={{ duration: 0.45 }}
                style={{
                  position: 'absolute',
                  left: 70,
                  top: 316,
                  width: 1180,
                  zIndex: 5,
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.78rem',
                  letterSpacing: '0.16em',
                  textTransform: 'uppercase',
                  color: '#c4b5fd',
                  textAlign: 'left',
                }}
              >
                Current Use
              </motion.div>

              {allNodes.map((item) => (
                <BoardNode key={item.id} item={item} stageIndex={activeStage} workflowMode={workflowVisible} dimmed={activeStage === 5} />
              ))}

              <svg
                viewBox={`0 0 ${BOARD_WIDTH} ${BOARD_HEIGHT}`}
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none',
                  filter: 'drop-shadow(0 0 8px rgba(167, 139, 250, 0.4))',
                  zIndex: 21,
                  opacity: activeStage === 5 ? 0.12 : 1,
                  transition: 'opacity 0.6s ease',
                }}
                aria-hidden="true"
              >
                <defs>
                  <marker id="arrow-solid" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="#c084fc" />
                  </marker>
                  <marker id="arrow-future" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="#38bdf8" />
                  </marker>
                  <marker id="arrow-review" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" />
                  </marker>
                </defs>
                <FlowPath d="M290 214 H350" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M290 299 H350" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M290 384 H350" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M290 469 H350" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M290 554 H350" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M290 649 H350" color="#f59e0b" dashed visible={workflowVisible} />
                <FlowPath d="M350 214 V649" color="#a855f7" width={3} visible={workflowVisible} />
                <FlowPath d="M350 426.5 H840" color="#d8b4fe" width={3} arrow="solid" visible={workflowVisible} />
                <FlowPath d="M350 299 H480" color="#c084fc" arrow="solid" visible={workflowVisible} />
                <FlowPath d="M350 384 H480" color="#c084fc" arrow="solid" visible={workflowVisible} />
                <FlowPath d="M700 299 H760" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M700 384 H760" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M700 534 H760" color="#a855f7" visible={workflowVisible} />
                <FlowPath d="M760 299 V534" color="#a855f7" width={3} visible={workflowVisible} />
                <FlowPath d="M760 384 H840" color="#d8b4fe" width={3} arrow="solid" visible={workflowVisible} />
                <FlowPath d="M790 162 V196" color="#38bdf8" dashed visible={workflowVisible} />
                <FlowPath d="M1030 162 V196" color="#38bdf8" dashed visible={workflowVisible} />
                <FlowPath d="M1290 162 V196" color="#38bdf8" dashed visible={workflowVisible} />
                <FlowPath d="M790 196 H1290" color="#38bdf8" dashed visible={workflowVisible} />
                <FlowPath d={`M960 196 V${WORKFLOW_LAYOUT.strategic.top}`} color="#38bdf8" dashed arrow="future" visible={workflowVisible} />
                <FlowPath d={`M${WORKFLOW_LAYOUT.strategic.left + WORKFLOW_LAYOUT.strategic.width} 405.25 H${WORKFLOW_LAYOUT.outputSplitX}`} color="#d8b4fe" width={3} visible={workflowVisible} />
                <FlowPath d={`M${WORKFLOW_LAYOUT.outputSplitX} 405.25 V345`} color="#c084fc" visible={workflowVisible} />
                <FlowPath d={`M${WORKFLOW_LAYOUT.outputSplitX} 405.25 V466`} color="#38bdf8" dashed visible={workflowVisible} />
                <FlowPath d={`M${WORKFLOW_LAYOUT.outputSplitX} 345 H${WORKFLOW_LAYOUT.outputArrowEndX}`} color="#c084fc" arrow="solid" visible={workflowVisible} />
                <FlowPath d={`M${WORKFLOW_LAYOUT.outputSplitX} 466 H${WORKFLOW_LAYOUT.outputArrowEndX}`} color="#38bdf8" dashed arrow="future" visible={workflowVisible} />
                <FlowPath d={`M960 592 V${WORKFLOW_LAYOUT.remyArrowEndY}`} color="#94a3b8" width={2.5} arrow="review" visible={workflowVisible} />
              </svg>

              <SectionLabel text="Intelligence Gathering" x={35} y={126} width={290} visible={workflowVisible} dimmed={activeStage === 5} />
              <SectionLabel text="Stakeholder and Contact Preparation" x={390} y={206} width={400} visible={workflowVisible} dimmed={activeStage === 5} />
              <SectionLabel text="Future Opportunities" x={835} y={68} width={250} visible={workflowVisible} dimmed={activeStage === 5} />
              <SectionLabel text="Output Creation" x={1140} y={271} width={300} visible={workflowVisible} dimmed={activeStage === 5} />

              <motion.div
                initial={false}
                animate={{ opacity: workflowVisible && activeStage !== 5 ? 1 : activeStage === 5 ? 0.2 : 0, y: workflowVisible || activeStage === 5 ? 0 : 18 }}
                transition={{ duration: 0.45 }}
                style={{
                  position: 'absolute',
                  left: 70,
                  top: 780,
                  width: 1280,
                  padding: '1.65rem 2rem',
                  borderRadius: '24px',
                  border: '1px solid rgba(167, 139, 250, 0.4)',
                  background: 'linear-gradient(90deg, rgba(15, 23, 42, 0.8), rgba(9, 9, 11, 0.6))',
                  backdropFilter: 'blur(12px)',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.4), inset 0 0 20px rgba(167, 139, 250, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '2.5rem',
                  zIndex: 18,
                }}
              >
                <div style={{ flexShrink: 0, paddingRight: '1.6rem', borderRight: '1px solid rgba(255,255,255,0.1)' }}>
                  <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.3rem', color: '#e9d5ff', marginBottom: '0.35rem', letterSpacing: '-0.02em' }}>
                    Human Review Architecture
                  </div>
                  <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.75rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#a78bfa' }}>
                    Standing Requirement
                  </div>
                </div>
                <div style={{ flexGrow: 1 }}>
                  <p style={{ fontFamily: 'var(--font-sans)', fontSize: '0.95rem', color: '#cbd5e1', lineHeight: 1.6, margin: 0, maxWidth: '720px' }}>
                    Professional judgment is not limited to a final handoff. It remains active across the whole system,
                    from source checks on monitoring data to the validation of strategic synthesis and output.
                  </p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'minmax(140px, auto) minmax(140px, auto)', gap: '0.7rem', flexShrink: 0 }}>
                  {reviewItems.map((item) => (
                    <div
                      key={item}
                      style={{
                        border: '1px solid rgba(167, 139, 250, 0.3)',
                        background: 'rgba(167, 139, 250, 0.08)',
                        borderRadius: '8px',
                        padding: '0.58rem 0.9rem',
                        fontFamily: 'var(--font-sans)',
                        fontSize: '0.82rem',
                        color: '#e2e8f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        textAlign: 'center',
                      }}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div
                initial={false}
                animate={{ opacity: tailoringVisible ? 1 : 0, y: tailoringVisible ? 0 : 10 }}
                transition={{ duration: 0.45 }}
                style={{
                  position: 'absolute',
                  left: 1100,
                  top: 304,
                  width: 390,
                  minHeight: 430,
                  padding: '13.8rem 1.3rem 1.4rem',
                  borderRadius: '20px',
                  border: '1px solid rgba(167, 139, 250, 0.65)',
                  background: 'linear-gradient(180deg, rgba(20, 20, 45, 0.7), rgba(10, 10, 15, 0.5))',
                  backdropFilter: 'blur(12px)',
                  zIndex: 17,
                  boxShadow: '0 30px 60px rgba(0,0,0,0.5), 0 0 30px rgba(167, 139, 250, 0.1), inset 0 0 25px rgba(167, 139, 250, 0.15)',
                }}
              >
                <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.82rem', letterSpacing: '0.16em', textTransform: 'uppercase', lineHeight: 1.35, color: '#fff', textShadow: '0 0 15px rgba(167, 139, 250, 0.8)', marginBottom: '1.55rem', textAlign: 'left' }}>
                  Outputs Adapt to Practice
                </div>
                <p style={{ fontFamily: 'var(--font-sans)', fontSize: '0.86rem', fontWeight: 400, color: '#e2e8f0', lineHeight: 1.72, margin: 0, maxWidth: '34ch', textRendering: 'geometricPrecision' }}>
                  At this stage, outputs are adapted through style guides, organizational conventions, and reference
                  materials so that draft content aligns more closely with real Public Affairs practice.
                </p>
              </motion.div>

              <motion.div
                initial={false}
                animate={{ opacity: prototypeVisible ? 1 : 0, scale: prototypeVisible ? 1 : 0.95, x: prototypeVisible ? 0 : 40 }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                style={{
                  position: 'absolute',
                  right: '40px',
                  top: '40px',
                  bottom: '40px',
                  width: '840px',
                  background: 'rgba(15, 23, 42, 0.95)',
                  backdropFilter: 'blur(20px)',
                  borderRadius: '24px',
                  border: '1px solid rgba(167, 139, 250, 0.4)',
                  boxShadow: '0 40px 100px rgba(0,0,0,0.6), 0 0 40px rgba(167, 139, 250, 0.1)',
                  zIndex: 100,
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#09090b', color: '#fff', fontSize: '14px' }}>
                  <div style={{ width: '260px', borderRight: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
                    <div style={{ padding: '2rem 1.5rem' }}>
                      <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.5rem', fontWeight: 600, color: '#fff', marginBottom: '0.2rem' }}>
                        Str<span style={{ color: '#a78bfa' }}>α</span>tegitect
                      </div>
                      <div style={{ fontSize: '0.6rem', letterSpacing: '0.12em', color: '#64748b', textTransform: 'uppercase' }}>
                        Architecture for PA Strategy
                      </div>
                    </div>
                    <div style={{ padding: '0 1rem', marginBottom: '2rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)', color: '#94a3b8', fontSize: '0.85rem' }}>
                        <div style={{ width: '12px', height: '1px', background: '#94a3b8' }} /> Back to Research
                      </div>
                    </div>
                    <div style={{ padding: '0 1rem', marginBottom: '2rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', borderRadius: '12px', background: 'linear-gradient(90deg, rgba(167, 139, 250, 0.2), rgba(167, 139, 250, 0.05))', color: '#fff', fontSize: '0.85rem', fontWeight: 500 }}>
                        <div style={{ width: '14px', height: '14px', background: '#a78bfa', borderRadius: '2px' }} /> Dashboard
                      </div>
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto', padding: '0 1rem 2rem' }}>
                      <div style={{ fontSize: '0.65rem', letterSpacing: '0.12em', color: '#475569', textTransform: 'uppercase', marginBottom: '1rem', paddingLeft: '1rem' }}>
                        Intelligence Gathering
                      </div>
                      {['Media Clips', 'Legislative Tracker', 'Influence Tracker', 'Background Memo', 'Hearing Memo'].map((item) => (
                        <div key={item} style={{ padding: '0.6rem 1rem', color: '#94a3b8', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{ width: '14px', height: '14px', border: '1px solid #475569', borderRadius: '3px' }} /> {item}
                        </div>
                      ))}

                      <div style={{ fontSize: '0.65rem', letterSpacing: '0.12em', color: '#475569', textTransform: 'uppercase', marginTop: '2rem', marginBottom: '1rem', paddingLeft: '1rem' }}>
                        Stakeholder Preparation
                      </div>
                      {['Stakeholder Map', 'Stakeholder Briefing', 'Media List'].map((item) => (
                        <div key={item} style={{ padding: '0.6rem 1rem', color: '#94a3b8', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{ width: '14px', height: '14px', border: '1px solid #475569', borderRadius: '3px' }} /> {item}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#09090b', overflowY: 'auto' }}>
                    <div style={{ padding: '4rem 4rem 2rem' }}>
                      <div style={{ fontFamily: 'var(--font-serif)', fontSize: '2.5rem', fontWeight: 600, color: '#fff', marginBottom: '0.4rem' }}>
                        Str<span style={{ color: '#a78bfa' }}>α</span>tegitect
                      </div>
                      <div style={{ fontSize: '0.7rem', letterSpacing: '0.2em', color: '#a78bfa', textTransform: 'uppercase', marginBottom: '2.5rem' }}>
                        Architecture for Public Affairs Strategy
                      </div>

                      <p style={{ color: '#94a3b8', lineHeight: 1.6, fontSize: '0.95rem', maxWidth: '600px', marginBottom: '3rem' }}>
                        A research-informed system for bounded AI augmentation in Public Affairs. Organized around
                        intelligence gathering, stakeholder preparation, strategic synthesis, output creation, and human
                        review.
                      </p>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '4rem' }}>
                        <div style={{ padding: '1.5rem', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                          <div style={{ fontSize: '0.65rem', letterSpacing: '0.12em', color: '#a78bfa', textTransform: 'uppercase', marginBottom: '0.8rem' }}>
                            Strategic Planning & Decision Support
                          </div>
                          <div style={{ fontSize: '0.85rem', color: '#64748b', lineHeight: 1.5 }}>
                            Research prototype for bounded AI augmentation in Public Affairs. Outputs require
                            professional review.
                          </div>
                        </div>
                        <div style={{ padding: '1.5rem', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
                          <div style={{ fontSize: '0.65rem', letterSpacing: '0.12em', color: '#a78bfa', textTransform: 'uppercase', marginBottom: '0.8rem' }}>
                            Tailored Workflow
                          </div>
                          <div style={{ fontSize: '0.85rem', color: '#64748b', lineHeight: 1.5 }}>
                            Built from applied research, coursework, notes, and project-specific reference materials.
                          </div>
                        </div>
                      </div>

                      <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ fontSize: '0.7rem', letterSpacing: '0.15em', color: '#a78bfa', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                          Intelligence Gathering
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                          Monitoring, tracking, and briefing inputs that build the factual base.
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.2rem' }}>
                        {['Media Clips', 'Legislative Tracker', 'Influence Tracker'].map((title, i) => (
                          <div
                            key={title}
                            style={{ padding: '1.5rem', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', position: 'relative' }}
                          >
                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.2rem' }}>
                              <div style={{ padding: '0.2rem 0.6rem', borderRadius: '4px', background: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa', fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Monitoring
                              </div>
                              <div style={{ padding: '0.2rem 0.6rem', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', color: '#64748b', fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Review Required
                              </div>
                            </div>
                            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fff', marginBottom: '0.75rem' }}>{title}</div>
                            <div style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.5 }}>
                              {['Daily Google News monitoring...', 'Real-time federal and state bill tracking...', 'LDA, FARA, and disclosure records...'][i]}
                            </div>
                            <div style={{ position: 'absolute', bottom: '1.5rem', right: '1.5rem', fontSize: '0.65rem', color: '#334155' }}>
                              0{i + 1}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    padding: '2.5rem 3.5rem',
                    borderTop: '1px solid rgba(255,255,255,0.08)',
                    background: 'rgba(15, 23, 42, 0.8)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.75rem', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#a78bfa', marginBottom: '0.6rem' }}>
                      PROTOTYPE GOES LIVE
                    </div>
                    <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem', color: '#fff', marginBottom: '0.6rem', letterSpacing: '-0.02em' }}>
                      Strategitect
                    </div>
                    <div style={{ fontFamily: 'var(--font-sans)', fontSize: '0.9rem', color: '#94a3b8', maxWidth: '400px' }}>
                      Enter the prototype and test the tools in practice.
                    </div>
                  </div>
                  <a
                    href={appPath}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '1rem 2rem',
                      borderRadius: '999px',
                      textDecoration: 'none',
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase',
                      color: '#09090B',
                      background: '#fff',
                      boxShadow: '0 0 30px rgba(167, 139, 250, 0.3)',
                    }}
                  >
                    Launch Strategitect
                  </a>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
