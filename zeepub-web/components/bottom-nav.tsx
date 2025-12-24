"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, Search, Settings, BarChart3, Library } from "lucide-react"
import { cn } from "@/lib/utils"

import { useAccessControl } from "@/hooks/use-access-control"

const navItems = [
  { icon: Home, label: "Inicio", href: "/" },
  { icon: Search, label: "Buscar", href: "/search" },
  { icon: Library, label: "Catálogo", href: "/catalog" },
  { icon: BarChart3, label: "Estado", href: "/status" },
]

export function BottomNav() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-card border-t border-border safe-area-inset-bottom">
      <div className="max-w-2xl mx-auto px-2 py-2">
        <div className="flex items-center justify-around gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center gap-1 px-4 py-2 rounded-lg transition-colors min-w-[72px]",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50",
                )}
              >
                <Icon className={cn("w-5 h-5", isActive && "text-primary")} />
                <span className={cn("text-xs font-medium", isActive && "text-primary")}>{item.label}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
