import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const INCIDENT = "Someone called saying my electricity would be cut tonight. Around 4:10 PM today Rs 49,999 was debited from my SBI account XX2234 via UPI, then Rs 25,000 at 4:14 PM. UPI Ref No 524587920123 and Ref: 524587920456. Money went to rajesh.kumar77@okaxis. Caller +91 98765 43210. My number is 9123456789.";

test("E2E-01 checker explains a scam", async ({ page }) => {
  await page.goto("/check");
  await page.getByRole("button", { name: "Parcel call" }).click();
  await expect(page.getByRole("heading", { name: "Very likely a scam" })).toBeVisible();
  await expect(page.locator("mark.hit").first()).toBeVisible();
  expect(await page.locator(".reason").count()).toBeGreaterThanOrEqual(3);
  await expect(page.getByRole("link", { name: "Call 1930" })).toHaveAttribute("href", "tel:1930");
});

test("E2E-02/03 emergency flow: Mode A script is Tier 1 only, Mode B has everything", async ({ page }) => {
  await page.goto("/lost/tell");
  await page.fill("#narr", INCIDENT);
  await page.getByLabel("About 30 minutes ago").check();
  await expect(page.locator(".chips-found")).toContainText("₹49,999");
  await expect(page.locator(".chips-found")).toContainText("₹25,000");
  await page.getByRole("button", { name: "Next" }).click();
  await page.fill("#f-name", "Zed Qwerty");
  await page.fill("#f-location", "Kothrud Pune");
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("button", { name: "Next" }).click();
  const script = page.getByRole("tabpanel");
  await expect(script).toContainText("524587920123");
  await expect(script).toContainText("UTR 524587920456: ₹25,000");
  await expect(script).not.toContainText("Zed Qwerty");
  await expect(script).not.toContainText("Kothrud");
  await page.getByRole("button", { name: "Back" }).click();
  await page.getByRole("button", { name: /B: Portal only/ }).click();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("tabpanel")).toContainText("Zed Qwerty");
});

test("E2E-04 missing UTR: flow continues, pack lists it as missing", async ({ page }) => {
  await page.goto("/lost/tell");
  await page.fill("#narr", "I paid Rs 500 to a stranger yesterday");
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("tabpanel")).toContainText("find it in your bank or UPI app");
});

test("deep link to a later step redirects to the start", async ({ page }) => {
  await page.goto("/lost/pack");
  await expect(page).toHaveURL(/\/lost\/tell/);
});

test("only our own server is contacted; ledger lists requests without content", async ({ page }) => {
  const hosts = new Set<string>();
  page.on("request", (r) => hosts.add(new URL(r.url()).host));
  await page.goto("/check");
  await page.getByRole("button", { name: "Bank KYC SMS" }).click();
  await expect(page.getByRole("heading", { name: "Very likely a scam" })).toBeVisible();
  expect([...hosts]).toEqual(["localhost:5173"]);
  await page.getByRole("button", { name: /Privacy Ledger/ }).click();
  const list = page.getByTestId("ledger-list");
  await expect(list).toContainText("/v1/check");
  await expect(list).not.toContainText("KYC");
});

test("E2E-06 delete everything clears storage", async ({ page }) => {
  await page.goto("/settings");
  await page.evaluate(() => { localStorage.setItem("x", "1"); sessionStorage.setItem("y", "1"); });
  await page.getByRole("button", { name: "Delete everything now" }).click();
  expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
});

test("E2E-07 Hindi UI", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "हिं" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("नमस्ते");
  await page.goto("/check");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("संदेश जाँचें");
});

test("E2E-08 reduced motion stops animations", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator(".halo-shimmer, .breathe")).toHaveCount(0);
});

test("Ask answers from the KB with sources, and says so when unknown", async ({ page }) => {
  await page.goto("/ask");
  await page.getByRole("button", { name: "What is a UTR?" }).click();
  await expect(page.locator(".chat .card").first()).toContainText("12-digit");
  await expect(page.locator(".src a").first()).toBeVisible();
  await page.fill("#q", "best pizza near me");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.locator(".chat").first()).toContainText("don't have a verified answer");
});

for (const path of ["/", "/check", "/lost/tell", "/ask", "/settings"]) {
  for (const theme of ["light", "dark"]) {
    test(`E2E-12 axe ${path} ${theme}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: theme as "light" | "dark" });
      await page.goto(path);
      await page.waitForTimeout(500);
      const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag22aa"]).analyze();
      expect(r.violations.filter((v) => v.impact === "serious" || v.impact === "critical"), JSON.stringify(r.violations.map((v) => [v.id, v.nodes[0]?.html]))).toEqual([]);
    });
  }
}
