"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { BookOpen, Download, Heart, LinkIcon, Info, ChevronRight, Library, ShieldCheck, BarChart3, Settings } from "lucide-react"
import { useTelegramContext } from "@/components/telegram-provider"
import { AccessGuard } from "@/components/access-guard"
import { UserLevelBadge } from "@/components/user-level-badge"
import { callBotAPI } from "@/lib/api"

interface BotInfo {
  name: string
  username: string
  description: string
  avatar: string
}

import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TransparentHeader } from "@/components/transparent-header"
import { useTheme } from "@/components/theme-provider"

export default function HomePage() {
  const { user, isAdmin, isAdminMode, setIsAdminMode } = useTelegramContext()
  const { avatarScale } = useTheme()
  const [botInfo, setBotInfo] = useState<BotInfo>({
    name: "ZeePubBot",
    username: "@ZeePubBot",
    description: "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
    avatar: "/robot-librarian.jpg",
  })

  const [businessMode, setBusinessMode] = useState(true)
  const [allowGroups, setAllowGroups] = useState(true)
  const [groupPrivacy, setGroupPrivacy] = useState(true)

  useEffect(() => {
    // Fetch bot info from API
    async function fetchBotInfo() {
      try {
        const info = await callBotAPI("bot_info")
        if (info && info.name) {
          setBotInfo(info)
        }
      } catch (error) {
        console.log("[HomePage] Using default bot info")
      }
    }
    fetchBotInfo()
  }, [])

  useEffect(() => {
    if (user) {
      console.log("[v0] Telegram user loaded:", user)
    }
  }, [user])

  const menuItems = [
    { icon: BookOpen, label: "Buscar Libros", href: "/search", description: "Encuentra ePubs en el catálogo" },
    { icon: Library, label: "Mi Catálogo", href: "/catalog", description: "Accede a bibliotecas OPDS" },
    { icon: Download, label: "Mis Descargas", href: "/downloads", description: "Historial y límites de descarga" },
    { icon: BarChart3, label: "Estado", href: "/status", description: "Ver estado del bot y estadísticas" },
    { icon: LinkIcon, label: "Mis Enlaces", href: "/links", description: "Gestión de links acortados", adminOnly: true },
    { icon: Heart, label: "Donar", href: "/donate", description: "Apoya el proyecto" },
    { icon: Info, label: "Ayuda", href: "/help", description: "Comandos y soporte" },
    { icon: ShieldCheck, label: "Gestión Accesos", href: "/admin/levels", description: "Configura niveles y permisos", adminOnly: true },
  ]

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background pt-safe">
        <TransparentHeader />


        {/* Bot Profile Section */}
        <div className="max-w-2xl mx-auto px-4 py-8">
          {user && (
            <div className="text-center mb-4">
              <p className="text-xs text-muted-foreground">Hola, {user.first_name}</p>
              <div className="mt-1 flex justify-center">
                <UserLevelBadge userId={user.id} />
              </div>
            </div>
          )}

          <div className="flex flex-col items-center text-center mb-5">
            <Avatar
              className="mb-2 border border-primary/20"
              style={{ width: `${56 * avatarScale}px`, height: `${56 * avatarScale}px` }}
            >
              <AvatarImage src={botInfo.avatar || "/placeholder.svg"} alt={botInfo.name} />
              <AvatarFallback className="bg-primary text-primary-foreground text-sm">ZP</AvatarFallback>
            </Avatar>
            {/* Admin toggle oculto en el nombre del bot */}
            <h2
              className={`text-xl font-bold mb-1 ${typeof isAdmin === 'boolean' && isAdmin ? 'cursor-pointer select-none' : ''}`}
              onClick={() => {
                if (typeof isAdmin === 'boolean' && isAdmin) {
                  setIsAdminMode(!isAdminMode)
                }
              }}
            >
              {botInfo.name}
            </h2>
            <p className="text-xs text-muted-foreground mb-2">{botInfo.username}</p>
            <p className="text-xs text-foreground/80 leading-relaxed max-w-xs">{botInfo.description}</p>
          </div>


          {/* Menu Items / Admin Panel */}
          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-xl font-bold mb-4">Funciones</h3>
              {menuItems
                .filter(item => !item.adminOnly)
                .map((item, index) => (
                  <a key={index} href={item.href}>
                    <Card className="p-3 hover:bg-secondary/50 transition-colors cursor-pointer border-border">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <item.icon className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-foreground">{item.label}</h4>
                          <p className="text-xs text-muted-foreground">{item.description}</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
                      </div>
                    </Card>
                  </a>
                ))}
            </div>

            {isAdminMode && (
              <div className="space-y-3 pt-4 border-t border-border">
                <h3 className="text-lg font-bold">Panel Administrador</h3>
                <div className="space-y-2">
                  {/* Apariencia - Solo en Admin Panel */}
                  <a href="/interface-config">
                    <Card className="p-3 hover:bg-secondary/50 transition-colors cursor-pointer border-border">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <Settings className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-foreground">Apariencia</h4>
                          <p className="text-xs text-muted-foreground">Personaliza tema, colores y tamaño</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
                      </div>
                    </Card>
                  </a>

                  {/* Access Management - First Item (Rounded Top) */}
                  <a href="/admin/levels" className="block">
                    <Card className="p-3 bg-card hover:bg-secondary/50 transition-colors cursor-pointer border-border rounded-none rounded-t-xl border-b-0">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <ShieldCheck className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-foreground">Gestión Accesos</h4>
                          <p className="text-xs text-muted-foreground">Configura niveles y permisos</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
                      </div>
                    </Card>
                  </a>

                  {/* Links Management - Middle Item (No border radius) */}
                  <a href="/links" className="block -mt-px">
                    <Card className="p-3 bg-card hover:bg-secondary/50 transition-colors cursor-pointer border-border rounded-none border-b-0">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <LinkIcon className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-foreground">Mis Enlaces</h4>
                          <p className="text-xs text-muted-foreground">Gestión de links acortados</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
                      </div>
                    </Card>
                  </a>

                  {/* Settings Cards - Middle Items (No border radius) */}
                  <Card className="p-3 bg-card border-border rounded-none border-b-0 -mt-px">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="business-mode" className="text-sm font-medium">Business Mode</Label>
                      <Switch id="business-mode" checked={businessMode} onCheckedChange={setBusinessMode} className="scale-75" />
                    </div>
                  </Card>

                  <Card className="p-3 bg-card border-border rounded-none border-b-0 -mt-px">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="allow-groups" className="text-sm font-medium">Permitir Grupos</Label>
                      <Switch id="allow-groups" checked={allowGroups} onCheckedChange={setAllowGroups} className="scale-75" />
                    </div>
                  </Card>

                  {/* Privacy - Last Item (Rounded Bottom) */}
                  <Card className="p-3 bg-card border-border rounded-none rounded-b-xl -mt-px">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="group-privacy" className="text-sm font-medium">Privacidad</Label>
                      <Switch id="group-privacy" checked={groupPrivacy} onCheckedChange={setGroupPrivacy} className="scale-75" />
                    </div>
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
