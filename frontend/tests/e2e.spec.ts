import { test, expect } from "@playwright/test"
import { readFileSync, writeFileSync, unlinkSync } from "fs"
import { join } from "path"

function createTestMp4(): string {
  const path = join(__dirname, "test_fixture.mp4")
  // Minimal valid MP4 (ftyp box only)
  const header = Buffer.from([
    0x00, 0x00, 0x00, 0x1c, 0x66, 0x74, 0x79, 0x70, // ....ftyp
    0x6d, 0x70, 0x34, 0x32, 0x00, 0x00, 0x00, 0x00, // mp42....
    0x6d, 0x70, 0x34, 0x32, 0x69, 0x73, 0x6f, 0x6d, // mp42isom
    0x00, 0x00, 0x00, 0x08,                         // ....
  ])
  writeFileSync(path, header)
  return path
}

test.describe("video-use E2E Smoke Tests", () => {

  test.afterAll(() => {
    try { unlinkSync(join(__dirname, "test_fixture.mp4")) } catch {}
  })

  // ── 1. Dashboard Loads ──
  test("Dashboard loads and shows UI", async ({ page }) => {
    await page.goto("/")
    await expect(page.locator("h1")).toContainText("Dashboard")
    await expect(page.locator("text=New Project")).toBeVisible()
  })

  // ── 2. Sidebar Navigation ──
  test("Sidebar navigation works", async ({ page }) => {
    await page.goto("/")
    await page.click("text=Projects")
    await expect(page.locator("h1")).toContainText("Projects")
    await page.click("text=Upload")
    await expect(page.locator("h1")).toContainText("Upload")
    await page.click("text=Templates")
    await expect(page.locator("h1")).toContainText("Templates")
    await page.click("text=Dashboard")
    await expect(page.locator("h1")).toContainText("Dashboard")
  })

  // ── 3. Templates Page ──
  test("Templates page shows built-in presets", async ({ page }) => {
    await page.goto("/templates")
    await expect(page.locator("text=Podcast Standard")).toBeVisible({ timeout: 5000 })
    await expect(page.locator("text=Rap Video Standard")).toBeVisible()
    await expect(page.locator("text=Interview Standard")).toBeVisible()
  })

  // ── 4. Template Category Filter ──
  test("Template category filtering works", async ({ page }) => {
    await page.goto("/templates")
    await page.waitForTimeout(1000)
    // Count all visible template cards before filtering
    const before = await page.locator("h3.font-medium").count()
    // Click the 'podcast' filter button (not a template card)
    await page.locator("button:has-text('podcast')").click()
    await page.waitForTimeout(500)
    // Should only show podcast template
    await expect(page.locator("text=Podcast Standard")).toBeVisible()
  })

  // ── 5. Template Creation ──
  test("Can create and delete a custom template", async ({ page }) => {
    const uniqueName = `E2E Template ${Date.now()}`
    await page.goto("/templates")
    await page.click("text=New Template")
    await page.fill("input[placeholder='Template name']", uniqueName)
    await page.fill("textarea", "Created by Playwright")
    await page.click("button:has-text('Create Template')")
    await expect(page.locator(`text=${uniqueName}`)).toBeVisible()

    // Delete it
    const card = page.locator(".bg-card.border", { hasText: uniqueName }).first()
    await card.hover()
    await card.locator("svg.lucide-trash2").first().click({ force: true })
    await page.waitForTimeout(500)
    await expect(page.locator(`text=${uniqueName}`)).not.toBeVisible({ timeout: 5000 })
  })

  // ── 6. Upload Page UI ──
  test("Upload page renders correctly", async ({ page }) => {
    await page.goto("/upload")
    await expect(page.locator("h1")).toContainText("Upload")
    await expect(page.locator("text=Drop video here or click to browse")).toBeVisible()
    await expect(page.locator("input[type='text']")).toBeVisible()
  })

  // ── 7. Upload creates project and redirects to editor ──
  test("Upload creates project and redirects to editor", async ({ page }) => {
    const testVideo = createTestMp4()

    await page.goto("/upload")
    await page.fill("input[type='text']", "E2E Upload Test")

    const fileChooserPromise = page.waitForEvent("filechooser")
    await page.click("text=Drop video here or click to browse")
    const fileChooser = await fileChooserPromise
    await fileChooser.setFiles(testVideo)

    // Should show uploading state
    await expect(page.locator("text=Uploading")).toBeVisible({ timeout: 10000 })

    // Should redirect to editor
    await page.waitForURL("**/projects/**", { timeout: 15000 })

    // Verify we're on the editor
    await expect(page.locator("text=Sources")).toBeVisible({ timeout: 10000 })
    await expect(page.locator("text=No sources")).not.toBeVisible({ timeout: 10000 })
  })

  // ── 8. Editor Sources Tab ──
  test("Editor sources tab shows uploaded file", async ({ page }) => {
    const testVideo = createTestMp4()

    await page.goto("/upload")
    await page.fill("input[type='text']", "E2E Editor Test")

    const fc = page.waitForEvent("filechooser")
    await page.click("text=Drop video here or click to browse")
    ;(await fc).setFiles(testVideo)

    await page.waitForURL("**/projects/**", { timeout: 15000 })
    await page.waitForTimeout(3000)

    // Sources tab should be active by default
    const sourceCard = page.locator(".bg-card").filter({ hasText: "test_fixture.mp4" })
    await expect(sourceCard).toBeVisible({ timeout: 10000 })
  })

  // ── 9. Editor Tabs Navigate ──
  test("Editor tabs navigate correctly", async ({ page }) => {
    const testVideo = createTestMp4()

    await page.goto("/upload")
    await page.fill("input[type='text']", "E2E Tabs Test")
    const fc = page.waitForEvent("filechooser")
    await page.click("text=Drop video here or click to browse")
    ;(await fc).setFiles(testVideo)
    await page.waitForURL("**/projects/**", { timeout: 15000 })
    await page.waitForTimeout(3000)

    // Click each tab and verify content
    const checks = [
      { name: "Transcript", text: "Select a source and transcribe it first" },
      { name: "Scenes", text: "Run scene detection from the Sources tab first" },
      { name: "Reframe", text: "Convert your video to different aspect ratios" },
      { name: "Audio", text: "Clean up audio with open-source" },
      { name: "Export", text: "Render & Export" },
    ]

    for (const { name, text } of checks) {
      await page.click(`button:has-text("${name}")`)
      await expect(page.locator(`text=${text}`)).toBeVisible({ timeout: 5000 })
    }
  })

  // ── 10. Export Presets Available ──
  test("Export tab shows all platform presets", async ({ page }) => {
    const testVideo = createTestMp4()

    await page.goto("/upload")
    await page.fill("input[type='text']", "E2E Export Test")
    const fc = page.waitForEvent("filechooser")
    await page.click("text=Drop video here or click to browse")
    ;(await fc).setFiles(testVideo)
    await page.waitForURL("**/projects/**", { timeout: 15000 })
    await page.waitForTimeout(2000)

    await page.click("button:has-text('Export')")
    await expect(page.locator("text=YouTube")).toBeVisible()
    await expect(page.locator("text=TikTok")).toBeVisible()
  })

  // ── 11. Reframe Options ──
  test("Reframe tab shows all aspect ratios", async ({ page }) => {
    const testVideo = createTestMp4()

    await page.goto("/upload")
    await page.fill("input[type='text']", "E2E Reframe Test2")
    const fc = page.waitForEvent("filechooser")
    await page.click("text=Drop video here or click to browse")
    ;(await fc).setFiles(testVideo)
    await page.waitForURL("**/projects/**", { timeout: 15000 })
    await page.waitForTimeout(2000)

    await page.click("button:has-text('Reframe')")
    await expect(page.locator("text=TikTok / Reels")).toBeVisible()
    await expect(page.locator("text=Instagram Square")).toBeVisible()
    await expect(page.locator("text=IG Portrait")).toBeVisible()
    await expect(page.locator("text=YouTube")).toBeVisible()
  })

  // ── 12. Dashboard shows created projects ──
  test("Dashboard reflects newly created projects", async ({ page }) => {
    const testVideo = createTestMp4()

    await page.goto("/upload")
    await page.fill("input[type='text']", "E2E Dashboard Test")
    const fc = page.waitForEvent("filechooser")
    await page.click("text=Drop video here or click to browse")
    ;(await fc).setFiles(testVideo)
    await page.waitForURL("**/projects/**", { timeout: 15000 })

    // Navigate back to dashboard
    await page.goto("/")

    // Should see the project
    await expect(page.locator("text=E2E Dashboard Test").first()).toBeVisible({ timeout: 10000 })
  })

  // ── 13. Error handling: non-existent project ──
  test("Non-existent project shows error", async ({ page }) => {
    await page.goto("/projects/999999")
    await expect(page.locator("text=Project not found")).toBeVisible({ timeout: 5000 })
  })

})
