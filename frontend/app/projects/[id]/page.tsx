"use client"

import { useEffect, useState, useRef } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { Source, Scene, Render, EDL, EDLRange } from "@/lib/types"
import { useProject } from "@/hooks/use-project"
import { useTranscript } from "@/hooks/use-transcript"
import { LoadingSpinner } from "@/components/shared/loading-spinner"
import { EmptyState } from "@/components/shared/empty-state"
import { formatDuration } from "@/lib/utils"
import { toast } from "sonner"
import { Film, FileVideo, Mic, BrainCircuit, Music, Crop, Download, Clock, Hash, Maximize2, Plus, Loader2, Wand2, Pencil, Scissors, Trash2, Save, CheckCircle2, Sparkles, X, Palette, Type, Volume2, Layers } from "lucide-react"

export default function ProjectEditorPage() {
  const params = useParams()
  const projectId = Number(params.id)
  const { project, loading, error, saveEDL, edl: loadedEDL, loadEDL } = useProject(projectId)
  const { transcript, startTranscription, loadTranscript } = useTranscript(projectId)

  const [activeTab, setActiveTab] = useState("sources")
  const [sources, setSources] = useState<Source[]>([])
  const [sourcesLoading, setSourcesLoading] = useState(true)
  const [scenes, setScenes] = useState<Scene[]>([])
  const [renders, setRenders] = useState<Render[]>([])
  const [processing, setProcessing] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [transcriptSubtab, setTranscriptSubtab] = useState<"view" | "edit">("view")
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null)
  const [cutBoundaries, setCutBoundaries] = useState<number[]>([])
  const [savedEDL, setSavedEDL] = useState<EDL | null>(null)

  const [autoEditModalOpen, setAutoEditModalOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState("talking_head")

  const loadSources = () => {
    setSourcesLoading(true)
    fetch(`/api/uploads/${projectId}`)
      .then(r => r.json())
      .then(data => setSources(Array.isArray(data) ? data : []))
      .catch(() => toast.error("Failed to load sources"))
      .finally(() => setSourcesLoading(false))
  }

  useEffect(() => {
    if (!projectId) return
    loadSources()
    loadEDL()
    api.listRenders(projectId).then(setRenders).catch(() => {})
  }, [projectId, loadEDL])

  useEffect(() => {
    if (loadedEDL) setSavedEDL(loadedEDL)
  }, [loadedEDL])

  useEffect(() => {
    if (activeTab !== "transcript") return
    if (transcript) return
    const src = sources.find(s => s.has_transcript)
    if (src) {
      setSelectedSourceId(src.id)
      loadTranscript(src.id)
    }
  }, [activeTab, sources, transcript, loadTranscript])

  const handleAction = async (label: string, fn: () => Promise<any>) => {
    setProcessing(label)
    try { await fn() }
    catch (e: unknown) { toast.error(e instanceof Error ? e.message : `${label} failed`) }
    finally { setProcessing(null) }
  }

  const handleUploadMore = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    setUploading(true)
    let lastError = ""
    let success = 0
    for (let i = 0; i < files.length; i++) {
      try {
        await api.uploadFile(projectId, files[i])
        success++
      } catch (err: unknown) {
        lastError = err instanceof Error ? err.message : "Upload failed"
      }
    }
    setUploading(false)
    loadSources()
    if (success > 0) toast.success(`${success} file(s) added`)
    if (lastError) toast.error(lastError)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const resolveRenderUrl = (outputPath: string | null): string => {
    if (!outputPath) return "#"
    const parts = outputPath.replace(/\\/g, "/").split("renders/")
    return `/renders/${parts[parts.length - 1]}`
  }

  const handleAutoEdit = () => {
    setAutoEditModalOpen(false)
    handleAction(`Auto-editing with ${selectedTemplate} template...`, async () => {
      const result = await fetch(`/api/editing/${projectId}/auto-edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template: selectedTemplate }),
      })
      if (!result.ok) throw new Error((await result.text()) || "Auto-edit failed")
      const edl = await result.json()
      toast.success(`EDL created: ${edl.ranges?.length || 0} segments, ${edl.total_duration_s}s`)
      // Refresh EDL data
      loadEDL()
    })
  }

  const toggleBoundary = (index: number) => {
    setSavedEDL(null)
    setCutBoundaries(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index)
      }
      return [...prev, index].sort((a, b) => a - b)
    })
  }

  const removeRange = (rangeIndex: number) => {
    setSavedEDL(null)
    setCutBoundaries(prev => {
      const sorted = [...prev].sort((a, b) => a - b)
      const startIdx = rangeIndex * 2
      const endIdx = startIdx + 1
      return sorted.filter((_, i) => i !== startIdx && i !== endIdx)
    })
  }

  const buildRanges = (): EDLRange[] => {
    if (!transcript || !selectedSourceId) return []
    const sorted = [...cutBoundaries].sort((a, b) => a - b)
    const src = sources.find(s => s.id === selectedSourceId)
    const sourceName = src?.filename || `Source ${selectedSourceId}`
    const padding = 0.05
    const ranges: EDLRange[] = []
    for (let i = 0; i + 1 < sorted.length; i += 2) {
      const startWord = transcript.words[sorted[i]]
      const endWord = transcript.words[sorted[i + 1]]
      if (!startWord || !endWord) continue
      let start = Math.max(0, startWord.start - padding)
      let end = endWord.end + padding
      if (src) end = Math.min(src.duration, end)
      ranges.push({
        source: sourceName,
        start,
        end,
        beat: "",
        note: "",
        quote: "",
      })
    }
    return ranges
  }

  const handleSaveEDL = async () => {
    const ranges = buildRanges()
    if (ranges.length === 0) return
    try {
      const result = await saveEDL({ ranges })
      setSavedEDL(result)
      toast.success(`EDL saved: ${ranges.length} segments, ${result.total_duration_s?.toFixed(2)}s`)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to save EDL")
    }
  }

  const handleRemoveTimelineItem = async (type: 'range' | 'overlay', index: number) => {
    if (!savedEDL) return;
    const newEDL = { ...savedEDL };
    if (type === 'range') {
      newEDL.ranges = newEDL.ranges.filter((_, i) => i !== index);
      newEDL.total_duration_s = newEDL.ranges.reduce((acc, r) => acc + (r.end - r.start), 0);
    } else {
      newEDL.overlays = newEDL.overlays.filter((_, i) => i !== index);
    }
    
    try {
      const result = await saveEDL(newEDL);
      setSavedEDL(result);
      toast.success('Timeline updated');
    } catch (e: unknown) {
      toast.error('Failed to update timeline');
    }
  }

  if (loading) return <LoadingSpinner size={32} label="Loading project..." className="justify-center py-16" />
  if (error) return <div className="text-destructive py-16 text-center">{error}</div>
  if (!project) return <EmptyState icon={Film} title="Project not found" description="This project doesn't exist." />

  const tabs = [
    { id: "sources", label: "Sources", icon: FileVideo },
    { id: "transcript", label: "Transcript", icon: Mic },
    { id: "timeline", label: "Timeline", icon: Layers },
    { id: "scenes", label: "Scenes", icon: BrainCircuit },
    { id: "reframe", label: "Reframe", icon: Crop },
    { id: "effects", label: "Effects", icon: Sparkles },
    { id: "audio", label: "Audio", icon: Music },
    { id: "render", label: "Export", icon: Download },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/projects" className="hover:text-foreground">Projects</Link>
            <span>/</span>
            <span className="text-foreground">{project.name}</span>
          </div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {project.aspect_ratio} · {project.fps}fps · {sources.length} source{sources.length !== 1 ? "s" : ""}
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
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <input ref={fileInputRef} type="file" accept="video/*" multiple className="hidden" id="editor-upload" onChange={handleUploadMore} />
            <button onClick={() => fileInputRef.current?.click()} disabled={uploading}
              className="flex items-center gap-2 bg-accent/10 text-accent px-4 py-2 rounded-md hover:bg-accent/20 disabled:opacity-50 transition-colors text-sm">
              {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</> : <><Plus className="w-4 h-4" /> Add Videos</>}
            </button>
            <button onClick={() => setAutoEditModalOpen(true)}
              className="flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md hover:bg-accent/90 transition-colors text-sm">
              <Wand2 className="w-4 h-4" /> Auto Edit
            </button>
            <span className="text-xs text-muted-foreground">{sources.length} file{sources.length !== 1 ? "s" : ""} loaded</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {sourcesLoading ? (
              <p className="col-span-full text-center text-muted-foreground py-8">Loading sources...</p>
            ) : sources.length === 0 ? (
              <p className="col-span-full text-center text-muted-foreground py-8">No sources yet. Click "Add Videos" above or use the Upload page.</p>
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
                    <button onClick={() => handleAction("Transcribing...", () => startTranscription(s.id))}
                      className="flex items-center gap-1 text-xs bg-accent/10 text-accent px-2 py-1 rounded hover:bg-accent/20">
                      <Mic className="w-3 h-3" /> Transcribe
                    </button>
                  )}
                  <button onClick={() => handleAction("Detecting scenes...", async () => {
                    const result = await api.detectScenes(projectId, s.id)
                    setScenes(result.scenes)
                  })} className="flex items-center gap-1 text-xs bg-secondary text-muted-foreground px-2 py-1 rounded hover:text-foreground">
                    <BrainCircuit className="w-3 h-3" /> Detect Scenes
                  </button>
                </div>
              </div>
            ))}
          </div>
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
          <div className="space-y-3">
            <div className="flex gap-2">
              <button
                onClick={() => setTranscriptSubtab("view")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  transcriptSubtab === "view" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Pencil className="w-3 h-3" /> View
              </button>
              <button
                onClick={() => setTranscriptSubtab("edit")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  transcriptSubtab === "edit" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Scissors className="w-3 h-3" /> Edit
              </button>
            </div>

            {transcriptSubtab === "view" && (
              <div className="bg-card border border-border rounded-lg p-4 max-h-[600px] overflow-y-auto">
                {transcript.words.map((w, i) => (
                  <span key={i} className="transcript-word text-sm" title={`${w.start.toFixed(2)}s - ${w.end.toFixed(2)}s`}>{w.text} </span>
                ))}
              </div>
            )}

            {transcriptSubtab === "edit" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2 bg-card border border-border rounded-lg p-4 max-h-[600px] overflow-y-auto">
                  {transcript.words.map((w, i) => {
                    const isBoundary = cutBoundaries.includes(i)
                    return (
                      <span
                        key={i}
                        onClick={() => toggleBoundary(i)}
                        className={`inline-block cursor-pointer text-sm mr-1 px-1 rounded transition-colors ${
                          isBoundary ? "bg-accent text-accent-foreground font-medium" : "hover:bg-secondary"
                        }`}
                        title={`${w.start.toFixed(2)}s - ${w.end.toFixed(2)}s`}
                      >
                        {w.text}
                      </span>
                    )
                  })}
                </div>

                <div className="bg-card border border-border rounded-lg p-4 space-y-4">
                  <h3 className="font-medium flex items-center gap-2">
                    <Scissors className="w-4 h-4" /> Cut List
                  </h3>
                  <div className="space-y-2">
                    {buildRanges().length === 0 && (
                      <p className="text-xs text-muted-foreground">Click words to mark start/end boundaries.</p>
                    )}
                    {buildRanges().map((range, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm bg-secondary/50 rounded p-2">
                        <div className="min-w-0">
                          <div className="text-xs text-muted-foreground truncate">{range.source}</div>
                          <div className="font-medium">{formatDuration(range.start)} - {formatDuration(range.end)}</div>
                          <div className="text-xs text-muted-foreground">{(range.end - range.start).toFixed(2)}s</div>
                        </div>
                        <button
                          onClick={() => removeRange(idx)}
                          className="ml-2 text-destructive hover:text-destructive/80 shrink-0"
                          title="Remove cut"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    {cutBoundaries.length % 2 !== 0 && (
                      <p className="text-xs text-amber-400">Pending end boundary...</p>
                    )}
                  </div>

                  <button
                    onClick={handleSaveEDL}
                    disabled={buildRanges().length === 0}
                    className="w-full flex items-center justify-center gap-2 bg-accent text-accent-foreground px-3 py-2 rounded-md hover:bg-accent/90 disabled:opacity-50 text-sm transition-colors"
                  >
                    <Save className="w-4 h-4" /> Save EDL
                  </button>

                  {savedEDL && (
                    <div className="text-xs text-green-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Runtime: {savedEDL.total_duration_s.toFixed(2)}s
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* Timeline tab */}
      {activeTab === "timeline" && (
        !savedEDL || savedEDL.ranges.length === 0 ? (
          <div className="text-center py-16">
            <Layers className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Generate an EDL first (via Auto Edit or Transcript tab)</p>
          </div>
        ) : (
          <div className="space-y-4">
            <h3 className="font-medium flex items-center gap-2"><Layers className="w-5 h-5 text-accent" /> Visual Timeline Editor</h3>
            <p className="text-sm text-muted-foreground">Click a clip to delete it from the sequence. Edits are saved automatically.</p>
            
            <div className="bg-card border border-border rounded-lg p-6 overflow-x-auto">
               <div className="relative h-40 min-w-[800px] bg-secondary/10 rounded-lg border border-border/50">
                 
                 {/* B-Roll Track (Top) */}
                 <div className="absolute top-2 left-0 right-0 h-14 border-b border-border/20">
                   <div className="absolute -left-16 top-4 text-xs font-medium text-muted-foreground">B-Roll</div>
                   {savedEDL.overlays.map((o, i) => {
                     const left = (o.start_in_output / savedEDL.total_duration_s) * 100
                     const width = (o.duration / savedEDL.total_duration_s) * 100
                     return (
                       <div 
                         key={i} 
                         onClick={() => handleRemoveTimelineItem('overlay', i)}
                         className="absolute h-10 top-2 bg-blue-500/80 border border-blue-400 rounded cursor-pointer hover:bg-destructive transition-colors flex items-center shadow-md group" 
                         style={{ left: `${left}%`, width: `${width}%` }} 
                         title={`Click to delete\nB-Roll: ${o.file}\nDuration: ${o.duration.toFixed(2)}s`}
                       >
                         <span className="text-[10px] px-2 truncate block text-white font-medium w-full group-hover:hidden">{o.file}</span>
                         <span className="text-[10px] px-2 truncate hidden text-white font-medium w-full group-hover:flex items-center justify-center gap-1"><Trash2 className="w-3 h-3" /> Delete</span>
                       </div>
                     )
                   })}
                 </div>

                 {/* A-Roll Track (Bottom) */}
                 <div className="absolute top-16 left-0 right-0 h-24">
                   <div className="absolute -left-16 top-6 text-xs font-medium text-muted-foreground">A-Roll</div>
                   <div className="absolute left-0 right-0 h-16 top-4 flex gap-[1px]">
                     {(() => {
                       let currentStart = 0;
                       return savedEDL.ranges.map((r, i) => {
                         const dur = r.end - r.start;
                         const widthPercent = (dur / savedEDL.total_duration_s) * 100;
                         currentStart += dur;
                         return (
                           <div 
                             key={i} 
                             onClick={() => handleRemoveTimelineItem('range', i)}
                             className="h-full bg-emerald-500/80 border-r border-emerald-400 last:border-0 rounded-sm cursor-pointer hover:bg-destructive transition-colors flex items-center shadow-md group" 
                             style={{ width: `${widthPercent}%` }} 
                             title={`Click to delete\nA-Roll: ${r.source}\nDuration: ${dur.toFixed(2)}s\nText: ${r.quote}`}
                           >
                             <span className="text-[10px] px-2 truncate block text-white font-medium w-full group-hover:hidden">{r.source}</span>
                             <span className="text-[10px] px-2 truncate hidden text-white font-medium w-full group-hover:flex items-center justify-center"><Trash2 className="w-3 h-3" /></span>
                           </div>
                         )
                       });
                     })()}
                   </div>
                 </div>

               </div>
               
               <div className="flex justify-between items-center text-xs text-muted-foreground mt-3 px-1">
                 <span>0:00</span>
                 <span>Total Duration: {formatDuration(savedEDL.total_duration_s)}</span>
               </div>
            </div>
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
              <button key={preset.aspect} onClick={() => {
                if (!sources[0]) return
                handleAction(`Reframing to ${preset.aspect}...`, () => api.reframe(projectId, sources[0].id, preset.aspect))
              }} className="bg-card border border-border rounded-lg p-4 text-center hover:border-accent transition-colors">
                <div className="text-2xl mb-1">{preset.emoji}</div>
                <div className="text-sm font-medium">{preset.aspect}</div>
                <div className="text-xs text-muted-foreground">{preset.label}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Effects tab */}
      {activeTab === "effects" && (
        <div className="space-y-8">
          <div>
            <h3 className="text-lg font-medium mb-3 flex items-center gap-2"><Palette className="w-5 h-5 text-accent" /> Color Grading</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { id: "neutral_punch", label: "Neutral Punch", desc: "Balanced contrast" },
                { id: "gritty_rap", label: "Gritty Rap", desc: "High contrast, desaturated" },
                { id: "neon_vibes", label: "Neon Vibes", desc: "Vibrant cyberpunk look" },
                { id: "vintage_film", label: "Vintage Film", desc: "Warm, grainy fade" },
              ].map((grade) => (
                <button key={grade.id} onClick={() => {
                  if (savedEDL) {
                    saveEDL({ ...savedEDL, grade: grade.id })
                    toast.success(`Applied ${grade.label} grade`)
                  } else toast.error("Create an EDL first (Transcript tab or Auto Edit)")
                }} className={`bg-card border ${savedEDL?.grade === grade.id ? "border-accent ring-2 ring-accent/20" : "border-border"} rounded-lg p-4 text-center hover:border-accent transition-colors`}>
                  <div className="font-medium text-sm">{grade.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">{grade.desc}</div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-3 flex items-center gap-2"><Type className="w-5 h-5 text-accent" /> Subtitle Styles</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { id: "karaoke_bounce", label: "Karaoke Bounce", desc: "Words bounce on beat" },
                { id: "bold_neon", label: "Bold Neon", desc: "Glowing rap lyrics" },
                { id: "clean_minimal", label: "Minimal", desc: "Standard bottom text" },
                { id: "typewriter", label: "Typewriter", desc: "Letter by letter" },
              ].map((style) => (
                <button key={style.id} onClick={() => {
                  if (savedEDL) {
                    saveEDL({ ...savedEDL, subtitle_style: style.id })
                    toast.success(`Applied ${style.label} subtitles`)
                  } else toast.error("Create an EDL first (Transcript tab or Auto Edit)")
                }} className={`bg-card border ${savedEDL?.subtitle_style === style.id ? "border-accent ring-2 ring-accent/20" : "border-border"} rounded-lg p-4 text-center hover:border-accent transition-colors`}>
                  <div className="font-medium text-sm">{style.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">{style.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Audio tab */}
      {activeTab === "audio" && (
        <div className="space-y-4 max-w-md">
          <p className="text-sm text-muted-foreground">Clean up and enhance audio with open-source FFmpeg filters.</p>
          {[
            { mode: "full", label: "Full Cleanup", desc: "Noise reduction → silence removal → loudness normalization" },
            { mode: "silence", label: "Remove Silence", desc: "Cut out dead air and long pauses" },
            { mode: "bass_boost", label: "Bass Boost (Rap / Music)", desc: "Enhance low frequencies for impactful beats" },
          ].map((item) => (
            <button key={item.mode} onClick={() => {
              if (!sources[0]) return
              handleAction(`${item.label}...`, () => api.cleanupAudio(projectId, sources[0].id, item.mode))
            }} className="w-full bg-card border border-border rounded-lg p-4 text-left hover:border-accent transition-colors flex items-start gap-3">
              <Volume2 className="w-5 h-5 text-muted-foreground mt-0.5" />
              <div>
                <div className="font-medium">{item.label}</div>
                <p className="text-xs text-muted-foreground mt-1">{item.desc}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Export tab */}
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
                <button key={p.preset} onClick={() => handleAction(`Rendering for ${p.label}...`, async () => {
                  const result = await api.render(projectId, p.preset) as Render
                  setRenders(prev => [...prev, result])
                })} className="bg-card border border-border rounded-lg p-4 text-center hover:border-accent transition-colors">
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
                    {r.status === "complete" && (
                      <a href={resolveRenderUrl(r.output_path)} download className="text-accent hover:underline text-xs">Download</a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Auto Edit Modal */}
      {autoEditModalOpen && (
        <div className="fixed inset-0 bg-background/80 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">Auto Edit</h2>
              <button onClick={() => setAutoEditModalOpen(false)}><X className="w-4 h-4 text-muted-foreground hover:text-foreground" /></button>
            </div>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Select a template for the AI to auto-generate an edit list (EDL).</p>
              <select 
                value={selectedTemplate} 
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full bg-secondary border border-border rounded-md px-3 py-2 text-sm"
              >
                <option value="talking_head">Talking Head (Standard)</option>
                <option value="director">Director Mode (Autonomous Multi-Cam)</option>
                <option value="cinema">Cinema Mode (Slow Deliberate Cuts)</option>
                <option value="rap">Rap / Music Video (Beat Sync)</option>
                <option value="podcast">Podcast (Multi-Cam)</option>
                <option value="interview">Interview</option>
              </select>
              <button onClick={handleAutoEdit}
                className="w-full bg-accent text-accent-foreground py-2 rounded-md hover:bg-accent/90 transition-colors">
                Generate Edit
              </button>
            </div>
          </div>
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
