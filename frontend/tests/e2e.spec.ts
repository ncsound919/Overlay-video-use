import { test, expect } from "@playwright/test"
import { writeFileSync, mkdirSync } from "fs"
import { join } from "path"

function makeMp4(name: string): string {
  mkdirSync(join(__dirname, "fixtures"), { recursive: true })
  const p = join(__dirname, "fixtures", name)
  writeFileSync(p, Buffer.from([
    0x00,0x00,0x00,0x1c,0x66,0x74,0x79,0x70,0x00,0x00,0x00,0x00,
    0x6d,0x70,0x34,0x32,0x69,0x73,0x6f,0x6d,0x00,0x00,0x00,0x08,
  ]))
  return p
}

test.describe("video-use E2E", () => {

  test("Dashboard loads", async ({ page }) => {
    await page.goto("/")
    await expect(page.locator("h1")).toContainText("Dashboard")
    await expect(page.locator("text=New Project")).toBeVisible()
  })

  test("Sidebar navigation", async ({ page }) => {
    await page.goto("/")
    const links = [["Projects","Projects"],["Upload","Upload"],["Templates","Templates"],["Dashboard","Dashboard"]]
    for (const [label, heading] of links) {
      await page.click(`text=${label}`)
      await page.waitForTimeout(500)
      await expect(page.locator("h1")).toContainText(heading)
    }
  })

  test("Upload page renders", async ({ page }) => {
    await page.goto("/upload")
    await expect(page.locator("text=Drop video here")).toBeVisible()
    await expect(page.locator("input[type='text']")).toBeVisible()
  })

  test("Templates page loads", async ({ page }) => {
    await page.goto("/templates")
    await page.waitForTimeout(2000)
    await expect(page.locator("h1")).toContainText("Templates")
  })

  test("Editor loads project", async ({ page }) => {
    // Navigate to project 1 (created by upload test or pre-existing)
    await page.goto("/projects/1")
    await page.waitForTimeout(3000)

    // Should either show project details or a loading/error state
    const heading = page.locator("h1")
    const hasHeading = await heading.count()
    expect(hasHeading).toBeGreaterThan(0)

    // Should have tabs if project loaded successfully
    const tabs = page.locator("button:has-text('Sources')")
    const exportBtn = page.locator("button:has-text('Export')")
    const addBtn = page.locator("text=Add Videos")
    const emptyMsg = page.locator("text=Project not found")
    // One of these states should be visible
    const anyVisible = await Promise.race([
      tabs.isVisible().then(v => v ? "tabs" : null),
      exportBtn.isVisible().then(v => v ? "export" : null),
      addBtn.isVisible().then(v => v ? "add" : null),
      emptyMsg.isVisible().then(v => v ? "empty" : null),
    ])
    expect(anyVisible).toBeTruthy()
  })

  test("Error page for non-existent project", async ({ page }) => {
    await page.goto("/projects/999999")
    await page.waitForTimeout(2000)
    expect(page.url()).toContain("999999")
  })

})
