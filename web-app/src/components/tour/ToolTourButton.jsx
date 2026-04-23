import { CompassIcon as Compass } from '@phosphor-icons/react';
import { useGuidedTour } from './useGuidedTour';

export default function ToolTourButton({ tourId, label = 'Tour This Tool' }) {
  const { startTour } = useGuidedTour();

  return (
    <button type="button" className="tour-launch-button" onClick={() => startTour(tourId)}>
      <Compass size={14} weight="bold" />
      {label}
    </button>
  );
}
