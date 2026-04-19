import { expect } from '@playwright/test';

export async function fillBackgroundMemo(page) {
  await page.getByTestId('input-background-subject').fill('Jagello 2000');
  await page.getByTestId('input-background-sections').fill('Overview of Activities\nKey Leadership\nU.S. and NATO Relations');
  await page.getByTestId('input-background-context').fill('Czech defense think tank focused on NATO and transatlantic security.');
}

export async function fillHearingMemo(page) {
  await page.getByTestId('input-hearing-youtube-url').fill('https://www.youtube.com/watch?v=8L0Q1r9wM1Y');
  await page.getByTestId('input-hearing-memo-from').fill('TechForward Alliance');
  await page.getByTestId('input-hearing-memo-date').fill('Monday, April 13, 2026');
  await page.getByTestId('input-hearing-subject-override').fill('Congressional Hearing Memo');
}

export async function fillInfluenceTracker(page) {
  await page.getByTestId('input-influence-entities').fill('OpenAI');
  await page.getByTestId('toggle-influence-source-lda').click();
  await page.getByTestId('toggle-influence-source-lda').click();
}

export async function fillLegislativeTracker(page) {
  await page.getByTestId('input-legislative-query').fill('artificial intelligence');
  await page.getByTestId('input-legislative-year').selectOption('2026');
}

export async function fillMediaClips(page) {
  await page.getByTestId('input-media-clips-topic').fill('India Media Clips');
  await page.getByTestId('input-media-clips-include-keywords').fill('India, elections, Modi');
  await page.getByTestId('input-media-clips-exclude-keywords').fill('cricket, Bollywood');
}

export async function fillMediaList(page) {
  await page.getByTestId('input-media-list-issue').fill('AI safety regulation and mandatory pre-deployment testing requirements');
}

export async function fillMessagingMatrix(page) {
  await page.getByTestId('input-messaging-position').fill('Support the AI Safety and Innovation Act because targeted testing protects consumers without stifling innovation.');
  await page.getByTestId('input-messaging-context').fill('The bill targets frontier systems and provides a compliance safe harbor.');
  await page.getByTestId('input-messaging-organization').fill('TechForward Alliance');
  await page.getByTestId('input-messaging-target-audience').fill('Senate Commerce Committee members');
}

export async function fillStakeholderBriefing(page) {
  await page.getByTestId('input-stakeholder-name').fill('Sen. Maria Cantwell');
  await page.getByTestId('input-stakeholder-organization').fill('U.S. Senate');
  await page.getByTestId('input-stakeholder-meeting-purpose').fill('Discuss support for a federal AI testing and transparency framework.');
}

export async function fillStakeholderMap(page) {
  await page.getByTestId('input-stakeholder-map-policy-issue').fill('AI regulation');
}

export async function sendRemyMessage(page, text) {
  await page.getByTestId('input-remy-message').fill(text);
  await page.getByTestId('submit-remy').click();
}

export async function waitForTerminalStatus(page, statusTestId) {
  const locator = page.getByTestId(statusTestId);
  await expect(locator).toBeVisible();
  await expect.poll(async () => ((await locator.textContent()) || '').toLowerCase(), {
    timeout: 15_000,
  }).toMatch(/completed|failed|processing|pending/);
}
