"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { Project } from "@/lib/types"
import { formatDate } from "@/lib/utils"
import { EmptyState } from "@/components/shared/empty-state"
import { FolderOpen, Plus } from "lucide-react"

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listProjects().then(setProjects).catch(console.error).finally(() => setLoading(false))
  }, [])

  const statusColors: Record<string, string> = {
    draft: "bg-muted text-muted-foreground",
    transcribing: "bg-blue-500/10 text-blue-400",
    editing: "bg-yellow-500/10 text-yellow-400",
    rendering: "bg-purple-500/10 text-purple-400",
    complete: "bg-green-500/10 text-green-400",
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Projects</h1>
        <Link href="/upload" className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90">
          <Plus className="w-4 h-4" /> New Project
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((i) => <div key={i} className="h-36 bg-card rounded-lg animate-pulse" />)}</div>
      ) : projects.length === 0 ? (
        <EmptyState icon={FolderOpen} title="No projects" description="Create your first project to get started." />
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`} className="bg-card border border-border rounded-lg p-4 hover:border-muted-foreground transition-colors group">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">{formatDate(p.created_at)}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[p.status] || statusColors.draft}`}>{p.status}</span>
              </div>
              <h3 className="font-medium group-hover:text-accent">{p.name}</h3>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-1">{p.description || "No description"}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
