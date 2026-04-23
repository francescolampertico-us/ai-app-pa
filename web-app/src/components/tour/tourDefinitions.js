export const TOUR_STORAGE_KEY = 'strategitect_guided_tour_completed';

export const REVIEWER_TOUR_ID = 'reviewer-tour';

export const TOUR_DEFINITIONS = {
  [REVIEWER_TOUR_ID]: {
    id: REVIEWER_TOUR_ID,
    label: 'Guided Reviewer Tour',
    steps: [
      {
        id: 'dashboard-overview',
        route: '/app',
        target: 'dashboard-overview',
        title: 'How the prototype is organized',
        body: 'These sections group tools by workflow stage: intelligence gathering, stakeholder preparation, and output creation.',
        placement: 'bottom',
      },
      {
        id: 'dashboard-background-memo',
        route: '/app',
        target: 'background-memo-card',
        title: 'Recommended starting point',
        body: 'Background Memo is the fastest review path because the input is simple and the output shows the system logic clearly.',
        placement: 'right',
      },
      {
        id: 'background-subject',
        route: '/app/background-memo',
        target: 'background-memo-subject',
        title: 'Start with a clear subject',
        body: 'Use an organization, issue, or person. Broad but recognizable entries like "NATO" or "Pfizer" work well for a first run.',
        placement: 'bottom',
      },
      {
        id: 'background-sections',
        route: '/app/background-memo',
        target: 'background-memo-sections',
        title: 'Define the memo structure',
        body: 'Write one section per line. This tells the tool how to organize the briefing instead of changing the underlying research logic.',
        placement: 'right',
      },
      {
        id: 'background-options',
        route: '/app/background-memo',
        target: 'background-memo-options',
        title: 'Optional grounding inputs',
        body: 'Context, source files, and disclosure settings deepen the memo, but they are not required for a simple reviewer demo.',
        placement: 'left',
      },
      {
        id: 'background-submit',
        route: '/app/background-memo',
        target: 'background-memo-submit',
        title: 'Run the pipeline manually',
        body: 'The tour never submits for you. When you are ready, this button starts the backend job with exactly the inputs you entered.',
        placement: 'top',
      },
      {
        id: 'background-output',
        route: '/app/background-memo',
        target: 'background-memo-output',
        title: 'What appears after a run',
        body: 'Status, generated memo content, downloads, and supporting materials show up here. Outputs remain review-required before external use.',
        placement: 'top',
      },
      {
        id: 'tour-complete',
        route: '/app/background-memo',
        title: 'Tour complete',
        body: 'You can now run Background Memo, return to the dashboard, or explore the rest of the toolkit and Remy freely.',
        placement: 'center',
      },
    ],
  },
};
