import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { getTooltipPosition, getTourTarget, scrollTargetIntoView } from './tourUtils';

const TARGET_WAIT_MS = 2500;

export default function TourOverlay({
  isActive,
  step,
  stepIndex,
  totalSteps,
  onBack,
  onNext,
  onClose,
}) {
  const [targetRect, setTargetRect] = useState(null);

  useEffect(() => {
    if (!isActive || !step) return undefined;

    let frameId = null;
    let timeoutId = null;
    let cancelled = false;
    let hasScrolled = false;

    const updateRect = () => {
      if (cancelled) return;

      const target = getTourTarget(step.target);
      if (target) {
        if (!hasScrolled) {
          scrollTargetIntoView(target);
          hasScrolled = true;
        }
        const rect = target.getBoundingClientRect();
        setTargetRect(rect);
      } else {
        setTargetRect(null);
      }

      frameId = window.requestAnimationFrame(updateRect);
    };

    updateRect();

    if (step.target) {
      timeoutId = window.setTimeout(() => {
        if (!getTourTarget(step.target)) {
          onNext({ skipMissing: true });
        }
      }, TARGET_WAIT_MS);
    }

    return () => {
      cancelled = true;
      if (frameId) window.cancelAnimationFrame(frameId);
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [isActive, onNext, step]);

  useEffect(() => {
    if (!isActive) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isActive, onClose]);

  const tooltipStyle = useMemo(
    () => getTooltipPosition(targetRect, step?.placement),
    [step?.placement, targetRect],
  );

  if (!isActive || !step) return null;

  const highlightVisible = Boolean(targetRect);

  return createPortal(
    <div className="tour-layer" aria-live="polite">
      <div className="tour-backdrop" onClick={onClose} />

      {highlightVisible && (
        <div
          className="tour-highlight"
          style={{
            top: targetRect.top - 8,
            left: targetRect.left - 8,
            width: targetRect.width + 16,
            height: targetRect.height + 16,
          }}
        />
      )}

      <section
        className="tour-tooltip"
        style={{
          top: tooltipStyle.top,
          left: tooltipStyle.left,
          width: tooltipStyle.width,
        }}
      >
        <div className="tour-step-label">
          Guided Tour · Step {Math.min(stepIndex + 1, totalSteps)} of {totalSteps}
        </div>
        <h2 className="tour-title">{step.title}</h2>
        <p className="tour-body">{step.body}</p>

        {step.target && !highlightVisible && (
          <p className="tour-status">Preparing the next step…</p>
        )}

        <div className="tour-actions">
          <button type="button" className="tour-button tour-button-ghost" onClick={onClose}>
            Skip
          </button>
          <div className="tour-actions-right">
            <button
              type="button"
              className="tour-button tour-button-ghost"
              onClick={onBack}
              disabled={stepIndex === 0}
            >
              Back
            </button>
            <button type="button" className="tour-button tour-button-primary" onClick={() => onNext()}>
              {stepIndex === totalSteps - 1 ? 'Done' : 'Next'}
            </button>
          </div>
        </div>
      </section>
    </div>,
    document.body,
  );
}
