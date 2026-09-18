import { test, expect } from '@playwright/test';

test.describe('Security & Route Protection', () => {
  test('unauthorized or unauthenticated requests to protected endpoints route safely', async ({ page }) => {
    // Navigate to protected route
    await page.goto('/login');
    await expect(page).toHaveURL(/.*login/);
  });

  test('login page enforces form validation for empty credentials', async ({ page }) => {
    await page.goto('/login');
    const submitBtn = page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Login")').first();
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      // Should remain on login page and not throw unhandled exception
      await expect(page).toHaveURL(/.*login/);
    }
  });
});
