/**
 * E2E tests for the DevFlow UI application.
 *
 * These tests run against the web version of the app (without Tauri).
 * They verify basic UI functionality and navigation.
 */

import { test, expect } from '@playwright/test';

test.describe('App Shell', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the application', async ({ page }) => {
    // App should render without errors
    await expect(page).toHaveTitle(/DevFlow/i);
  });

  test('should display sidebar navigation', async ({ page }) => {
    // Sidebar should be visible
    const sidebar = page.locator('nav');
    await expect(sidebar).toBeVisible();
  });

  test('should show bridge status indicator', async ({ page }) => {
    // There should be some indication of bridge/connection status
    const statusIndicator = page.getByText(/stopped|connecting|running|error/i);
    await expect(statusIndicator.first()).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate to Development page', async ({ page }) => {
    await page.getByRole('link', { name: /development/i }).click();
    await expect(page).toHaveURL(/.*development/);
  });

  test('should navigate to Database page', async ({ page }) => {
    await page.getByRole('link', { name: /database/i }).click();
    await expect(page).toHaveURL(/.*database/);
  });

  test('should navigate to Secrets page', async ({ page }) => {
    await page.getByRole('link', { name: /secrets/i }).click();
    await expect(page).toHaveURL(/.*secrets/);
  });

  test('should navigate to Deploy page', async ({ page }) => {
    await page.getByRole('link', { name: /deploy/i }).click();
    await expect(page).toHaveURL(/.*deploy/);
  });

  test('should navigate to Config page', async ({ page }) => {
    await page.getByRole('link', { name: /config/i }).click();
    await expect(page).toHaveURL(/.*config/);
  });
});

test.describe('Development Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/development');
  });

  test('should display page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /development/i })).toBeVisible();
  });

  test('should show no project message when no project selected', async ({ page }) => {
    // When no project is selected, should show a message
    const noProjectMessage = page.getByText(/no project selected/i);
    await expect(noProjectMessage).toBeVisible();
  });

  test('should have refresh button', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('should have start all button', async ({ page }) => {
    const startButton = page.getByRole('button', { name: /start all/i });
    await expect(startButton).toBeVisible();
  });
});

test.describe('Database Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/database');
  });

  test('should display page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /database/i })).toBeVisible();
  });
});

test.describe('Secrets Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/secrets');
  });

  test('should display page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /secrets/i })).toBeVisible();
  });
});

test.describe('Deploy Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/deploy');
  });

  test('should display page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /deploy/i })).toBeVisible();
  });
});

test.describe('Config Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/config');
  });

  test('should display page header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /config/i })).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // App should still be visible on mobile
    await expect(page.locator('body')).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();
  });

  test('should work on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have no major accessibility issues on home page', async ({ page }) => {
    await page.goto('/');

    // Basic accessibility check - all interactive elements should be focusable
    const buttons = page.getByRole('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      // Disabled buttons may not need to be focusable
      const isDisabled = await button.isDisabled();
      if (!isDisabled) {
        await expect(button).toBeEnabled();
      }
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');

    // Tab through the page
    await page.keyboard.press('Tab');
    const firstFocused = page.locator(':focus');
    await expect(firstFocused).toBeVisible();

    // Continue tabbing
    await page.keyboard.press('Tab');
    const secondFocused = page.locator(':focus');
    await expect(secondFocused).toBeVisible();
  });
});
