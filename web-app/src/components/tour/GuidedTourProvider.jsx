import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import TourOverlay from './TourOverlay';
import { REVIEWER_TOUR_ID, TOUR_DEFINITIONS, TOUR_STORAGE_KEY } from './tourDefinitions';
import { GuidedTourContext } from './GuidedTourContext';

function getStoredCompletion() {
  try {
    return window.localStorage.getItem(TOUR_STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

function setStoredCompletion(value) {
  try {
    if (value) window.localStorage.setItem(TOUR_STORAGE_KEY, '1');
    else window.localStorage.removeItem(TOUR_STORAGE_KEY);
  } catch {
    // ignore storage failures
  }
}

export function GuidedTourProvider({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTourId, setActiveTourId] = useState(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [isCompleted, setIsCompleted] = useState(() => getStoredCompletion());

  const activeTour = activeTourId ? TOUR_DEFINITIONS[activeTourId] : null;
  const activeStep = activeTour?.steps?.[stepIndex] || null;

  useEffect(() => {
    if (!activeStep?.route) return;
    if (location.pathname !== activeStep.route) {
      navigate(activeStep.route);
    }
  }, [activeStep?.route, location.pathname, navigate]);

  const closeTour = useCallback(() => {
    setActiveTourId(null);
    setStepIndex(0);
  }, []);

  const completeTour = useCallback(() => {
    setStoredCompletion(true);
    setIsCompleted(true);
    closeTour();
  }, [closeTour]);

  const startTour = useCallback((tourId = REVIEWER_TOUR_ID) => {
    setStoredCompletion(false);
    setIsCompleted(false);
    setActiveTourId(tourId);
    setStepIndex(0);
  }, []);

  const nextStep = useCallback(({ skipMissing = false } = {}) => {
    setStepIndex((current) => {
      if (!activeTour) return current;
      const nextIndex = current + 1;
      if (nextIndex >= activeTour.steps.length) {
        window.setTimeout(() => completeTour(), skipMissing ? 0 : 0);
        return current;
      }
      return nextIndex;
    });
  }, [activeTour, completeTour]);

  const previousStep = useCallback(() => {
    setStepIndex((current) => Math.max(0, current - 1));
  }, []);

  const value = useMemo(
    () => ({
      startTour,
      closeTour,
      isActive: Boolean(activeTour),
      isCompleted,
      activeTourId,
    }),
    [activeTour, activeTourId, closeTour, isCompleted, startTour],
  );

  return (
    <GuidedTourContext.Provider value={value}>
      {children}
      <TourOverlay
        isActive={Boolean(activeTour)}
        step={activeStep}
        stepIndex={stepIndex}
        totalSteps={activeTour?.steps?.length || 0}
        onBack={previousStep}
        onNext={nextStep}
        onClose={closeTour}
      />
    </GuidedTourContext.Provider>
  );
}
