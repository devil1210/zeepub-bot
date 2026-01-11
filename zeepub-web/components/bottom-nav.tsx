"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, Search, Settings, BarChart3, Library, Download } from "lucide-react"
import { cn } from "@/lib/utils"

import { useAccessControl } from "@/hooks/use-access-control"
import { useStrings } from "@/components/strings-provider"

const navItems = [
  { icon: Home, labelKey: "home_functions", defaultLabel: "Inicio", href: "/" },
  { icon: Library, labelKey: "menu_catalog_label", defaultLabel: "Catálogo", href: "/catalog" },
  { icon: Download, labelKey: "menu_downloads_label", defaultLabel: "Descargas", href: "/downloads" },
  { icon: BarChart3, labelKey: "menu_status_label", defaultLabel: "Estado", href: "/status" },
]

export function BottomNav() {
  const pathname = usePathname()
  const { t } = useStrings()

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] max-w-md animate-in slide-in-from-bottom-4 duration-500 delay-150 fill-mode-both">
      <nav className="bg-background/70 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] p-1.5 ring-1 ring-white/5">
        <div className="flex items-center justify-around">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            const label = t(item.labelKey as any) || item.defaultLabel

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex flex-col items-center justify-center gap-0.5 px-3 py-2 rounded-xl transition-all duration-300",
                  "flex-1 min-w-[64px]",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {isActive && (
                  <div className="absolute inset-0 bg-primary/10 rounded-xl animate-in fade-in zoom-in-95 duration-300" />
                )}
                <Icon className={cn("w-5 h-5 relative z-10 transition-transform duration-300", isActive && "scale-110")} />
                <span className={cn(
                  "text-[9px] sm:text-xs font-bold relative z-10 transition-all duration-300",
                  isActive ? "opacity-100 translate-y-0" : "opacity-80"
                )}>
                  {label}
                </span>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
