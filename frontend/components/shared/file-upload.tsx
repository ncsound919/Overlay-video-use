"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { Upload, FileVideo, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>
  accept?: string
  maxSize?: number
}

export function FileUpload({ onUpload, accept = "video/*", maxSize = 4096 }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const input = fileRef.current
    if (!input) return
    const handleChange = async () => {
      const file = input.files?.[0]
      if (!file) return
      setUploading(true)
      try { await onUpload(file) } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed")
      } finally { setUploading(false) }
    }
    input.addEventListener("change", handleChange)
    return () => input.removeEventListener("change", handleChange)
  }, [onUpload])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    setError(null)
    const file = e.dataTransfer.files[0]
    if (!file) return
    if (file.size > maxSize * 1024 * 1024) {
      setError(`File too large. Max ${maxSize}MB.`)
      return
    }
    setUploading(true)
    try { await onUpload(file) } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed")
    } finally { setUploading(false) }
  }, [onUpload, maxSize])

  return (
    <div className={cn("border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer",
        isDragging ? "border-accent bg-accent/5" : "border-border hover:border-muted-foreground",
        uploading && "opacity-50 pointer-events-none"
      )}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => fileRef.current?.click()}
    >
      <input ref={fileRef} type="file" accept={accept} className="sr-only" />
      {uploading ? (
        <div className="space-y-2">
          <FileVideo className="w-12 h-12 mx-auto text-accent animate-pulse" />
          <p className="text-muted-foreground">Uploading...</p>
        </div>
      ) : (
        <div className="space-y-2">
          <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
          <p className="text-lg font-medium">Drop video here or click to browse</p>
          <p className="text-sm text-muted-foreground">MP4, MOV, AVI up to {maxSize}MB</p>
        </div>
      )}
      {error && <div className="mt-4 flex items-center gap-2 text-destructive text-sm">{error}</div>}
    </div>
  )
}
