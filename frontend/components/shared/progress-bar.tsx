import { cn } from "@/lib/utils"

interface ProgressBarProps {
  progress: number
  className?: string
  label?: string
}

export function ProgressBar({ progress, className, label }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, progress))
  return (
    <div className={cn("space-y-1", className)}>
      {label && <div className="flex justify-between text-sm"><span>{label}</span><span>{Math.round(clamped)}%</span></div>}
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div className="h-full bg-accent rounded-full transition-all duration-300" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  )
}
