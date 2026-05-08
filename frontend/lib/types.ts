export interface Project {
  id: number
  name: string
  description: string
  status: "draft" | "transcribing" | "editing" | "rendering" | "complete"
  aspect_ratio: string
  fps: number
  source_count: number
  created_at: string
  updated_at: string
}

export interface Source {
  id: number
  filename: string
  duration: number
  width: number
  height: number
  codec: string
  has_transcript: boolean
  created_at: string
}

export interface TranscriptWord {
  text: string
  type: string
  start: number
  end: number
  speaker_id: string
}

export interface Transcript {
  words: TranscriptWord[]
  language?: string
  text?: string
}

export interface EDLRange {
  source: string
  start: number
  end: number
  beat: string
  note: string
  quote: string
}

export interface EDL {
  id: number
  project_id: number
  version: number
  grade: string
  total_duration_s: number
  ranges: EDLRange[]
  overlays: Array<{ file: string; start_in_output: number; duration: number }>
  subtitles: string | null
  created_at: string
}

export interface Render {
  id: number
  project_id: number
  status: string
  preset: string
  width: number
  height: number
  duration_s: number
  file_size_mb: number
  error: string | null
  output_path: string | null
  created_at: string
}

export interface Scene {
  start: number
  end: number
  duration: number
}

export interface Template {
  id: number
  name: string
  description: string
  category: string
  config: Record<string, unknown>
  created_at: string | null
}

export interface ExportPreset {
  label: string
  width: number
  height: number
  extension: string
  [key: string]: unknown
}
