"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { api } from "@/lib/api-client"
import type { Source, EDLRange, Scene, Render } from "@/lib/types"
import { useProject } from "@/hooks/use-project"
import { useTranscript } from "@/hooks/use-transcript"
import { LoadingSpinner } from "@/components/shared/loading-spinner"
import { EmptyState } from "@/components/shared/empty-state"
import { formatDuration } from "@/lib/utils"
import { Film, FileVideo, Mic, Scissors, BrainCircuit, Music, Crop, Download, Clock, Hash, Maximize2 } from "lucide-react"

export default function ProjectEditorPage() {
  const params = useParams()
  const projectId = Number(params.id)
  const { project, loading, error } = useProject(projectId)
  const { transcript, loadTranscript, startTranscription } = useTranscript(projectId)

  const [activeTab, setActiveTab] = useState("sources")
  const [sources, setSources] = useState<Source[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [renders, setRenders] = useState<Render[]>([])
  const [processing, setProcessing] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    api.listRenders(projectId).then(setRenders).catch(() => {})
  }, [projectId])

  if (loading) return <LoadingSpinner size={32} label="Loading project..." className="justify-center py-16" />
  if (error) return <div className="text-destructive py-16 text-center">{error}</div>
  if (!project) return <EmptyState icon={Film} title="Project not found" description="This project doesn't exist." />

  const tabs = [
    { id: "sources", label: "Sources", icon: FileVideo },
    { id: "transcript", label: "Transcript", icon: Mic },
    { id: "scenes", label: "Scenes", icon: BrainCircuit },
    { id: "reframe", label: "Reframe", icon: Crop },
    { id: "audio", label: "Audio", icon: Music },
    { id: "render", label: "Export", icon: Download },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <a href="/projects" className="hover:text-foreground">Projects</a>
            <span>/</span>
            <span className="text-foreground">{project.name}</span>
          </div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {project.aspect_ratio} · {project.fps}fps · {project.source_count} source{project.source_count !== 1 ? "s" : ""}
          </p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${
          project.status === "complete" ? "bg-green-500/10 text-green-400" :
          project.status === "transcribing" ? "bg-blue-500/10 text-blue-400" : "bg-muted text-muted-foreground"
        }`}>{project.status}</span>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
              activeTab === t.id ? "bg-background text-accent" : "text-muted-foreground hover:text-foreground"
            }`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Sources tab */}
      {activeTab === "sources" && (
        <div className="grid gap-4 md:grid-cols-2">
          {sources.length === 0 ? (
            <p className="col-span-full text-center text-muted-foreground py-8">No sources. Upload from the Upload page.</p>
          ) : sources.map((s) => (
            <div key={s.id} className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <FileVideo className="w-5 h-5 text-accent" />
                <span className="font-medium truncate">{s.filename}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {formatDuration(s.duration)}</span>
                <span className="flex items-center gap-1"><Maximize2 className="w-3 h-3" /> {s.width}×{s.height}</span>
                <span className="flex items-center gap-1"><Hash className="w-3 h-3" /> {s.codec}</span>
                <span className={`flex items-center gap-1 ${s.has_transcript ? "text-green-400" : ""}`}>
                  <Mic className="w-3 h-3" /> {s.has_transcript ? "Transcribed" : "Pending"}
                </span>
              </div>
              <div className="flex gap-2 mt-3">
                {!s.has_transcript && (
                  <button onClick={async () => {
                    setProcessing("Transcribing...")
                    await startTranscription(s.id)
                    setProcessing(null)
                  }} className="flex items-center gap-1 text-xs bg-accent/10 text-accent px-2 py-1 rounded hover:bg-accent/20">
                    <Mic className="w-3 h-3" /> Transcribe
                  </button>
                )}
                <button onClick={async () => {
                  setProcessing("Detecting scenes...")
                  const result = await api.detectScenes(projectId, s.id)
                  setScenes(result.scenes)
                  setProcessing(null)
                }} className="flex items-center gap-1 text-xs bg-secondary text-muted-foreground px-2 py-1 rounded hover:text-foreground">
                  <BrainCircuit className="w-3 h-3" /> Detect Scenes
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Transcript tab */}
      {activeTab === "transcript" && (
        !transcript ? (
          <div className="text-center py-16">
            <Mic className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Select a source and transcribe it first</p>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-lg p-4 max-h-[600px] overflow-y-auto">
            {transcript.words.map((w, i) => (
              <span key={i} className="transcript-word text-sm" title={`${w.start.toFixed(2)}s - ${w.end.toFixed(2)}s`}>{w.text} </span>
            ))}
          </div>
        )
      )}

      {/* Scenes tab */}
      {activeTab === "scenes" && (
        scenes.length === 0 ? (
          <div className="text-center py-16">
            <BrainCircuit className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Run scene detection from the Sources tab first</p>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-lg divide-y divide-border">
            {scenes.map((s, i) => (
              <div key={i} className="flex items-center justify-between p-3 text-sm hover:bg-secondary/50">
                <span>Scene {i + 1}</span>
                <span className="text-muted-foreground">{formatDuration(s.start)} - {formatDuration(s.end)}</span>
                <span className="text-muted-foreground">{(s.end - s.start).toFixed(1)}s</span>
              </div>
            ))}
          </div>
        )
      )}

      {/* Reframe tab */}
      {activeTab === "reframe" && (
        <div className="space-y-4 max-w-md">
          <p className="text-sm text-muted-foreground">Convert your video to different aspect ratios for social platforms.</p>
          <div className="grid grid-cols-2 gap-3">
            {[
              { aspect: "9:16", label: "TikTok / Reels", emoji: "📱" },
              { aspect: "1:1", label: "Instagram Square", emoji: "📋" },
              { aspect: "4:5", label: "IG Portrait", emoji: "📱" },
              { aspect: "16:9", label: "YouTube", emoji: "🖥️" },
            ].map((preset) => (
              <button key={preset.aspect} onClick={async () => {
                if (!sources[0]) return
                setProcessing(`Reframing to ${preset.aspect}...`)
                await api.reframe(projectId, sources[0].id, preset.aspect)
                setProcessing(null)
              }} className="bg-card border border-border rounded-lg p-4 text-center hover:border-accent transition-colors">
                <div className="text-2xl mb-1">{preset.emoji}</div>
                <div className="text-sm font-medium">{preset.aspect}</div>
                <div className="text-xs text-muted-foreground">{preset.label}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Audio tab */}
      {activeTab === "audio" && (
        <div className="space-y-4 max-w-md">
          <p className="text-sm text-muted-foreground">Clean up audio with open-source FFmpeg filters.</p>
          {[
            { mode: "full", label: "Full Cleanup", desc: "Noise reduction → silence removal → loudness normalization" },
            { mode: "silence", label: "Remove Silence", desc: "Cut out dead air and long pauses" },
          ].map((item) => (
            <button key={item.mode} onClick={async () => {
              if (!sources[0]) return
              setProcessing(`${item.label}...`)
              await api.cleanupAudio(projectId, sources[0].id, item.mode)
              setProcessing(null)
            }} className="w-full bg-card border border-border rounded-lg p-4 text-left hover:border-accent transition-colors">
              <div className="font-medium">{item.label}</div>
              <p className="text-xs text-muted-foreground mt-1">{item.desc}</p>
            </button>
          ))}
        </div>
      )}

      {/* Render tab */}
      {activeTab === "render" && (
        <div className="space-y-6">
          <div>
            <h3 className="font-medium mb-3">Render & Export</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { preset: "youtube", label: "YouTube", dims: "1920×1080" },
                { preset: "tiktok", label: "TikTok / Reels", dims: "1080×1920" },
                { preset: "instagram_square", label: "IG Square", dims: "1080×1080" },
                { preset: "twitter", label: "X / Twitter", dims: "1280×720" },
              ].map((p) => (
                <button key={p.preset} onClick={async () => {
                  setProcessing(`Rendering for ${p.label}...`)
                  try {
                    const result = await api.render(projectId, p.preset) as Render
                    setRenders((prev) => [...prev, result])
                  } catch (e) { console.error(e) }
                  setProcessing(null)
                }} className="bg-card border border-border rounded-lg p-4 text-center hover:border-accent transition-colors">
                  <div className="text-sm font-medium">{p.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">{p.dims}</div>
                </button>
              ))}
            </div>
          </div>

          {renders.length > 0 && (
            <div>
              <h3 className="font-medium mb-2">Render History</h3>
              <div className="bg-card border border-border rounded-lg divide-y divide-border">
                {renders.map((r, i) => (
                  <div key={i} className="flex items-center justify-between p-3 text-sm">
                    <div>
                      <span className="font-medium">{r.preset}</span>
                      <span className={`ml-2 text-xs ${r.status === "complete" ? "text-green-400" : r.status === "failed" ? "text-destructive" : "text-muted-foreground"}`}>{r.status}</span>
                    </div>
                    <div className="text-muted-foreground text-xs">
                      {r.duration_s ? `${r.duration_s.toFixed(1)}s` : ""}
                      {r.file_size_mb ? ` · ${r.file_size_mb}MB` : ""}
                    </div>
                    {r.status === "complete" && r.output_path && (
                      <a href={`/renders/${r.output_path.split("renders\\").pop() || r.output_path.split("renders/").pop()}`} download className="text-accent hover:underline text-xs">Download</a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Processing overlay */}
      {processing && (
        <div className="fixed inset-0 bg-background/80 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <LoadingSpinner size={32} className="justify-center mb-4" />
            <p className="text-lg font-medium">{processing}</p>
          </div>
        </div>
      )}
    </div>
  )
}
