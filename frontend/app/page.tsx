"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { Project } from "@/lib/types"
import { formatDate } from "@/lib/utils"
import { EmptyState } from "@/components/shared/empty-state"
import { Film, Plus } from "lucide-react"

export default function DashboardPage() {
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
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Manage your video editing projects</p>
        </div>
        <Link href="/upload"
          className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90 transition-colors">
          <Plus className="w-4 h-4" />
          New Project
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-40 bg-card rounded-lg animate-pulse" />)}
        </div>
      ) : projects.length === 0 ? (
        <EmptyState icon={Film} title="No projects yet"
          description="Upload a video to start editing. video-use will transcribe, analyze, and help you create the perfect cut."
          action={<Link href="/upload" className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90"><Plus className="w-4 h-4" />Create your first project</Link>} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}
              className="bg-card border border-border rounded-lg p-4 hover:border-muted-foreground transition-colors group">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-muted-foreground">{formatDate(p.created_at)}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[p.status] || statusColors.draft}`}>{p.status}</span>
              </div>
              <h3 className="font-medium mb-1 group-hover:text-accent transition-colors">{p.name}</h3>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{p.description || "No description"}</p>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{p.source_count} source{p.source_count !== 1 ? "s" : ""}</span>
                <span>{p.aspect_ratio}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
