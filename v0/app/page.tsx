"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, BookOpen, Settings, Info, Download, Heart, LinkIcon, ChevronRight } from "lucide-react"
import Link from "next/link"

interface BotInfo {
  name: string
  username: string
  description: string
  avatar: string
}

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [botInfo, setBotInfo] = useState<BotInfo>({
    name: "ZeePubBot",
    username: "@ZeePubBot",
    description: "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
    avatar: "/robot-librarian.jpg",
  })

  const menuItems = [
    { icon: BookOpen, label: "Buscar Libros", href: "/search", description: "Encuentra ePubs en el catálogo" },
    { icon: Download, label: "Mis Descargas", href: "/downloads", description: "Historial y límites de descarga" },
    { icon: Settings, label: "Configuración", href: "/settings", description: "Preferencias del bot" },
    { icon: LinkIcon, label: "Mis Enlaces", href: "/links", description: "Gestión de links acortados" },
    { icon: Heart, label: "Donar", href: "/donate", description: "Apoya el proyecto" },
    { icon: Info, label: "Ayuda", href: "/help", description: "Comandos y soporte" },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <button className="text-foreground/60">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <h1 className="text-lg font-semibold">ZeePubBot</h1>
          <button className="text-foreground/60">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="1" />
              <circle cx="12" cy="5" r="1" />
              <circle cx="12" cy="19" r="1" />
            </svg>
          </button>
        </div>
      </header>

      {/* Bot Profile Section */}
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="flex flex-col items-center text-center mb-8">
          <Avatar className="w-24 h-24 mb-4 border-2 border-primary/20">
            <AvatarImage src={botInfo.avatar || "/placeholder.svg"} alt={botInfo.name} />
            <AvatarFallback className="bg-primary text-primary-foreground text-2xl">ZP</AvatarFallback>
          </Avatar>
          <h2 className="text-3xl font-bold mb-2">{botInfo.name}</h2>
          <p className="text-muted-foreground mb-4">{botInfo.username}</p>
          <p className="text-sm text-foreground/80 leading-relaxed max-w-md">{botInfo.description}</p>
          <button className="text-primary text-sm mt-2 hover:underline">Leer más →</button>
        </div>

        {/* Search */}
        <div className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Buscar"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 bg-card border-border rounded-xl"
            />
          </div>
        </div>

        {/* Menu Items */}
        <div className="space-y-3">
          <h3 className="text-xl font-bold mb-4">Funciones</h3>

          {menuItems.map((item, index) => (
            <Link key={index} href={item.href}>
              <Card className="p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-foreground mb-1">{item.label}</h4>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 space-y-3">
          <h3 className="text-xl font-bold mb-4">Acceso Rápido</h3>
          <Link href="/status">
            <Button className="w-full h-14 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl text-base font-medium">
              Ver Estado del Bot
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
