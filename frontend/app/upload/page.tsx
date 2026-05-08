"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { FileUpload } from "@/components/shared/file-upload"
import { api } from "@/lib/api-client"
import { LoadingSpinner } from "@/components/shared/loading-spinner"

export default function UploadPage() {
  const router = useRouter()
  const [step, setStep] = useState<"create" | "uploading" | "done">("create")
  const [projectId, setProjectId] = useState<number | null>(null)
  const [projectName, setProjectName] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (file: File) => {
    setError(null)
    setStep("uploading")
    try {
      const name = projectName || file.name.replace(/\.[^/.]+$/, "")
      const project = await api.createProject({ name, description: `Auto-created from ${file.name}` })
      setProjectId(project.id)
      await api.uploadFile(project.id, file)
      setStep("done")
      setTimeout(() => router.push(`/projects/${project.id}`), 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
      setStep("create")
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Upload Video</h1>
        <p className="text-muted-foreground mt-1">Drop a video file to create a new project.</p>
      </div>

      {step === "create" && (
        <>
          <div className="space-y-2">
            <label className="text-sm font-medium">Project Name (optional)</label>
            <input type="text" value={projectName} onChange={(e) => setProjectName(e.target.value)}
              placeholder="Leave blank to use filename"
              className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent" />
          </div>
          <FileUpload onUpload={handleUpload} />
          {error && <p className="text-destructive text-sm">{error}</p>}
        </>
      )}

      {step === "uploading" && (
        <div className="flex flex-col items-center py-16">
          <LoadingSpinner size={48} label="Uploading and creating project..." />
        </div>
      )}

      {step === "done" && (
        <div className="flex flex-col items-center py-16">
          <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mb-4">
            <span className="text-green-400 text-2xl">✓</span>
          </div>
          <h2 className="text-xl font-medium mb-1">Upload complete!</h2>
          <p className="text-muted-foreground">Redirecting to project editor...</p>
        </div>
      )}
    </div>
  )
}
