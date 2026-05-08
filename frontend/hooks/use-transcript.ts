"use client"

import { useState, useCallback } from "react"
import { api } from "@/lib/api-client"
import type { Transcript } from "@/lib/types"

export function useTranscript(projectId: number) {
  const [transcript, setTranscript] = useState<Transcript | null>(null)
  const [loading, setLoading] = useState(false)

  const loadTranscript = useCallback(async (sourceId: number) => {
    setLoading(true)
    try {
      const data = await api.getTranscript(projectId, sourceId)
      setTranscript(data)
    } catch { } finally { setLoading(false) }
  }, [projectId])

  const startTranscription = useCallback(async (sourceId: number, engine = "elevenlabs", numSpeakers?: number) => {
    setLoading(true)
    try {
      await api.transcribe(projectId, sourceId, engine, numSpeakers)
      await loadTranscript(sourceId)
    } finally { setLoading(false) }
  }, [projectId, loadTranscript])

  return { transcript, loading, loadTranscript, startTranscription }
}
