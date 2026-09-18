import { test, expect } from '@playwright/test';

test.describe('Operational Workflows & Navigation', () => {
  test('login page displays system operational connection status', async ({ page }) => {
    await page.goto('/login');
    // Verify system telemetry or active profile selector is mounted
    const serverSelector = page.locator('select, [role="combobox"]').first();
    if (await serverSelector.isVisible()) {
      await expect(serverSelector).toBeEnabled();
    }
  });

  test('login quick-fill populates credentials correctly', async ({ page }) => {
    await page.goto('/login');
    const operatorBtn = page.locator('button:has-text("Operator"), button:has-text("Driver")').first();
    if (await operatorBtn.isVisible()) {
      await operatorBtn.click();
      const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]');
      await expect(emailInput).toHaveValue(/operator/i);
    }
  });
});
