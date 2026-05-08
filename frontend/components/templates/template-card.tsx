import type { Template } from "@/lib/types"
import { Trash2 } from "lucide-react"

interface TemplateCardProps {
  template: Template
  onApply?: (template: Template) => void
  onDelete?: (id: number) => void
}

const categoryIcons: Record<string, string> = {
  podcast: "🎙️", rap: "🎤", interview: "🎬", tutorial: "📚", custom: "📁",
}

export function TemplateCard({ template, onApply, onDelete }: TemplateCardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 hover:border-accent transition-colors group">
      <div className="flex items-start justify-between mb-3">
        <div className="text-2xl">{categoryIcons[template.category] || "📁"}</div>
        {template.id > 0 && onDelete && (
          <button onClick={() => onDelete(template.id)}
            className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all">
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
      <h3 className="font-medium mb-1">{template.name}</h3>
      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{template.description}</p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground capitalize">{template.category}</span>
        {onApply && <button onClick={() => onApply(template)} className="text-xs text-accent hover:underline">Apply template</button>}
      </div>
    </div>
  )
}
