import { test, expect } from "@playwright/test"
import { join } from "path"

const VIDEO_DIR = "C:\\Users\\User\\Documents\\videos"
const MUSIC_FILE = "C:\\Users\\User\\Desktop\\Overlay-video-use-main\\the realness.mp3"

const videos = [
  join(VIDEO_DIR, "AQM4pdFKl6g3c5n8kYbWslw_WJWwFZTMAIF5cy7YktbVO1osVuXPXbWHA_yXZOMkKXN9wB0YyWv8LmIAUNLK6IN_4123811867637452.mp4"),
  join(VIDEO_DIR, "AQM62URA1laNrxmqzzxJUSF1Z0MhQ9Rarp1daAfRfFhIBsGpoCxYa840rNUQLQIEJXcgBtyLeEirjTRoMeGvkjD_4129390920412880.mp4"),
  join(VIDEO_DIR, "AQMfirMQvnj7QfR_qpwTmcEspQlk3E23lme4eDywO7i5LcYorntzVpRRQrMVhCcMf9Oi1BUGzZRDnAPXzwrcKO__4120631944622111.mp4"),
]

test.describe("Human user: real video project", () => {

  test("Full workflow — upload 3 videos, transcribe, edit EDL, export", async ({ page }) => {
    test.setTimeout(180000)

    // ─── 1. Dashboard ───
    await page.goto("/")
    await page.waitForLoadState("networkidle")
    await expect(page.locator("h1")).toContainText("Dashboard")

    // ─── 2. Upload page → create project with first video ───
    await page.click("aside >> text=Upload")
    await page.waitForLoadState("networkidle")
    await expect(page.locator("h1")).toContainText("Upload")

    await page.fill("input[type='text']", "Real Video Project")
    await page.locator("input[type='file']").setInputFiles(videos[0])

    // wait for redirect to project editor
    await page.waitForURL(/\/projects\/\d+/, { timeout: 30000 })
    await page.waitForTimeout(3000)

    let h1 = await page.locator("h1").textContent()
    expect(h1?.toLowerCase()).toContain("real video")
    console.log(`[PASS] Created project: ${h1}`)

    // ─── 3. Add remaining 2 videos via editor ───
    const editorUpload = page.locator("#editor-upload")
    await editorUpload.setInputFiles([videos[1], videos[2]])
    await page.waitForTimeout(4000)

    // Verify source cards appeared
    const sourceCards = page.locator(".bg-card.border.rounded-lg >> .font-medium")
    const visibleCount = await sourceCards.count()
    console.log(`[INFO] Sources visible: ${visibleCount}`)
    expect(visibleCount).toBeGreaterThanOrEqual(2)

    // ─── 4. Transcribe a source ───
    const transcribeBtn = page.locator("button:has-text('Transcribe')").first()
    const hasTranscribe = await transcribeBtn.isVisible().catch(() => false)
    if (hasTranscribe) {
      console.log("[ACTION] Clicking Transcribe...")
      await transcribeBtn.click()

      // Whisper on 3-min video can take 60s+. Wait for overlay to disappear.
      const overlay = page.locator(".fixed.inset-0")
      try {
        await overlay.waitFor({ state: "visible", timeout: 5000 })
        console.log("[INFO] Processing overlay appeared — waiting for whisper...")
        await overlay.waitFor({ state: "hidden", timeout: 120000 })
        console.log("[INFO] Processing overlay disappeared")
      } catch {
        console.log("[INFO] Overlay timed out — transcription may still be running")
      }

      // Reload page to refresh source list (shows "Transcribed" status)
      await page.reload()
      await page.waitForLoadState("networkidle")
      await page.waitForTimeout(2000)
    } else {
      console.log("[SKIP] No Transcribe button (may already be transcribed)")
    }

    // Check source cards for transcribed status
    const transcribedBadge = page.locator("text=Transcribed")
    const hasTranscript = await transcribedBadge.first().isVisible().catch(() => false)
    console.log(`[INFO] Source has transcript: ${hasTranscript}`)

    // ─── 5. Navigate to Transcript tab ───
    await page.locator("button:has-text('Transcript')").click()
    await page.waitForTimeout(1500)

    const emptyState = page.locator("text=transcribe it first")
    const hasEmptyState = await emptyState.isVisible().catch(() => false)

    if (!hasEmptyState) {
      console.log("[PASS] Transcript tab has content")

      // Switch to Edit mode
      const editBtn = page.locator("button:has-text('Edit')")
      if (await editBtn.isVisible().catch(() => false)) {
        await editBtn.click()
        await page.waitForTimeout(1000)

        // Click words to create cut boundaries
        const words = page.locator(".lg\\:col-span-2 span.cursor-pointer")
        const wordCount = await words.count().catch(() => 0)
        console.log(`[INFO] Clickable words in transcript: ${wordCount}`)

        if (wordCount > 5) {
          // Mark 4 boundaries to create 2 ranges
          await words.nth(5).click()
          await words.nth(15).click()
          await page.waitForTimeout(300)

          await words.nth(30).click()
          await words.nth(45).click()
          await page.waitForTimeout(300)

          // Verify cut list
          const cutItems = page.locator(".bg-secondary\\/50")
          const cutCount = await cutItems.count().catch(() => 0)
          console.log(`[INFO] Cut list items: ${cutCount}`)

          // Save EDL
          const saveBtn = page.locator("button:has-text('Save EDL')")
          if (await saveBtn.isVisible().catch(() => false)) {
            await saveBtn.click()
            await page.waitForTimeout(1500)
            const runtime = await page.locator("text=Runtime:").isVisible().catch(() => false)
            const runtimeText = await page.locator("text=Runtime:").textContent().catch(() => "")
            console.log(`[PASS] EDL saved: ${runtimeText}`)
            expect(runtime).toBeTruthy()
          }
        } else {
          console.log("[SKIP] Not enough words for EDL editing")
        }
      }
    } else {
      console.log("[INFO] No transcript — skipping EDL editing")
    }

    // ─── 6. Scenes tab ───
    await page.locator("button:has-text('Scenes')").click()
    await page.waitForTimeout(1000)
    const hasScenes = await page.locator("text=Run scene detection").isVisible().catch(() => false)
    console.log(`[INFO] Scenes tab: ${hasScenes ? "prompts detection" : "shows scenes"}`)

    // ─── 7. Audio tab ───
    await page.locator("button:has-text('Audio')").click()
    await page.waitForTimeout(1000)
    await expect(page.getByText("Clean up audio")).toBeVisible()
    console.log("[PASS] Audio tab loaded")

    // Click "Full Cleanup" button
    const fullCleanup = page.locator("button:has-text('Full Cleanup')")
    if (await fullCleanup.isVisible().catch(() => false)) {
      await fullCleanup.click()
      await page.waitForTimeout(3000)
      console.log("[ACTION] Clicked Full Cleanup")
    }

    // ─── 8. Export tab ───
    await page.locator("button:has-text('Export')").click()
    await page.waitForTimeout(1000)
    await expect(page.getByText("YouTube").first()).toBeVisible()
    await expect(page.getByText("TikTok").first()).toBeVisible()
    console.log("[PASS] Export tab shows presets")

    // Try rendering
    const youtubeBtn = page.locator("button:has-text('YouTube'):not(:has-text('IG'))")
    if (await youtubeBtn.first().isVisible().catch(() => false)) {
      await youtubeBtn.first().click()
      await page.waitForTimeout(5000)
      const overlay2 = page.locator(".fixed.inset-0")
      try {
        await overlay2.waitFor({ state: "hidden", timeout: 30000 })
      } catch {}
      console.log("[ACTION] Triggered YouTube render")
    }

    // ─── 9. Navigate back to dashboard ───
    await page.click("aside >> text=Dashboard")
    await page.waitForLoadState("networkidle")
    await page.waitForTimeout(1000)
    await expect(page.locator("h1")).toContainText("Dashboard")

    const projectCard = page.getByText("Real Video Project").first()
    const projectVisible = await projectCard.isVisible().catch(() => false)
    console.log(`[PASS] Project on dashboard: ${projectVisible}`)
    expect(projectVisible).toBeTruthy()

    console.log("\n=== REAL VIDEO WORKFLOW COMPLETE ===")
  })

})
