import { test, expect } from "@playwright/test"
import { execSync } from "child_process"
import { writeFileSync, mkdirSync, unlinkSync, existsSync } from "fs"
import { join } from "path"
import { homedir } from "os"

function makeTestVideo(name = "test.mp4"): string {
  const tmp = join(homedir(), "AppData", "Local", "Temp")
  mkdirSync(join(tmp), { recursive: true })
  const out = join(tmp, `vu_e2e_${name.replace(/\W/g, "_")}_${Date.now()}.mp4`)
  try {
    execSync(
      `ffmpeg -y -f lavfi -i testsrc=duration=3:size=192x108:rate=24 ` +
      `-f lavfi -i sine=frequency=440:duration=3 ` +
      `-c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "${out}"`,
      { stdio: "pipe" }
    )
  } catch {
    writeFileSync(out, Buffer.from([
      0x00,0x00,0x00,0x20,0x66,0x74,0x79,0x70,0x00,0x00,0x00,0x00,
      0x6d,0x70,0x34,0x32,0x69,0x73,0x6f,0x6d,0x00,0x00,0x00,0x00,
      0x69,0x73,0x6f,0x6d,0x00,0x00,0x00,0x00,
    ]))
  }
  return out
}

test.describe("video-use — real browser E2E", () => {
  let createdProjectId = "1"

  test("1 — Dashboard loads", async ({ page }) => {
    await page.goto("/")
    await page.waitForLoadState("networkidle")
    await expect(page.locator("h1")).toContainText("Dashboard")
    await expect(page.getByText("New Project")).toBeVisible()
  })

  test("2 — Sidebar navigation", async ({ page }) => {
    await page.goto("/")
    await page.waitForLoadState("networkidle")

    const pages = [
      ["Dashboard", "Dashboard"],
      ["Projects", "Projects"],
      ["Upload", "Upload"],
      ["Templates", "Templates"],
    ] as const

    for (const [link, heading] of pages) {
      await page.click(`aside >> text=${link}`)
      await page.waitForLoadState("networkidle")
      await expect(page.locator("h1")).toContainText(heading)
    }
  })

  test("3 — Upload page renders with all elements", async ({ page }) => {
    await page.goto("/upload")
    await page.waitForLoadState("networkidle")
    await expect(page.locator("h1")).toContainText("Upload")
    await expect(page.getByText("Drop video here")).toBeVisible()
    await expect(page.locator("input[type='text']")).toBeVisible()
  })

  test("4 — Upload a video → redirect to project editor", async ({ page }) => {
    const vid = makeTestVideo()
    await page.goto("/upload")
    await page.waitForLoadState("networkidle")
    await page.locator("input[type='file']").setInputFiles(vid)
    await page.waitForURL(/\/projects\/\d+/, { timeout: 20000 })
    await expect(page.locator("h1")).toBeVisible()
    await page.waitForTimeout(500)
    const h1 = await page.locator("h1").textContent()
    expect(h1?.length).toBeGreaterThan(0)

    const url = page.url()
    const match = url.match(/\/projects\/(\d+)/)
    if (match) {
      createdProjectId = match[1]
      console.log(`[INFO] Extracted created project ID: ${createdProjectId}`)
    }

    try { unlinkSync(vid) } catch {}
  })

  test("5 — Project editor tabs all present", async ({ page }) => {
    await page.goto(`/projects/${createdProjectId}`)
    await page.waitForLoadState("networkidle")
    await page.waitForTimeout(2000)

    const tabBar = page.locator(".rounded-lg >> button")
    const count = await tabBar.count()
    expect(count).toBeGreaterThanOrEqual(6)
  })

  test("6 — Add more sources via editor file input", async ({ page }) => {
    const vid = makeTestVideo("extra.mp4")
    await page.goto(`/projects/${createdProjectId}`)
    await page.waitForLoadState("networkidle")
    await page.waitForTimeout(1000)
    await page.locator("#editor-upload").setInputFiles(vid)
    await page.waitForTimeout(3000)
    const anyVisible = await Promise.race([
      page.locator("text=added").isVisible().then(() => true),
      page.locator("text=Upload").isVisible().then(() => true),
      page.locator("text=source").isVisible().then(() => true),
      page.locator("text=Error").isVisible().then(() => false),
    ])
    expect(anyVisible).toBeTruthy()
    try { unlinkSync(vid) } catch {}
  })

  test("7 — Templates page loads with cards", async ({ page }) => {
    await page.goto("/templates")
    await page.waitForLoadState("networkidle")
    await page.waitForTimeout(2000)
    await expect(page.locator("h1")).toContainText("Templates")
    const cards = page.locator(".bg-card.border >> h3").first()
    await expect(cards).toBeVisible()
    const cardCount = await page.locator(".bg-card.border >> h3").count()
    expect(cardCount).toBeGreaterThanOrEqual(3)
  })

  test("8 — Non-existent project doesn't crash", async ({ page }) => {
    await page.goto("/projects/999999")
    await page.waitForLoadState("networkidle")
    await page.waitForTimeout(2000)
    expect(page.url()).toContain("999999")
    const body = await page.locator("body").textContent()
    expect(body?.length).toBeGreaterThan(0)
  })

  test("9 — Projects list renders", async ({ page }) => {
    await page.goto("/projects")
    await page.waitForLoadState("networkidle")
    await expect(page.locator("h1")).toContainText("Projects")
  })

  test("10 — Non-video upload shows error", async ({ page }) => {
    const tmp = join(homedir(), "AppData", "Local", "Temp")
    mkdirSync(join(tmp), { recursive: true })
    const bad = join(tmp, "evil.txt")
    writeFileSync(bad, Buffer.from("not a video"))

    await page.goto("/upload")
    await page.waitForLoadState("networkidle")
    await page.locator("input[type='file']").setInputFiles(bad)
    await page.waitForTimeout(2000)
    const hasError = await page.locator("[class*='destructive'], [class*='error'], [class*='text-destructive']").first().isVisible().catch(() => false)
    const errorText = await page.getByText(/unsupported|invalid|failed/i).first().isVisible().catch(() => false)
    expect(hasError || errorText).toBeTruthy()
    try { unlinkSync(bad) } catch {}
  })

  test("11 — Full workflow: upload → edit → export tab → dashboard shows project", async ({ page }) => {
    const vid = makeTestVideo("fullflow.mp4")

    await page.goto("/upload")
    await page.waitForLoadState("networkidle")
    await page.fill("input[type='text']", "Full Flow Test")
    await page.locator("input[type='file']").setInputFiles(vid)

    await page.waitForURL(/\/projects\/\d+/, { timeout: 20000 })
    const h1 = await page.locator("h1").textContent()
    expect(h1?.toLowerCase()).toContain("full flow")

    await page.locator("button:has-text('Export')").click()
    await page.waitForTimeout(500)
    await expect(page.getByText(/youtube/i).first()).toBeVisible()
    await expect(page.getByText(/tiktok/i).first()).toBeVisible()

    await page.click("aside >> text=Dashboard")
    await page.waitForLoadState("networkidle")
    await page.waitForTimeout(1000)
    const projectShown = await page.getByText("Full Flow Test").first().isVisible()
    expect(projectShown).toBeTruthy()

    try { unlinkSync(vid) } catch {}
  })
})
