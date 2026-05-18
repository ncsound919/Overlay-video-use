"use client"

import { useState, useEffect, useCallback } from "react"
import { api } from "@/lib/api-client"
import type { Project, EDL, EDLRange } from "@/lib/types"

export function useProject(id: number) {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [edl, setEdl] = useState<EDL | null>(null)
  const [edlLoading, setEdlLoading] = useState(false)

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

  const loadEDL = useCallback(async () => {
    setEdlLoading(true)
    try {
      const data = await api.getEDL(id)
      setEdl(data)
    } catch {
      setEdl(null)
    } finally {
      setEdlLoading(false)
    }
  }, [id])

  const saveEDL = useCallback(async (data: { ranges: EDLRange[]; grade?: string; subtitle_style?: string; overlays?: Array<{ file: string; start_in_output: number; duration: number; start_in_source?: number }> }) => {
    const result = await api.createEDL(id, data)
    setEdl(result)
    return result
  }, [id])

  useEffect(() => { load() }, [load])

  return { project, loading, error, reload: load, edl, edlLoading, loadEDL, saveEDL }
}
