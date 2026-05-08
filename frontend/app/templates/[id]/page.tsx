"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { api } from "@/lib/api-client"
import type { Template } from "@/lib/types"
import { TemplateCard } from "@/components/templates/template-card"
import { LoadingSpinner } from "@/components/shared/loading-spinner"
import { EmptyState } from "@/components/shared/empty-state"
import { LayoutTemplate } from "lucide-react"
import Link from "next/link"

export default function TemplateDetailPage() {
  const params = useParams()
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
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/templates" className="hover:text-foreground">Templates</Link>
        <span>/</span>
        <span className="text-foreground">{template.name}</span>
      </div>
      <h1 className="text-3xl font-bold">{template.name}</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <TemplateCard template={template} />
      </div>
      {template.config && Object.keys(template.config).length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-medium mb-2">Config</h3>
          <pre className="text-xs text-muted-foreground overflow-x-auto">
            {JSON.stringify(template.config, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
