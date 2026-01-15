"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, Search, Settings, BarChart3, Library, Download } from "lucide-react"
import { cn } from "@/lib/utils"

import { useAccessControl } from "@/hooks/use-access-control"
import { useStrings } from "@/components/strings-provider"

const navItems = [
  { icon: Home, labelKey: "home_functions", defaultLabel: "Funciones", href: "/" },
  { icon: Library, labelKey: "menu_catalog_label", defaultLabel: "Mi Catálogo", href: "/catalog" },
  { icon: Download, labelKey: "menu_downloads_label", defaultLabel: "Mis Descargas", href: "/downloads" },
  { icon: BarChart3, labelKey: "menu_status_label", defaultLabel: "Estado", href: "/status" },
]

export function BottomNav() {
  const pathname = usePathname()
  const { t } = useStrings()

  return (
    <nav className="w-full bg-background/80 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-1 relative overflow-hidden group/nav">
      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5 pointer-events-none" />
      <div className="flex items-center justify-around gap-1 p-0.5">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          const label = t(item.labelKey as any) || item.defaultLabel

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex-1 flex flex-col items-center justify-center gap-1 h-12 rounded-xl transition-all duration-300 active:scale-95",
                isActive
                  ? "bg-primary/20 text-primary shadow-[0_0_15px_rgba(var(--primary),0.3)] border border-primary/20"
                  : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
              )}
            >
              <Icon className={cn("w-4 h-4 transition-transform duration-300", isActive && "scale-110")} />
              <span className={cn(
                "text-[9px] uppercase tracking-[0.1em] font-bold text-center",
                isActive ? "opacity-100" : "opacity-70"
              )}>
                {label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
