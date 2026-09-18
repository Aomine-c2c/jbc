import { test, expect } from '@playwright/test';

test.describe('Authentication & Landing', () => {
  test('landing page loads and has application title', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/DWRMS/i);
  });

  test('login page presents all operational persona quick-login selectors', async ({ page }) => {
    await page.goto('/login');

    // Verify main branding is visible
    await expect(page.locator('text=BIKITA MINERALS')).toBeVisible();

    // Verify login form inputs
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();

    // Verify quick login buttons for operational personas exist
    await expect(page.locator('button:has-text("Operator"), button:has-text("Driver")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Tech"), button:has-text("Artisan")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Supervisor")').first()).toBeVisible();
    await expect(page.locator('button:has-text("Admin")').first()).toBeVisible();
  });
});
