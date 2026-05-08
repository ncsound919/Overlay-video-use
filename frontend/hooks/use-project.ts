"use client"

import { useState, useEffect, useCallback } from "react"
import { api } from "@/lib/api-client"
import type { Project } from "@/lib/types"

export function useProject(id: number) {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const p = await api.getProject(id)
      setProject(p)
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project")
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  return { project, loading, error, reload: load }
}
