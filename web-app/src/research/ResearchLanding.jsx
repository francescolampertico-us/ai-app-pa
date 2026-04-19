import { useEffect, useState } from 'react';
import './research.css';
import NarrativeLayout from '../../../academic-landing-page/src/components/NarrativeLayout.jsx';
import SceneHero from '../../../academic-landing-page/src/components/SceneHero.jsx';
import SceneIntro from '../../../academic-landing-page/src/components/SceneIntro.jsx';
import SceneRQ from '../../../academic-landing-page/src/components/SceneRQ.jsx';
import SceneLiteratureCh1 from '../../../academic-landing-page/src/components/SceneLiteratureCh1.jsx';
import SceneLiteratureCh2 from '../../../academic-landing-page/src/components/SceneLiteratureCh2.jsx';
import SceneLiteratureCh3 from '../../../academic-landing-page/src/components/SceneLiteratureCh3.jsx';
import SceneMethodology from '../../../academic-landing-page/src/components/SceneMethodology.jsx';
import SceneFindings from '../../../academic-landing-page/src/components/SceneFindings.jsx';
import SceneSystemDesign from '../../../academic-landing-page/src/components/SceneSystemDesign.jsx';
import SceneLimitations from '../../../academic-landing-page/src/components/SceneLimitations.jsx';
import CitationPopup from '../../../academic-landing-page/src/components/CitationPopup.jsx';

export default function ResearchLanding() {
  const [activeScene, setActiveScene] = useState('intro');
  const [hasVisitedApp, setHasVisitedApp] = useState(false);

  useEffect(() => {
    try {
      setHasVisitedApp(window.localStorage.getItem('strategitect_dashboard_visited') === '1');
    } catch {
      setHasVisitedApp(false);
    }
  }, []);

  useEffect(() => {
    const container = document.getElementById('scroll-container');
    if (!container) return undefined;

    const scenes = [
      { elementId: 'scene-hero', tag: 'intro' },
      { elementId: 'scene-intro', tag: 'intro' },
      { elementId: 'scene-rq', tag: 'intro' },
      { elementId: 'scene-ch1', tag: 'literature' },
      { elementId: 'scene-ch2', tag: 'literature' },
      { elementId: 'scene-ch3', tag: 'literature' },
      { elementId: 'scene-methodology', tag: 'methodology' },
      { elementId: 'scene-findings', tag: 'findings' },
      { elementId: 'scene-system-design', tag: 'system' },
      { elementId: 'scene-limitations', tag: 'limitations' }
    ];

    const handleScroll = () => {
      const scrollPos = container.scrollTop + (window.innerHeight * 0.5);
      let currentTarget = 'intro';

      for (const scene of scenes) {
        const el = document.getElementById(scene.elementId);
        if (el && el.offsetTop <= scrollPos) {
          currentTarget = scene.tag;
        }
      }

      setActiveScene(currentTarget);
    };

    container.addEventListener('scroll', handleScroll);
    handleScroll();

    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="research-shell">
      <NarrativeLayout activeScene={activeScene}>
        <SceneHero appPath="/app" hasVisitedApp={hasVisitedApp} />
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
      <CitationPopup />
    </div>
  );
}
