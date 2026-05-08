"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Film, FolderOpen, Upload, LayoutTemplate } from "lucide-react"

const navItems = [
  { href: "/", label: "Dashboard", icon: Film },
  { href: "/projects", label: "Projects", icon: FolderOpen },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <Link href="/" className="flex items-center gap-2">
          <Film className="w-6 h-6 text-accent" />
          <span className="font-bold text-lg">video-use</span>
        </Link>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
          return (
            <Link key={item.href} href={item.href}
              className={cn("flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive ? "bg-accent/10 text-accent font-medium" : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}>
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="p-3 border-t border-border">
        <p className="text-xs text-muted-foreground">video-use v0.1</p>
        <p className="text-xs text-muted-foreground">FFmpeg backend</p>
      </div>
    </aside>
  )
}
