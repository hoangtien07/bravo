import { expect, test } from "@playwright/test";

test("a live Accounting Work deep link requires a real candidate session", async ({ page }) => {
  await page.goto("/work/cases/not-authorized");
  await expect(page).toHaveURL(/\/login\?next=/);
  await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
  await expect(page.getByText(/Phiên cục bộ của candidate/)).toBeVisible();
});

test("QA fixture route remains isolated and has visual baselines", async ({ browser }) => {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  let accountingRequests = 0;
  desktop.on("request", request => { if (request.url().includes("/api/v2/accounting-cases")) accountingRequests += 1; });
  await desktop.goto("/work?qa=1");
  await expect(desktop.getByRole("heading", { name: "Công việc AI" })).toBeVisible();
  await expect(desktop.getByText(/Route này không gọi AccountingCase API/)).toBeVisible();
  expect(accountingRequests).toBe(0);
  await expect(desktop).toHaveScreenshot("work-qa-desktop.png", { fullPage: true });
  await desktop.close();

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto("/work?qa=1");
  await expect(mobile.getByRole("heading", { name: "Công việc AI" })).toBeVisible();
  await expect(mobile).toHaveScreenshot("work-qa-mobile.png", { fullPage: true });
  await mobile.close();
});
