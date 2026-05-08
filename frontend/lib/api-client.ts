const API_BASE = "/api"

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  listProjects: () => request<import("./types").Project[]>("/projects/"),
  createProject: (data: { name: string; description?: string; aspect_ratio?: string; fps?: number }) =>
    request<import("./types").Project>("/projects/", { method: "POST", body: JSON.stringify(data) }),
  getProject: (id: number) => request<import("./types").Project>(`/projects/${id}`),
  deleteProject: (id: number) => request<{ ok: boolean }>(`/projects/${id}`, { method: "DELETE" }),

  uploadFile: (projectId: number, file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    return fetch(`${API_BASE}/uploads/${projectId}`, { method: "POST", body: formData }).then((r) => r.json())
  },

  transcribe: (projectId: number, sourceId: number, engine = "elevenlabs", numSpeakers?: number) =>
    request<{ ok: boolean; transcript_path: string }>(`/transcription/${projectId}/sources/${sourceId}`, {
      method: "POST", body: JSON.stringify({ engine, num_speakers: numSpeakers }),
    }),
  getTranscript: (projectId: number, sourceId: number) =>
    request<import("./types").Transcript>(`/transcription/${projectId}/sources/${sourceId}/transcript`),

  createEDL: (projectId: number, data: { ranges: import("./types").EDLRange[]; grade?: string; overlays?: [] }) =>
    request<import("./types").EDL>(`/editing/${projectId}/edl`, { method: "POST", body: JSON.stringify(data) }),
  getEDL: (projectId: number) => request<import("./types").EDL>(`/editing/${projectId}/edl`),
  deleteEDL: (projectId: number) => request<{ ok: boolean }>(`/editing/${projectId}/edl`, { method: "DELETE" }),

  render: (projectId: number, preset = "youtube") =>
    request<import("./types").Render>(`/rendering/${projectId}/render`, { method: "POST", body: JSON.stringify({ preset }) }),
  listRenders: (projectId: number) =>
    request<import("./types").Render[]>(`/rendering/${projectId}/renders`),

  detectScenes: (projectId: number, sourceId: number, threshold = 30) =>
    request<{ scenes: import("./types").Scene[]; count: number }>(`/scenes/${projectId}/sources/${sourceId}/detect`, { method: "POST", body: JSON.stringify({ threshold }) }),

  reframe: (projectId: number, sourceId: number, targetAspect = "9:16", mode = "crop") =>
    request<{ output_path: string }>(`/reframe/${projectId}/sources/${sourceId}/reframe`, { method: "POST", body: JSON.stringify({ target_aspect: targetAspect, mode }) }),

  cleanupAudio: (projectId: number, sourceId: number, mode = "full") =>
    request<{ output_path: string }>(`/audio/${projectId}/sources/${sourceId}/cleanup`, { method: "POST", body: JSON.stringify({ mode }) }),

  listTemplates: (category = "") =>
    request<import("./types").Template[]>(`/templates/?category=${category}`),
  createTemplate: (data: { name: string; description?: string; category?: string; config?: Record<string, unknown> }) =>
    request<import("./types").Template>("/templates/", { method: "POST", body: JSON.stringify(data) }),
  deleteTemplate: (id: number) => request<{ ok: boolean }>(`/templates/${id}`, { method: "DELETE" }),

  listExportPresets: () => request<Record<string, import("./types").ExportPreset>>("/exports/presets"),
  exportVideo: (projectId: number, preset = "youtube") =>
    request<{ output_path: string }>(`/exports/${projectId}/export`, { method: "POST", body: JSON.stringify({ preset }) }),
  extractClip: (projectId: number, start: number, end: number, preset = "tiktok") =>
    request<{ output_path: string }>(`/exports/${projectId}/clip`, { method: "POST", body: JSON.stringify({ start, end, preset }) }),
}
