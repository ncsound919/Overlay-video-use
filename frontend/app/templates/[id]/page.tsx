"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { api } from "@/lib/api-client"
import type { Template } from "@/lib/types"
import { LoadingSpinner } from "@/components/shared/loading-spinner"
import { EmptyState } from "@/components/shared/empty-state"
import { LayoutTemplate, Settings, Play } from "lucide-react"
import Link from "next/link"

const categoryLabels: Record<string, string> = {
  podcast: "Podcast", rap: "Rap / Music", interview: "Interview", tutorial: "Tutorial", custom: "Custom"
}

export default function TemplateDetailPage() {
  const params = useParams()
  const router = useRouter()
  const templateId = Number(params.id)
  const [template, setTemplate] = useState<Template | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getTemplate(templateId)
      .then(setTemplate)
      .catch(() => setError("Template not found"))
      .finally(() => setLoading(false))
  }, [templateId])

  if (loading) return <LoadingSpinner size={32} label="Loading..." className="justify-center py-16" />
  if (error || !template) return (
    <EmptyState
      icon={LayoutTemplate}
      title="Template not found"
      description="This template doesn't exist or may have been deleted."
      action={<Link href="/templates" className="text-accent hover:underline">Back to Templates</Link>}
    />
  )

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/templates" className="hover:text-foreground">Templates</Link>
        <span>/</span>
        <span className="text-foreground">{template.name}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{template.name}</h1>
          {template.description && <p className="text-muted-foreground mt-2">{template.description}</p>}
        </div>
        <span className="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-full capitalize">
          {categoryLabels[template.category] || template.category}
        </span>
      </div>

      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-medium mb-4">Template Settings</h2>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Grade</h3>
            <p className="text-sm">{template.config?.grade || "default"}</p>
          </div>
          {template.config?.caption_style && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Caption Style</h3>
              <p className="text-sm">Font: {template.config.caption_style.font || "default"}</p>
              <p className="text-sm">Size: {template.config.caption_style.size || "default"}</p>
            </div>
          )}
          {template.config?.cuts && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Cut Settings</h3>
              <p className="text-sm">Silence threshold: {template.config.cuts.silence_threshold_ms || "default"}ms</p>
              <p className="text-sm">Filler removal: {template.config.cuts.filler_removal ? "Yes" : "No"}</p>
            </div>
          )}
        </div>
      </div>

      {template.config && Object.keys(template.config).length > 0 && (
        <details className="bg-card border border-border rounded-lg">
          <summary className="px-4 py-3 cursor-pointer text-sm font-medium hover:bg-secondary/50">Raw Config</summary>
          <pre className="px-4 pb-4 text-xs text-muted-foreground overflow-x-auto">
            {JSON.stringify(template.config, null, 2)}
          </pre>
        </details>
      )}

      <div className="flex gap-3">
        <button
          onClick={() => router.push("/projects/new")}
          className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90"
        >
          <Play className="w-4 h-4" /> Apply to Project
        </button>
        <Link href="/templates" className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-md hover:bg-secondary/80">
          Back
        </Link>
      </div>
    </div>
  )
}