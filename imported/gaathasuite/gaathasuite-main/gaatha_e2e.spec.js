const { test, expect } = require('@playwright/test');

test('Gaatha Suite login -> dashboard -> CRM -> logout', async ({ page }) => {
  await page.goto('http://localhost:5000/auth/login', { waitUntil: 'networkidle', timeout: 30000 });
  await page.getByLabel('Username').fill('admin@example.com');
  await page.getByLabel('Password').fill('ChangeThisSuperAdminPassword!');
  await page.getByRole('button', { name: 'Login' }).click();

  await expect(page).toHaveURL(/\/superadmin\/dashboard|\/dashboard/, { timeout: 30000 });

  await page.goto('http://localhost:5000/crm', { waitUntil: 'networkidle', timeout: 30000 });
  await expect(page.getByText('Sales Pipeline')).toBeVisible({ timeout: 30000 });

  await page.getByRole('button', { name: /Add New Lead/i }).click();
  const leadName = 'Browser QA Lead ' + Date.now();
  await page.getByPlaceholder('Enter lead name').fill(leadName);
  await page.getByPlaceholder('Enter company name').fill('Playwright Pilot');
  await page.getByPlaceholder('Enter email address').fill('qa+' + Date.now() + '@example.com');
  await page.getByRole('button', { name: 'Create Lead' }).click();

  await expect(page.getByText(leadName, { exact: false })).toBeVisible({ timeout: 30000 });

  await page.getByRole('button', { name: /Logout/i }).click();
  await expect(page).toHaveURL(/\/auth\/login/, { timeout: 30000 });
});
