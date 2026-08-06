import { expect, test } from "@playwright/test";
import axe from "axe-core";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const makerEmail = process.env.DEMO18_MAKER_EMAIL;
const reviewerEmail = process.env.DEMO18_REVIEWER_EMAIL;
const password = process.env.DEMO18_PASSWORD;
const enabled = Boolean(makerEmail && reviewerEmail && password);
const visualEvidence = resolve(fileURLToPath(new URL("../..", import.meta.url)), "evidence", "v2");
const visualViewports = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1024x768", width: 1024, height: 768 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "390x844", width: 390, height: 844 },
] as const;

async function expectNoCriticalAxe(page: import("@playwright/test").Page) {
  await page.addScriptTag({ content: axe.source });
  const critical = await page.evaluate(async () => {
    const result = await (window as unknown as { axe: typeof axe }).axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] } });
    return result.violations.filter(item => item.impact === "critical").map(item => item.id);
  });
  expect(critical).toEqual([]);
}

async function login(page: import("@playwright/test").Page, email: string) {
  await page.goto("/login?next=%2F");
  await expectNoCriticalAxe(page);
  await page.getByLabel("Email").fill(email);
  await page.getByRole("textbox", { name: "Mật khẩu" }).fill(password!);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page).toHaveURL(/\/$/);
}

test.describe("local synthetic live demo", () => {
  test.skip(!enabled, "Run through scripts/run_demo18_live_browser.py; credentials are intentionally not a test source value.");

  test("maker completes live Chat, durable reload, and read-only share", async ({ page, context }) => {
    await login(page, makerEmail!);
    await page.getByLabel("What do you need to know?").fill("Quy trình đối chiếu ngân hàng BRAVO gồm những bước nào?");
    await page.getByRole("button", { name: "Send question" }).click();
    await expect(page).toHaveURL(/\/c\//);
    await expect(page.getByRole("button", { name: "Share" })).toBeEnabled({ timeout: 90_000 });
    await page.reload();
    await expect(page.getByRole("button", { name: "Share" })).toBeEnabled();
    await expectNoCriticalAxe(page);
    const attachment = page.locator('input[type="file"]');
    await expect(attachment).toHaveCount(1);
    await attachment.setInputFiles("e2e/fixtures/demo18-note.txt");
    await expect(page.getByText("demo18-note.txt", { exact: false })).toBeVisible();
    await page.getByPlaceholder("Ask a follow-up question").fill("Tóm tắt tệp đính kèm và nêu rõ giới hạn thực thi.");
    await page.getByRole("button", { name: "Send" }).click();
    const citationButtons = page.getByLabel("Evidence Rail").locator("ol button");
    await expect(citationButtons).not.toHaveCount(0, { timeout: 90_000 });
    const citationCount = await citationButtons.count();
    await citationButtons.nth(citationCount - 1).click();
    await expect(page.getByText("Selected citation:", { exact: false })).toBeVisible();
    const feedback = page.getByRole("button", { name: "Helpful answer" });
    await expect(feedback).not.toHaveCount(0);
    await feedback.nth((await feedback.count()) - 1).click();
    await expect(page.getByRole("button", { name: "Stop" })).toHaveCount(0, { timeout: 90_000 });
    await expect(page.getByText("BRAVO is responding", { exact: true })).toHaveCount(0);
    for (const viewport of visualViewports) {
      await page.setViewportSize(viewport);
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: resolve(visualEvidence, `DEMO18-chat-${viewport.name}-light.png`), fullPage: true });
    }
    await page.goto(`${new URL(page.url()).pathname}?theme=dark`);
    await expect(page.getByRole("button", { name: "Share" })).toBeEnabled();
    for (const viewport of visualViewports) {
      await page.setViewportSize(viewport);
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: resolve(visualEvidence, `DEMO18-chat-${viewport.name}-dark.png`), fullPage: true });
    }
    await page.goto(new URL(page.url()).pathname);
    await expect(page.getByRole("button", { name: "Share" })).toBeEnabled();
    await page.getByRole("button", { name: "Mở điều hướng" }).click();
    await expect(page.getByRole("dialog", { name: "Điều hướng" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog", { name: "Điều hướng" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Mở điều hướng" })).toBeFocused();
    await page.getByRole("button", { name: "Share" }).click();
    const shared = page.getByText(/^Read-only link:/);
    await expect(shared).toBeVisible();
    const href = (await shared.textContent())?.replace("Read-only link:", "").trim();
    expect(href).toMatch(/^\/shared\//);
    const sharedPage = await context.newPage();
    await sharedPage.goto(href!);
    await expect(sharedPage.getByText("BRAVO · READ-ONLY SHARE")).toBeVisible();
    await expect(sharedPage.getByRole("button", { name: "Share" })).toHaveCount(0);
    await expectNoCriticalAxe(sharedPage);
    await sharedPage.close();
  });

  test("maker and independent reviewer complete all three browser case lifecycles", async ({ browser }) => {
    test.setTimeout(120_000);
    const maker = await browser.newContext(); const reviewer = await browser.newContext();
    const makerPage = await maker.newPage(); const reviewerPage = await reviewer.newPage();
    await login(makerPage, makerEmail!); await login(reviewerPage, reviewerEmail!);
    const casePaths: string[] = [];
    for (const type of ["bank_reconciliation", "voucher_evidence_review", "period_close_readiness"]) {
      await makerPage.goto(`/work/new/${type}`);
      await makerPage.getByRole("button", { name: "Khóa phạm vi và tạo case" }).click();
      await expect(makerPage).toHaveURL(/\/work\/cases\//);
      await makerPage.getByRole("button", { name: "Nạp bằng chứng" }).click();
      await expect(makerPage.getByRole("button", { name: "Chạy kiểm tra" })).toBeVisible();
      await makerPage.getByRole("button", { name: "Chạy kiểm tra" }).click();
      await expect(makerPage.getByLabel("Evidence Rail").getByText("Chờ rà soát", { exact: true })).toBeVisible();
      casePaths.push(new URL(makerPage.url()).pathname);
    }
    for (const path of casePaths) {
      await reviewerPage.goto(path);
      await reviewerPage.getByRole("button", { name: "Rà soát" }).click();
      await reviewerPage.getByRole("button", { name: "Gửi review packet" }).click();
      await expect(reviewerPage.getByLabel("Evidence Rail").getByText("Đã rà soát", { exact: true })).toBeVisible();
      await reviewerPage.getByRole("button", { name: "Xuất", exact: true }).click();
      await reviewerPage.getByRole("button", { name: "Xuất review artifact" }).click();
      await expect(reviewerPage.getByLabel("Evidence Rail").getByText("Đã xuất artifact", { exact: true })).toBeVisible();
      await expect(reviewerPage.locator("pre").filter({ hasText: "artifact_produced_not_executed" })).toBeVisible();
      await expectNoCriticalAxe(reviewerPage);
    }
    await maker.close(); await reviewer.close();
  });
});
