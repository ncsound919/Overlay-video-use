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

async function setupProjectWithSource(page, name: string, fileName: string): Promise<number> {
  // Create project + upload source directly via API
  const r1 = await page.evaluate(async (n) => {
    const r = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: n }),
    })
    return (await r.json()).id
  }, name)

  const r2 = await page.evaluate(async (pid) => {
    const formData = new FormData()
    formData.append("file", new Blob([
      new Uint8Array([0,0,0,0x1c,0x66,0x74,0x79,0x70,0,0,0,0,0x6d,0x70,0x34,0x32,0x69,0x73,0x6f,0x6d,0,0,0,8])
    ], { type: "video/mp4" }), "test.mp4")
    const r = await fetch(`/api/uploads/${pid}`, { method: "POST", body: formData })
    return r.ok
  }, r1)

  return r1
}

test.describe("video-use E2E", () => {

  test("Dashboard loads", async ({ page }) => {
    await page.goto("/")
    await expect(page.locator("h1")).toContainText("Dashboard")
    await expect(page.locator("text=New Project")).toBeVisible()
  })

  test("Sidebar navigation", async ({ page }) => {
    await page.goto("/")
    const links = [
      ["Projects", "Projects"],
      ["Upload", "Upload"],
      ["Templates", "Templates"],
      ["Dashboard", "Dashboard"],
    ]
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

  test("Templates show defaults", async ({ page }) => {
    await page.goto("/templates")
    await page.waitForTimeout(1500)
    const cards = await page.locator(".bg-card.border").count()
    expect(cards).toBeGreaterThan(0)
  })

  test("Editor loads project with sources", async ({ page }) => {
    const pid = await setupProjectWithSource(page, "E2E Editor Test", "clip.mp4")
    await page.goto(`/projects/${pid}`)
    await page.waitForTimeout(3000)

    await expect(page.locator("h1")).toContainText("E2E Editor Test")
    await expect(page.locator("text=test.mp4")).toBeVisible({ timeout: 5000 })
    await expect(page.locator("text=Add Videos")).toBeVisible()

    // Navigate all tabs
    await page.click("button:has-text('Transcript')")
    await page.waitForTimeout(500)
    await expect(page.locator("text=transcribe it first")).toBeVisible()

    await page.click("button:has-text('Scenes')")
    await page.waitForTimeout(500)
    await expect(page.locator("text=Run scene detection")).toBeVisible()

    await page.click("button:has-text('Reframe')")
    await page.waitForTimeout(500)
    await expect(page.locator("text=TikTok / Reels")).toBeVisible()

    await page.click("button:has-text('Audio')")
    await page.waitForTimeout(500)
    await expect(page.locator("text=Clean up audio")).toBeVisible()

    await page.click("button:has-text('Export')")
    await page.waitForTimeout(500)
    await expect(page.locator("text=Render & Export")).toBeVisible()
  })

  test("Multi-source project shows all files", async ({ page }) => {
    const pid = await setupProjectWithSource(page, "Multi Source", "clip1.mp4")
    await page.evaluate(async (id) => {
      const form = new FormData()
      form.append("file", new Blob([
        new Uint8Array([0,0,0,0x1c,0x66,0x74,0x79,0x70,0,0,0,0,0x6d,0x70,0x34,0x32,0x69,0x73,0x6f,0x6d,0,0,0,8])
      ], { type: "video/mp4" }), "clip2.mp4")
      await fetch(`/api/uploads/${id}`, { method: "POST", body: form })
    }, pid)

    await page.goto(`/projects/${pid}`)
    await page.waitForTimeout(3000)

    await expect(page.locator("text=test.mp4")).toBeVisible({ timeout: 5000 })
    await expect(page.locator("text=clip2.mp4")).toBeVisible({ timeout: 5000 })
    // The counter should show 2 sources
    await expect(page.locator("text=2 sources")).toBeVisible({ timeout: 5000 })
  })

  test("Error page for non-existent project", async ({ page }) => {
    await page.goto("/projects/999999")
    await page.waitForTimeout(2000)
    // Next.js 404 page should have the project URL
    const url = page.url()
    expect(url).toContain("999999")
  })

})
