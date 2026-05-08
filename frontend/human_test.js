const { chromium } = require("@playwright/test")

async function main() {
  const browser = await chromium.launch({ headless: false, slowMo: 200 })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const BASE = "http://localhost:3002"

  // 1. DASHBOARD
  console.log("1. Dashboard")
  await page.goto(BASE)
  await page.waitForTimeout(1500)
  console.log("   URL:", page.url())

  // 2. SIDEBAR - click Upload
  console.log("2. Click Upload in sidebar")
  await page.click("text=Upload")
  await page.waitForTimeout(1000)
  console.log("   URL:", page.url())

  // 3. UPLOAD PAGE - fill name
  console.log("3. Fill project name")
  await page.fill("input[type='text']", "Human Walkthrough Demo")
  await page.waitForTimeout(300)

  // 4. CLICK DROPZONE to open file dialog
  console.log("4. Click upload area")
  const [fc] = await Promise.all([
    page.waitForEvent("filechooser"),
    page.locator(".border-dashed").click(),
  ])

  // 5. SELECT A REAL MP4
  console.log("5. Select test video file")
  await fc.setFiles(__dirname + "/tests/fixtures/journey1.mp4")

  // 6. WAIT FOR REDIRECT
  console.log("6. Waiting for redirect to editor...")
  await page.waitForURL(/\/projects\/\d+/, { timeout: 20000 })
  await page.waitForTimeout(3000)
  console.log("   URL:", page.url())
  console.log("   H1:", await page.locator("h1").textContent())

  // 7. EDITOR - check what we see
  console.log("7. Editor content:")
  const body = (await page.locator("body").textContent()) || ""
  console.log("   Has 'Add Videos':", body.includes("Add Videos"))
  console.log("   Has 'journey1.mp4':", body.includes("journey1.mp4"))
  console.log("   Has '0:00':", body.includes("0:00"))
  console.log("   Has 'Pending':", body.includes("Pending"))

  // 8. LIST TABS
  const tabLabels = ["Sources", "Transcript", "Scenes", "Reframe", "Audio", "Export"]
  for (const t of tabLabels) {
    const count = await page.locator(`button:has-text("${t}")`).count()
    console.log(`   Tab buttons matching "${t}": ${count}`)
  }

  // 9. DONE
  console.log("9. Human walkthrough complete")
  console.log("\n--- Summary ---")
  console.log("Upload & redirect: YES")
  console.log("File visible in editor:", body.includes("journey1.mp4"))
  console.log("Add Videos button:", body.includes("Add Videos"))

  await browser.close()
}

main().catch(console.error)
