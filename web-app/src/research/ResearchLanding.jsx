import { useEffect, useState } from 'react';
import './research.css';
import NarrativeLayout from './landing/NarrativeLayout';
import SceneHero from './landing/SceneHero';
import SceneIntro from './landing/SceneIntro';
import SceneRQ from './landing/SceneRQ';
import SceneLiteratureCh1 from './landing/SceneLiteratureCh1';
import SceneLiteratureCh2 from './landing/SceneLiteratureCh2';
import SceneLiteratureCh3 from './landing/SceneLiteratureCh3';
import SceneMethodology from './landing/SceneMethodology';
import SceneFindings from './landing/SceneFindings';
import SceneSystemDesign from './landing/SceneSystemDesign';
import SceneLimitations from './landing/SceneLimitations';

const SCENES = [
  'scene-hero',
  'scene-intro',
  'scene-rq',
  'scene-ch1',
  'scene-ch2',
  'scene-ch3',
  'scene-methodology',
  'scene-findings',
  'scene-system-design',
  'scene-limitations',
  'scene-conclusion',
  'scene-references',
  'scene-appendix',
];

export default function ResearchLanding() {
  const [activeScene, setActiveScene] = useState('scene-hero');

  useEffect(() => {
    const container = document.getElementById('scroll-container');
    if (!container) return undefined;

    const updateActive = () => {
      const checkpoint = container.scrollTop + window.innerHeight * 0.35;
      let next = SCENES[0];

      for (const id of SCENES) {
        const element = document.getElementById(id);
        if (element && element.offsetTop <= checkpoint) {
          next = id;
        }
      }

      setActiveScene(next);
    };

    container.addEventListener('scroll', updateActive);
    updateActive();
    return () => container.removeEventListener('scroll', updateActive);
  }, []);

  return (
    <div className="research-shell">
      <NarrativeLayout activeScene={activeScene}>
        <SceneHero appPath="/app" />
        <SceneIntro />
        <SceneRQ />
        <SceneLiteratureCh1 />
        <SceneLiteratureCh2 />
        <SceneLiteratureCh3 />
        <SceneMethodology />
        <SceneFindings />
        <SceneSystemDesign appPath="/app" />
        <SceneLimitations appPath="/app" />
      </NarrativeLayout>
    </div>
  );
}
