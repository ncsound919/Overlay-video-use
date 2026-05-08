"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api-client"
import type { Template } from "@/lib/types"
import { TemplateCard } from "@/components/templates/template-card"
import { EmptyState } from "@/components/shared/empty-state"
import { LayoutTemplate, Plus, X } from "lucide-react"

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: "", description: "", category: "custom" })

  useEffect(() => {
    api.listTemplates(category).then(setTemplates).catch(console.error).finally(() => setLoading(false))
  }, [category])

  const handleCreate = async () => {
    await api.createTemplate({
      name: form.name, description: form.description, category: form.category,
      config: { grade: "neutral_punch", caption_style: { font: "Helvetica", size: 18 },
                cuts: { silence_threshold_ms: 400, filler_removal: true } },
    })
    setShowForm(false)
    setForm({ name: "", description: "", category: "custom" })
    api.listTemplates(category).then(setTemplates)
  }

  const handleDelete = async (id: number) => {
    await api.deleteTemplate(id)
    setTemplates((prev) => prev.filter((t) => t.id !== id))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Templates</h1>
          <p className="text-muted-foreground mt-1">Pre-configured editing profiles for different content types</p>
        </div>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90">
          <Plus className="w-4 h-4" /> New Template
        </button>
      </div>

      <div className="flex gap-2">
        {["", "podcast", "rap", "interview", "custom"].map((c) => (
          <button key={c} onClick={() => setCategory(c)}
            className={`text-sm px-3 py-1 rounded-full transition-colors ${category === c ? "bg-accent text-accent-foreground" : "bg-secondary text-muted-foreground hover:text-foreground"}`}>
            {c || "All"}
          </button>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-background/80 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">New Template</h2>
              <button onClick={() => setShowForm(false)}><X className="w-4 h-4" /></button>
            </div>
            <div className="space-y-3">
              <input placeholder="Template name" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm" />
              <textarea placeholder="Description" value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm resize-none h-20" />
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm">
                <option value="custom">Custom</option>
                <option value="podcast">Podcast</option>
                <option value="rap">Rap / Music</option>
                <option value="interview">Interview</option>
              </select>
              <button onClick={handleCreate} disabled={!form.name}
                className="w-full bg-accent text-accent-foreground py-2 rounded-md hover:bg-accent/90 disabled:opacity-50">
                Create Template
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((i) => <div key={i} className="h-40 bg-card rounded-lg animate-pulse" />)}</div>
      ) : templates.length === 0 ? (
        <EmptyState icon={LayoutTemplate} title="No templates" description="Create a template to save editing presets." />
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {templates.map((t) => <TemplateCard key={t.id || t.name} template={t} onDelete={t.id > 0 ? handleDelete : undefined} />)}
        </div>
      )}
    </div>
  )
}
