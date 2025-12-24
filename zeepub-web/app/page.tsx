"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, BookOpen, Download, Heart, LinkIcon, Info, ChevronRight, Library, ShieldCheck } from "lucide-react"
import { useTelegramContext } from "@/components/telegram-provider"
import { AccessGuard } from "@/components/access-guard"

interface BotInfo {
  name: string
  username: string
  description: string
  avatar: string
}

import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const { user, isAdmin, isAdminMode, setIsAdminMode } = useTelegramContext()
  const [botInfo] = useState<BotInfo>({
    name: "ZeePubBot",
    username: "@ZeePubBot",
    description: "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
    avatar: "/robot-librarian.jpg",
  })

  const [businessMode, setBusinessMode] = useState(true)
  const [allowGroups, setAllowGroups] = useState(true)
  const [groupPrivacy, setGroupPrivacy] = useState(true)

  useEffect(() => {
    if (user) {
      console.log("[v0] Telegram user loaded:", user)
    }
  }, [user])

  const menuItems = [
    { icon: BookOpen, label: "Buscar Libros", href: "/search", description: "Encuentra ePubs en el catálogo" },
    { icon: Library, label: "Mi Catálogo", href: "/catalog", description: "Accede a bibliotecas OPDS" },
    { icon: Download, label: "Mis Descargas", href: "/downloads", description: "Historial y límites de descarga" },
    { icon: LinkIcon, label: "Mis Enlaces", href: "/links", description: "Gestión de links acortados", adminOnly: true },
    { icon: Heart, label: "Donar", href: "/donate", description: "Apoya el proyecto" },
    { icon: Info, label: "Ayuda", href: "/help", description: "Comandos y soporte" },
    { icon: ShieldCheck, label: "Gestión Accesos", href: "/admin/levels", description: "Configura niveles y permisos", adminOnly: true },
  ]

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
          <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex-1" />
            <h1 className="text-lg font-semibold text-center flex-1">ZeePubBot</h1>
            <div className="flex-1 flex justify-end">
              {isAdmin && (
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Admin</span>
                  <Switch
                    checked={isAdminMode}
                    onCheckedChange={setIsAdminMode}
                    className="scale-75"
                  />
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Bot Profile Section */}
        <div className="max-w-2xl mx-auto px-4 py-8">
          {user && (
            <div className="text-center mb-4">
              <p className="text-xs text-muted-foreground">Hola, {user.first_name}</p>
            </div>
          )}

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
          {!isAdminMode && (
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
          )}

          {/* Menu Items / Admin Panel */}
          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-xl font-bold mb-4">Funciones</h3>
              {menuItems
                .filter(item => !item.adminOnly)
                .map((item, index) => (
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

            {isAdminMode && (
              <div className="space-y-4 pt-4 border-t border-border">
                <h3 className="text-xl font-bold">Panel Administrador</h3>
                <div className="space-y-4">
                  {/* Access Management */}
                  <a href="/admin/levels">
                    <Card className="p-4 border-primary/20 bg-primary/5 hover:bg-primary/10 transition-colors cursor-pointer border-border">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <ShieldCheck className="w-6 h-6 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-foreground mb-1">Gestión Accesos</h4>
                          <p className="text-sm text-muted-foreground">Configura niveles y permisos</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    </Card>
                  </a>

                  {/* Links Management */}
                  <a href="/links">
                    <Card className="p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <LinkIcon className="w-6 h-6 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-foreground mb-1">Mis Enlaces</h4>
                          <p className="text-sm text-muted-foreground">Gestión de links acortados</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    </Card>
                  </a>

                  {/* Settings Cards */}
                  <Card className="p-4 border-border">
                    <div className="flex items-center justify-between mb-2">
                      <Label htmlFor="business-mode" className="font-semibold">Business Mode</Label>
                      <Switch id="business-mode" checked={businessMode} onCheckedChange={setBusinessMode} />
                    </div>
                    <p className="text-xs text-muted-foreground">Manejo automático de mensajes en cuentas de usuario</p>
                  </Card>

                  <Card className="p-4 border-border">
                    <div className="flex items-center justify-between mb-2">
                      <Label htmlFor="allow-groups" className="font-semibold">Permitir Grupos</Label>
                      <Switch id="allow-groups" checked={allowGroups} onCheckedChange={setAllowGroups} />
                    </div>
                    <p className="text-xs text-muted-foreground">Habilitar el bot en chats grupales</p>
                  </Card>

                  <Card className="p-4 border-border">
                    <div className="flex items-center justify-between mb-2">
                      <Label htmlFor="group-privacy" className="font-semibold">Privacidad</Label>
                      <Switch id="group-privacy" checked={groupPrivacy} onCheckedChange={setGroupPrivacy} />
                    </div>
                    <p className="text-xs text-muted-foreground">Limitar mensajes leídos en grupos</p>
                  </Card>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AccessGuard>
  )
}
