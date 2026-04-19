import { test, expect } from '@playwright/test';
import { getSurface, loadSurfaceManifest, loadUiFixture } from '../helpers/qaManifest.js';
import { stubArtifactDownloads, stubJson, stubRemyChat, stubToolJob } from '../helpers/network.js';
import {
  fillBackgroundMemo,
  fillHearingMemo,
  fillInfluenceTracker,
  fillLegislativeTracker,
  fillMediaClips,
  fillMediaList,
  fillMessagingMatrix,
  fillStakeholderBriefing,
  fillStakeholderMap,
  sendRemyMessage,
} from '../helpers/pageFlows.js';

const completedFixtureCases = [
  {
    name: 'hearing memo',
    surfaceId: 'hearing_memo_generator',
    fixture: 'hearing_memo_completed',
    fill: fillHearingMemo,
    assertText: 'Verification: PASS',
  },
  {
    name: 'influence tracker',
    surfaceId: 'influence_disclosure_tracker',
    fixture: 'influence_tracker_completed',
    fill: fillInfluenceTracker,
    assertText: 'LDA Data Tables',
  },
  {
    name: 'messaging matrix',
    surfaceId: 'messaging_matrix',
    fixture: 'messaging_matrix_completed',
    fill: fillMessagingMatrix,
    assertText: 'Overarching Message',
  },
  {
    name: 'stakeholder briefing',
    surfaceId: 'stakeholder_briefing',
    fixture: 'stakeholder_briefing_completed',
    fill: fillStakeholderBriefing,
    assertText: 'Key Questions To Ask',
  },
  {
    name: 'stakeholder map',
    surfaceId: 'stakeholder_map',
    fixture: 'stakeholder_map_completed',
    fill: fillStakeholderMap,
    assertText: 'Engagement Priority',
  },
];

test('all routed app surfaces render their declared title test IDs', async ({ page }) => {
  const routedSurfaces = loadSurfaceManifest().filter((surface) => surface.route);

  for (const surface of routedSurfaces) {
    await page.goto(surface.route);
    if (surface.test_ids?.title) {
      await expect(page.getByTestId(surface.test_ids.title)).toBeVisible();
    }
  }
});

test('background memo fixture renders drawers and docx download wiring', async ({ page }) => {
  const surface = getSurface('background_memo_generator');
  const fixture = loadUiFixture('background_memo_completed');

  await stubToolJob(page, 'background_memo_generator', [fixture]);
  await stubArtifactDownloads(page);

  await page.goto(surface.route);
  await fillBackgroundMemo(page);
  await page.getByTestId(surface.test_ids.submit).click();

  await expect(page.getByTestId('status-background-memo')).toContainText('completed');
  await expect(page.getByTestId('drawer-background-research')).toBeVisible();
  await expect(page.getByTestId('drawer-background-disclosures')).toBeVisible();

  const artifactRequest = page.waitForRequest('**/api/jobs/qa-background-completed/artifacts/0');
  await page.getByTestId('download-background-memo-docx').click();
  await artifactRequest;
});

for (const item of completedFixtureCases) {
  test(`${item.name} fixture renders completed state`, async ({ page }) => {
    const surface = getSurface(item.surfaceId);
    await stubToolJob(page, item.surfaceId, [loadUiFixture(item.fixture)]);
    await stubArtifactDownloads(page);
    await page.goto(surface.route);
    await item.fill(page);
    await page.getByTestId(surface.test_ids.submit).click();
    await expect(page.getByText(item.assertText)).toBeVisible();
  });
}

test('legislative tracker fixture supports search followed by summary rendering', async ({ page }) => {
  const surface = getSurface('legislative_tracker');
  const watchlistFixture = {
    id: 'qa-legislative-watchlist',
    status: 'completed',
    progress: 100,
    message: 'Watchlist loaded.',
    created_at: '2026-04-18T12:00:00',
    result_data: {
      action: 'watchlist_list',
      watchlist: [],
      report: ''
    },
    artifacts: []
  };
  const searchFixture = loadUiFixture('legislative_search_completed');
  const summaryFixture = loadUiFixture('legislative_summary_completed');

  await stubToolJob(page, 'legislative_tracker', [watchlistFixture, searchFixture, summaryFixture]);
  await stubArtifactDownloads(page);

  await page.goto(surface.route);
  await fillLegislativeTracker(page);
  await page.getByTestId(surface.test_ids.submit).click();

  await expect(page.getByText('Artificial Intelligence Safety Act')).toBeVisible();
  await page.getByTestId('select-legislative-bill-123').click();
  await page.getByTestId('submit-legislative-detailed-summary').click();

  await expect(page.getByText('Verified source summary generated from official bill text.')).toBeVisible();
  await expect(page.getByTestId('download-legislative-summary')).toBeVisible();
});

test('media clips fixture covers clip generation, cleaner update, report build, and Mail helper', async ({ page }) => {
  const generateFixture = loadUiFixture('media_clips_completed');
  const cleanerFixture = loadUiFixture('media_clip_cleaner_completed');
  const reportFixture = loadUiFixture('media_clips_report_completed');

  await stubToolJob(page, 'media_clips', [generateFixture, reportFixture]);
  await stubToolJob(page, 'media_clip_cleaner', [cleanerFixture, cleanerFixture]);
  await stubArtifactDownloads(page);
  await stubJson(page, '**/api/tools/open-email-draft', { status: 'ok', message: 'Mail.app draft opened.' });

  await page.goto('/app/media-clips');
  await fillMediaClips(page);
  await page.getByTestId('submit-media-clips').click();

  await expect(page.getByText('Found 1 articles. 1 article(s) still need article text review or paste-in.')).toBeVisible();
  await page.getByTestId('input-media-clips-cleaner-raw').fill('Subscription required\n\nIndia trade negotiators said Monday they expect talks with U.S. counterparts to continue this month.');
  await page.getByTestId('submit-media-clips-cleaner').click();
  await expect(page.getByTestId('output-media-clips-cleaner')).toHaveValue(/India trade negotiators said Monday/);

  await page.getByTestId('submit-media-clips-build-report').click();
  await expect(page.getByTestId('download-media-clips-artifact-media_clips_apr18.docx')).toBeVisible();

  await page.getByTestId('input-media-clips-email-to').fill('team@example.com');
  await page.getByTestId('submit-open-email-draft').click();
  await expect(page.getByText('Mail.app opened with draft ready to send.')).toBeVisible();
});

test('media clips review list supports removing an article in the react app', async ({ page }) => {
  const generateFixture = loadUiFixture('media_clips_completed');

  await stubToolJob(page, 'media_clips', [generateFixture]);
  await page.goto('/app/media-clips');
  await fillMediaClips(page);
  await page.getByTestId('submit-media-clips').click();

  await expect(page.getByText('Found 1 articles. 1 article(s) still need article text review or paste-in.')).toBeVisible();
  await page.getByTestId('remove-media-clips-article-0').click();
  await expect(page.getByText('Found 1 articles. 1 article(s) still need article text review or paste-in.')).toHaveCount(0);
  await expect(page.getByText('No matching articles found in the selected 24h window.')).toBeVisible();
});

test('media list fixture renders contacts and pitch helper modal', async ({ page }) => {
  const surface = getSurface('media_list_builder');
  const fixture = loadUiFixture('media_list_completed');
  const pitchFixture = loadUiFixture('pitch_draft_success');

  await stubToolJob(page, 'media_list_builder', [fixture]);
  await stubArtifactDownloads(page);
  await stubJson(page, '**/api/tools/pitch-draft', pitchFixture);

  await page.goto(surface.route);
  await fillMediaList(page);
  await page.getByTestId(surface.test_ids.submit).click();

  await expect(page.getByRole('link', { name: 'Policy Wire' })).toBeVisible();
  await page.getByTestId('open-media-list-pitch-0').click();
  await page.getByTestId('submit-media-list-pitch').click();
  await expect(page.getByTestId('input-media-list-pitch-subject')).toHaveValue('Testing deadline and safe harbor');
});

test('remy fixture renders tool events', async ({ page }) => {
  await stubRemyChat(page, loadUiFixture('remy_chat_success'));

  await page.goto('/app/remy');
  await sendRemyMessage(page, 'Run a background memo on Jagello 2000.');
  await expect(page.getByTestId('remy-tool-event-background_memo_generator')).toBeVisible();
});

test('remy fixture renders rate-limit fallback', async ({ page }) => {
  await stubRemyChat(page, loadUiFixture('remy_chat_rate_limit'));
  await page.goto('/app/remy');
  await sendRemyMessage(page, 'Try again.');
  await expect(page.getByText(/temporarily rate-limited upstream/)).toBeVisible();
});
