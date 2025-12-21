"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, BookOpen, Download, Heart, LinkIcon, Info, ChevronRight } from "lucide-react"
import { useTelegramContext } from "@/components/telegram-provider"

interface BotInfo {
  name: string
  username: string
  description: string
  avatar: string
}

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const { user } = useTelegramContext()
  const [botInfo] = useState<BotInfo>({
    name: "ZeePubBot",
    username: "@ZeePubBot",
    description: "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
    avatar: "/robot-librarian.jpg",
  })

  useEffect(() => {
    if (user) {
      console.log("[v0] Telegram user loaded:", user)
    }
  }, [user])

  const menuItems = [
    { icon: BookOpen, label: "Buscar Libros", href: "/search", description: "Encuentra ePubs en el catálogo" },
    { icon: Download, label: "Mis Descargas", href: "/downloads", description: "Historial y límites de descarga" },
    { icon: LinkIcon, label: "Mis Enlaces", href: "/links", description: "Gestión de links acortados" },
    { icon: Heart, label: "Donar", href: "/donate", description: "Apoya el proyecto" },
    { icon: Info, label: "Ayuda", href: "/help", description: "Comandos y soporte" },
  ]

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <h1 className="text-lg font-semibold text-center">ZeePubBot</h1>
          {user && <p className="text-xs text-center text-muted-foreground mt-0.5">Hola, {user.first_name}</p>}
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
        </div>

        {/* Search */}
        <div className="mb-8">
          <a href="/search">
            <div className="relative cursor-pointer">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none" />
              <Input
                type="text"
                placeholder="Buscar libros..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                readOnly
                className="pl-12 h-12 bg-card border-border rounded-xl cursor-pointer"
              />
            </div>
          </a>
        </div>

        {/* Menu Items */}
        <div className="space-y-3">
          <h3 className="text-xl font-bold mb-4">Funciones</h3>

          {menuItems.map((item, index) => (
            <a key={index} href={item.href}>
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
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
