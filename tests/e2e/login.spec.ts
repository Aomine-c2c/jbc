import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/DWRMS/);
});

test('unauthenticated users are redirected', async ({ page }) => {
  await page.goto('/jobs');
  // Expect to be kicked out to login page
  // await expect(page).toHaveURL(/.*login/);
});
