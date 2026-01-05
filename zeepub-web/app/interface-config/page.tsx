"use client"

import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Info, Moon, Sun, Monitor, Type, UserCircle, BookOpen, Heart, HelpCircle, Palette, Save, Globe, AlertTriangle, Search, CreditCard, RotateCcw, Check } from "lucide-react"
import { AccessGuard } from "@/components/access-guard"
import { TransparentHeader } from "@/components/transparent-header"
import { useTheme } from "@/components/theme-provider"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { useStrings } from "@/components/strings-provider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import { useTelegramContext } from "@/components/telegram-provider"
import { useState, useEffect } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Paleta de colores predefinidos
const colorPresets = [
    { name: "Azul", value: "#3b82f6", dark: "#60a5fa" },
    { name: "Verde", value: "#22c55e", dark: "#4ade80" },
    { name: "Púrpura", value: "#a855f7", dark: "#c084fc" },
    { name: "Rosa", value: "#ec4899", dark: "#f472b6" },
    { name: "Naranja", value: "#f97316", dark: "#fb923c" },
    { name: "Rojo", value: "#ef4444", dark: "#f87171" },
]

export default function InterfaceConfigPage() {
    // Use global theme context
    const {
        isDarkMode,
        setIsDarkMode,
        primaryColor,
        setPrimaryColor,
        uiScale,
        setUiScale,
        avatarScale,
        setAvatarScale,
        showSearchCard,
        setShowSearchCard,
        showSearchBar,
        setShowSearchBar,
        showDonateCard,
        setShowDonateCard,
        showHelpCard,
        setShowHelpCard,
        showSettingsInMenu,
        setShowSettingsInMenu,
        saveGlobalSettings,
        applySettings,
    } = useTheme()

    const { isAdmin, userProfile } = useTelegramContext()
    const [editTarget, setEditTarget] = useState("personal")
    const [isSaving, setIsSaving] = useState(false)
    const [botAvatar, setBotAvatar] = useState("/robot-librarian.jpg")

    // Fetch bot avatar for preview and SYNC personal settings
    useEffect(() => {
        const init = async () => {
            try {
                // Apply personal settings immediately from localStorage
                // ThemeProvider already does this, but we force a sync check
                const { callBotAPI } = await import("@/lib/api")
                const info = await callBotAPI("bot_info")
                if (info && info.avatar) {
                    setBotAvatar(info.avatar)
                }
            } catch (error) {
                console.error("Error initializing config page:", error)
            }
        }
        init()
    }, [])

    // Handle target context change
    const handleTargetChange = async (newTarget: string) => {
        setEditTarget(newTarget)

        if (newTarget === "personal") {
            // Restore personal settings from localStorage
            const personal = {
                isDarkMode: localStorage.getItem("theme") === "dark",
                primaryColor: localStorage.getItem("primaryColor") || "#3b82f6",
                uiScale: parseFloat(localStorage.getItem("uiScale") || "1"),
                avatarScale: parseFloat(localStorage.getItem("avatarScale") || "1"),
                showSearchCard: localStorage.getItem("showSearchCard") === "true",
                showSearchBar: localStorage.getItem("showSearchBar") === "true",
                showDonateCard: localStorage.getItem("showDonateCard") === "true",
                showHelpCard: localStorage.getItem("showHelpCard") === "true",
                showSettingsInMenu: localStorage.getItem("showSettingsInMenu") === "true"
            }
            applySettings(personal, true) // Restore and ENABLE persistence
            toast.info("Has vuelto a tu configuración personal")
        } else {
            // Fetch defaults for the selected level
            try {
                const { callBotAPI } = await import("@/lib/api")
                const data = await callBotAPI("ui_settings", { subAction: "get", role: newTarget })
                if (data) {
                    applySettings(data, false) // Apply but DISABLE persistence to localStorage during edit
                    toast.info(`Cargada configuración para: ${newTarget === 'global' ? 'Global' : `Nivel ${newTarget.toUpperCase()}`}`)
                }
            } catch (error) {
                console.error("Error loading level settings:", error)
                toast.error("No se pudo cargar la configuración del nivel")
            }
        }
    }

    const handleSaveLevel = async () => {
        setIsSaving(true)
        try {
            if (editTarget === "personal") {
                await saveGlobalSettings("personal")
                toast.success("Tu configuración personal ha sido guardada en la nube")
            } else {
                await saveGlobalSettings(editTarget)
                toast.success(`Configuración guardada correctamente para ${editTarget === 'global' ? 'Todos' : `el nivel ${editTarget.toUpperCase()}`}`)
            }
        } catch (error) {
            toast.error("Error al guardar la configuración en el servidor")
        } finally {
            setIsSaving(false)
        }
    }

    const handleResetToLevelDefaults = async () => {
        setIsSaving(true)
        try {
            const { callBotAPI } = await import("@/lib/api")
            // Determine user effective role from profile
            const role = userProfile?.level?.id || "free"
            const data = await callBotAPI("ui_settings", { subAction: "get", role: role })
            if (data) {
                applySettings(data, true) // Apply AND allow persistence
                await saveGlobalSettings("personal") // OVERWRITE personal in DB with these role defaults
                toast.success("Tu configuración ha sido restablecida a los valores oficiales de tu nivel")
            }
        } catch (error) {
            console.error("Error resetting to defaults:", error)
            toast.error("No se pudo obtener la configuración oficial del nivel")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <AccessGuard>
            <div className="min-h-screen bg-background pt-safe">
                <TransparentHeader />

                <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
                    {/* Selector de Objetivo (Solo Admins) */}
                    {isAdmin && (
                        <Card className="p-4 border-2 border-primary/30 bg-primary/10 rounded-2xl shadow-lg">
                            <div className="flex items-center gap-3 mb-4">
                                <Globe className="w-5 h-5 text-primary" />
                                <Label className="text-lg font-bold">Configurar para:</Label>
                            </div>
                            <div className="space-y-4">
                                <Select value={editTarget} onValueChange={handleTargetChange}>
                                    <SelectTrigger className="w-full bg-card h-12 rounded-xl text-md font-medium">
                                        <SelectValue placeholder="Selecciona nivel o contexto" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="personal" className="font-bold text-primary">Para ti (Personal)</SelectItem>
                                        <Separator className="my-2" />
                                        <SelectItem value="global">Todos los usuarios (Global)</SelectItem>
                                        <SelectItem value="admin">Nivel: Administrador</SelectItem>
                                        <SelectItem value="staff">Nivel: Staff</SelectItem>
                                        <SelectItem value="premium">Nivel: Premium</SelectItem>
                                        <SelectItem value="vip">Nivel: VIP</SelectItem>
                                        <SelectItem value="white">Nivel: Patrocinador</SelectItem>
                                        <SelectItem value="free">Nivel: Lector (Free)</SelectItem>
                                    </SelectContent>
                                </Select>

                                {editTarget === "personal" ? (
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            className="flex-1 bg-card border-primary/20 hover:bg-primary/5 text-primary text-xs h-10 rounded-xl"
                                            onClick={handleResetToLevelDefaults}
                                            disabled={isSaving}
                                        >
                                            <Palette className="w-4 h-4 mr-2" />
                                            Restablecer a valores del nivel
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                                        <Info className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                                        <div className="space-y-1">
                                            <p className="text-sm font-semibold text-amber-500">Modo de Edición de Nivel</p>
                                            <p className="text-xs text-amber-200/80 leading-relaxed">
                                                ⚠️ A partir de este momento se cambiara la configuracion para <strong>{editTarget === 'global' ? 'todos los usuarios' : `el nivel ${editTarget.toUpperCase()}`}</strong>.
                                                Los cambios que realices a continuación solo se aplicarán permanentemente cuando pulses el botón de guardar.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </Card>
                    )}

                    {/* Banner de aviso cuando se edita un nivel */}
                    {editTarget !== "personal" && (
                        <Alert className="bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400">
                            <AlertTriangle className="w-4 h-4" />
                            <AlertTitle>Editando nivel {editTarget.toUpperCase()}</AlertTitle>
                            <AlertDescription>
                                Los cambios afectarán a todos los usuarios de este nivel que no tengan una configuración personal guardada.
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Previsualización */}
                    <Card className="p-6 border-border shadow-sm overflow-hidden relative">
                        <Label className="text-lg font-bold mb-4 block">Previsualización</Label>
                        <div className="relative z-10 bg-background/50 backdrop-blur-sm rounded-xl p-4 border border-border/50">
                            <Avatar
                                className="border-2 border-primary shadow-lg transition-all mx-auto mb-4"
                                style={{
                                    width: `${80 * avatarScale}px`,
                                    height: `${80 * avatarScale}px`
                                }}
                            >
                                <AvatarImage src={botAvatar} alt="Bot Avatar" />
                                <AvatarFallback className="bg-primary/20 text-primary font-bold" style={{ fontSize: `${24 * avatarScale}px` }}>
                                    ZP
                                </AvatarFallback>
                            </Avatar>
                            <div className="text-center space-y-2">
                                <h3 className="font-bold text-xl text-foreground">ZeePub Bot</h3>
                                <p className="text-sm text-muted-foreground">Asistente de lectura digital</p>
                                <div className="flex justify-center gap-2 mt-4">
                                    <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">
                                        Demo
                                    </Badge>
                                    <Badge variant="outline" className="border-primary/50 text-primary">
                                        v1.0
                                    </Badge>
                                </div>
                            </div>
                        </div>

                        {/* Background pattern preview */}
                        <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
                            style={{
                                backgroundImage: `radial-gradient(circle at 1px 1px, ${primaryColor} 1px, transparent 0)`,
                                backgroundSize: '24px 24px'
                            }}
                        />
                    </Card>

                    <Tabs defaultValue="appearance" className="w-full">
                        <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="appearance">Apariencia</TabsTrigger>
                            <TabsTrigger value="interface">Interfaz</TabsTrigger>
                        </TabsList>

                        <TabsContent value="appearance" className="space-y-6 mt-6">
                            {/* Tema */}
                            <Card className="p-6 border-border">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        {isDarkMode ? (
                                            <Moon className="w-5 h-5 text-primary" />
                                        ) : (
                                            <Sun className="w-5 h-5 text-primary" />
                                        )}
                                        <div>
                                            <Label className="text-base font-semibold">Tema</Label>
                                            <p className="text-xs text-muted-foreground">
                                                Cambiar entre modo claro y oscuro
                                            </p>
                                        </div>
                                    </div>
                                    <Switch
                                        checked={isDarkMode}
                                        onCheckedChange={setIsDarkMode}
                                        className="scale-110"
                                    />
                                </div>
                                <div className="text-sm text-muted-foreground">
                                    {isDarkMode ? "Modo Oscuro" : "Modo Claro"}
                                </div>
                            </Card>

                            {/* Color Principal */}
                            <div className="space-y-4">
                                <Label className="text-base">Color Principal</Label>
                                <div className="grid grid-cols-5 gap-3">
                                    {[
                                        { color: "#3b82f6", name: "Azul" },
                                        { color: "#ef4444", name: "Rojo" },
                                        { color: "#10b981", name: "Verde" },
                                        { color: "#f59e0b", name: "Ámbar" },
                                        { color: "#8b5cf6", name: "Violeta" },
                                        { color: "#ec4899", name: "Rosa" },
                                        { color: "#06b6d4", name: "Cian" },
                                        { color: "#f97316", name: "Naranja" },
                                        { color: "#64748b", name: "Pizarra" },
                                        { color: "#171717", name: "Neutro" },
                                    ].map((c) => (
                                        <button
                                            key={c.color}
                                            onClick={() => setPrimaryColor(c.color)}
                                            className={`
                                                w-full aspect-square rounded-full flex items-center justify-center transition-all
                                                ${primaryColor === c.color ? 'ring-2 ring-offset-2 ring-primary scale-110 shadow-lg' : 'hover:scale-105 hover:shadow-md'}
                                            `}
                                            style={{ backgroundColor: c.color }}
                                            title={c.name}
                                        >
                                            {primaryColor === c.color && <Check className="w-4 h-4 text-white drop-shadow-md" />}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Escala UI */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label className="text-base">Escala de Interfaz</Label>
                                    <span className="text-sm text-muted-foreground">{Math.round(uiScale * 100)}%</span>
                                </div>
                                <Slider
                                    value={[uiScale]}
                                    min={0.8}
                                    max={1.2}
                                    step={0.05}
                                    onValueChange={(val) => setUiScale(val[0])}
                                />
                                <div className="flex justify-between text-xs text-muted-foreground px-1">
                                    <span>Pequeño</span>
                                    <span>Normal</span>
                                    <span>Grande</span>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="interface" className="space-y-6 mt-6">
                            {/* Avatar Scale */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label className="text-base">Tamaño del Avatar</Label>
                                    <span className="text-sm text-muted-foreground">{Math.round(avatarScale * 100)}%</span>
                                </div>
                                <Slider
                                    value={[avatarScale]}
                                    min={0.8}
                                    max={1.5}
                                    step={0.1}
                                    onValueChange={(val) => setAvatarScale(val[0])}
                                />
                            </div>

                            {/* Toggles de Visibilidad */}
                            <div className="space-y-4">
                                <Label className="text-base mb-2 block">Elementos Visibles</Label>

                                <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <Search className="w-5 h-5 text-primary" />
                                        <Label htmlFor="show-search-card" className="font-medium">Tarjeta de Búsqueda</Label>
                                    </div>
                                    <Switch id="show-search-card" checked={showSearchCard} onCheckedChange={setShowSearchCard} />
                                </div>

                                <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <Search className="w-5 h-5 text-primary" />
                                        <Label htmlFor="show-search-bar" className="font-medium">Barra Flotante</Label>
                                    </div>
                                    <Switch id="show-search-bar" checked={showSearchBar} onCheckedChange={setShowSearchBar} />
                                </div>

                                <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <CreditCard className="w-5 h-5 text-primary" />
                                        <Label htmlFor="show-donate-card" className="font-medium">Tarjeta de Donación</Label>
                                    </div>
                                    <Switch id="show-donate-card" checked={showDonateCard} onCheckedChange={setShowDonateCard} />
                                </div>

                                <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <HelpCircle className="w-5 h-5 text-primary" />
                                        <Label htmlFor="show-help-card" className="font-medium">Tarjeta de Ayuda</Label>
                                    </div>
                                    <Switch id="show-help-card" checked={showHelpCard} onCheckedChange={setShowHelpCard} />
                                </div>

                                {editTarget !== "personal" && (
                                    <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                        <div className="flex items-center gap-3">
                                            <Palette className="w-5 h-5 text-primary" />
                                            <Label htmlFor="show-settings-in-menu" className="font-medium">Shortcut de Apariencia en Menú</Label>
                                        </div>
                                        <Switch id="show-settings-in-menu" checked={showSettingsInMenu} onCheckedChange={setShowSettingsInMenu} />
                                    </div>
                                )}
                            </div>
                        </TabsContent>
                    </Tabs>

                    <div className="sticky bottom-6 z-50 px-2 pb-2">
                        <Button
                            className="w-full h-14 rounded-2xl text-lg font-bold shadow-2xl shadow-primary/40 border-2 border-primary/50 relative overflow-hidden group"
                            onClick={handleSaveLevel}
                            disabled={isSaving}
                        >
                            <div className="absolute inset-0 bg-primary/20 group-hover:bg-primary/30 transition-colors" />
                            <span className="relative flex items-center justify-center gap-2">
                                {isSaving ? "Guardando..." : `Guardar ${editTarget === 'personal' ? 'Cambios' : `para ${editTarget.toUpperCase()}`}`}
                                <Save className="w-6 h-6" />
                            </span>
                        </Button>

                        {editTarget === 'personal' && (
                            <Button
                                variant="ghost"
                                className="w-full mt-2 text-muted-foreground hover:text-foreground hover:bg-transparent"
                                onClick={handleResetToLevelDefaults}
                                disabled={isSaving}
                            >
                                <RotateCcw className="w-4 h-4 mr-2" />
                                Restablecer a valores del nivel
                            </Button>
                        )}
                    </div>

                    {/* Información */}
                    <Card className="p-4 border-border bg-primary/5">
                        <p className="text-xs text-muted-foreground text-center">
                            {editTarget === 'personal'
                                ? "Las configuraciones se guardan automáticamente y se aplicarán en toda la aplicación"
                                : "En modo de edición de nivel, los cambios solo se guardan cuando pulsas el botón de guardar"}
                        </p>
                    </Card>
                </div>
            </div>
        </AccessGuard>
    )
}
