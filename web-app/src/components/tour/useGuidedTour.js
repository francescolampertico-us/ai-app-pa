import { useContext } from 'react';
import { GuidedTourContext } from './GuidedTourContext';

export function useGuidedTour() {
  const context = useContext(GuidedTourContext);
  if (!context) {
    throw new Error('useGuidedTour must be used within a GuidedTourProvider');
  }
  return context;
}
