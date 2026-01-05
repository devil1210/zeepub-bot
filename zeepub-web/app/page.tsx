"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { BookOpen, Download, Heart, LinkIcon, Info, ChevronRight, Library, ShieldCheck, BarChart3, Settings, Search, Palette } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTelegramContext } from "@/components/telegram-provider"
import { useStrings } from "@/components/strings-provider"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { AccessGuard } from "@/components/access-guard"
import { UserLevelBadge } from "@/components/user-level-badge"
import { callBotAPI } from "@/lib/api"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { TransparentHeader } from "@/components/transparent-header"
import { useTheme } from "@/components/theme-provider"

interface BotInfo {
  name: string
  username: string
  description: string
  avatar: string
}

export default function HomePage() {
  const {
    user,
    isAdmin,
    isAdminMode,
    setIsAdminMode,
    publishTarget,
    setPublishTarget,
    targetId,
    setTargetId,
    threadId,
    setThreadId
  } = useTelegramContext()
  const { t } = useStrings()
  const { avatarScale, showSearchCard, showSearchBar, showDonateCard, showHelpCard, showSettingsInMenu } = useTheme()
  const router = useRouter()
  const [homeSearchQuery, setHomeSearchQuery] = useState("")

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

  const menuItems = [
    { icon: BookOpen, label: t("menu_search_label"), href: "/search", description: t("menu_search_desc"), id: "search" },
    { icon: Library, label: t("menu_catalog_label"), href: "/catalog", description: t("menu_catalog_desc"), id: "catalog" },
    { icon: Download, label: t("menu_downloads_label"), href: "/downloads", description: t("menu_downloads_desc"), id: "downloads" },
    { icon: BarChart3, label: t("menu_status_label"), href: "/status", description: t("menu_status_desc"), id: "status" },
    { icon: Palette, label: "Apariencia", href: "/interface-config", description: "Personaliza tu interfaz", id: "appearance" },
    { icon: LinkIcon, label: "Mis Enlaces", href: "/links", description: "Gestión de links acortados", adminOnly: true, id: "links" },
    { icon: Heart, label: t("menu_donate_label"), href: "/donate", description: t("menu_donate_desc"), id: "donate" },
    { icon: Info, label: t("menu_help_label"), href: "/help", description: t("menu_help_desc"), id: "help" },
    { icon: ShieldCheck, label: "Gestión Accesos", href: "/admin/levels", description: "Configura niveles y permisos", adminOnly: true, id: "admin" },
  ]

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background pt-safe">
        <TransparentHeader />

        <div className="max-w-2xl mx-auto px-4 py-8">
          {user && (
            <div className="text-center mb-4">
              <p className="text-xs text-muted-foreground">{t("home_greeting", { Nombre: user.first_name })}</p>
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

          <div className="space-y-6">
            <div className="space-y-3">
              {showSearchBar && (
                <div className="mb-6 relative group">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 z-10">
                    <Search className="w-5 h-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                  </div>
                  <Input
                    type="text"
                    placeholder={t("search_placeholder")}
                    value={homeSearchQuery}
                    onChange={(e) => setHomeSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && homeSearchQuery.trim()) {
                        router.push(`/search?q=${encodeURIComponent(homeSearchQuery)}`)
                      }
                    }}
                    className="pl-12 h-14 bg-card border-border rounded-2xl shadow-sm focus-visible:ring-primary/20 transition-all text-base"
                  />
                  {homeSearchQuery.trim() && (
                    <Button
                      onClick={() => router.push(`/search?q=${encodeURIComponent(homeSearchQuery)}`)}
                      size="sm"
                      className="absolute right-2 top-1/2 -translate-y-1/2 h-10 px-4 rounded-xl bg-primary text-primary-foreground font-bold shadow-md shadow-primary/20 animate-in fade-in zoom-in duration-200"
                    >
                      {t("search_button")}
                    </Button>
                  )}
                </div>
              )}

              <h3 className="text-xl font-bold mb-4">{t("home_functions")}</h3>
              {menuItems
                .filter(item => {
                  if (item.adminOnly && !isAdminMode) return false
                  if (item.id === "search" && !showSearchCard) return false
                  if (item.id === "donate" && !showDonateCard) return false
                  if (item.id === "help" && !showHelpCard) return false
                  if (item.id === "appearance" && !showSettingsInMenu) return false
                  return true
                })
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
                <h3 className="text-lg font-bold">{t("home_admin_panel")}</h3>
                <div className="space-y-2">
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

                  <Card className="p-3 bg-card border-border rounded-none rounded-b-xl -mt-px border-b">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="group-privacy" className="text-sm font-medium">Privacidad</Label>
                      <Switch id="group-privacy" checked={groupPrivacy} onCheckedChange={setGroupPrivacy} className="scale-75" />
                    </div>
                  </Card>

                  <div className="pt-2">
                    <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block px-1">
                      {t("home_admin_publish_title")}
                    </Label>
                    <Tabs value={publishTarget} onValueChange={setPublishTarget} className="w-full">
                      <TabsList className="grid w-full grid-cols-3 bg-secondary/30 h-10 p-1">
                        <TabsTrigger value="private" className="text-xs data-[state=active]:bg-primary data-[state=active]:text-white">
                          {t("home_admin_publish_private")}
                        </TabsTrigger>
                        <TabsTrigger value="channel" className="text-xs data-[state=active]:bg-primary data-[state=active]:text-white">
                          {t("home_admin_publish_channel")}
                        </TabsTrigger>
                        <TabsTrigger value="group" className="text-xs data-[state=active]:bg-primary data-[state=active]:text-white">
                          {t("home_admin_publish_group")}
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>

                  <div className="space-y-3 pt-2">
                    <div className="space-y-1.5">
                      <Label htmlFor="target-id" className="text-xs font-medium px-1">
                        {t("home_admin_publish_id")}
                      </Label>
                      <Input
                        id="target-id"
                        placeholder="ej: -100123456789"
                        value={targetId}
                        onChange={(e) => setTargetId(e.target.value)}
                        className="h-9 bg-secondary/20 border-border/50 text-sm focus-visible:ring-primary/30"
                      />
                    </div>
                    {publishTarget === "group" && (
                      <div className="space-y-1.5">
                        <Label htmlFor="thread-id" className="text-xs font-medium px-1">
                          {t("home_admin_publish_topic")}
                        </Label>
                        <Input
                          id="thread-id"
                          placeholder="ej: 1234"
                          value={threadId}
                          onChange={(e) => setThreadId(e.target.value)}
                          className="h-9 bg-secondary/20 border-border/50 text-sm focus-visible:ring-primary/30"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AccessGuard>
  )
}
