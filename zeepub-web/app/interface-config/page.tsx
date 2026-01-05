"use client"

import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Info, Moon, Sun, Monitor, Type, UserCircle, BookOpen, Heart, HelpCircle, Palette, Save, Globe } from "lucide-react"
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

    const { isAdmin } = useTelegramContext()
    const [editTarget, setEditTarget] = useState("personal")
    const [isSaving, setIsSaving] = useState(false)
    const [botAvatar, setBotAvatar] = useState("/robot-librarian.jpg")

    // Fetch bot avatar for preview and SYNC personal settings
    useEffect(() => {
        const init = async () => {
            try {
                // Apply personal settings immediately to ensure we are in a clean state
                const personal = {
                    isDarkMode: localStorage.getItem("theme") === "dark",
                    primaryColor: localStorage.getItem("primaryColor") || "#3b82f6",
                    uiScale: parseFloat(localStorage.getItem("uiScale") || "1"),
                    avatarScale: parseFloat(localStorage.getItem("avatarScale") || "1"),
                    showSearchCard: localStorage.getItem("showSearchCard") !== "false", // default true
                    showSearchBar: localStorage.getItem("showSearchBar") === "true",
                    showDonateCard: localStorage.getItem("showDonateCard") !== "false", // default true
                    showHelpCard: localStorage.getItem("showHelpCard") !== "false", // default true
                    showSettingsInMenu: localStorage.getItem("showSettingsInMenu") === "true"
                }
                applySettings(personal, true)

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
        if (editTarget === "personal") return

        setIsSaving(true)
        try {
            await saveGlobalSettings(editTarget)
            toast.success(`Configuración guardada correctamente para ${editTarget === 'global' ? 'Todos' : `el nivel ${editTarget.toUpperCase()}`}`)
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
            const data = await callBotAPI("ui_settings", { subAction: "get", role: "auto" })
            if (data) {
                applySettings(data, true) // Apply AND persist as personal
                toast.success("Tu configuración ha sido restablecida a los valores de tu nivel")
            }
        } catch (error) {
            toast.error("No se pudo obtener la configuración del nivel")
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

                    {/* Selector de Tema */}
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

                    {/* Selector de Color Principal */}
                    <Card className="p-6 border-border">
                        <div className="flex items-center gap-3 mb-4">
                            <Palette className="w-5 h-5 text-primary" />
                            <div>
                                <Label className="text-base font-semibold">Color Principal</Label>
                                <p className="text-xs text-muted-foreground">
                                    Personaliza el color de acento de la interfaz
                                </p>
                            </div>
                        </div>
                        <div className="grid grid-cols-6 gap-3 mt-4">
                            {colorPresets.map((color) => {
                                const colorValue = isDarkMode ? color.dark : color.value
                                const isSelected = primaryColor === colorValue
                                return (
                                    <button
                                        key={color.name}
                                        onClick={() => setPrimaryColor(colorValue)}
                                        className={`
                                            relative h-12 rounded-lg transition-all
                                            ${isSelected ? "ring-2 ring-offset-2 ring-offset-background ring-white scale-110" : "hover:scale-105"}
                                        `}
                                        style={{ backgroundColor: colorValue }}
                                        aria-label={color.name}
                                    >
                                        {isSelected && (
                                            <div className="absolute inset-0 flex items-center justify-center">
                                                <div className="w-2 h-2 bg-white rounded-full" />
                                            </div>
                                        )}
                                    </button>
                                )
                            })}
                        </div>

                        {/* Custom Color Picker */}
                        <div className="mt-4 flex items-center gap-3 flex-wrap">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="color"
                                    value={primaryColor.startsWith('#') ? primaryColor : `#${primaryColor}`}
                                    onChange={(e) => setPrimaryColor(e.target.value)}
                                    className="w-12 h-12 rounded-lg border-2 border-border cursor-pointer bg-transparent"
                                    style={{ padding: 0 }}
                                />
                                <span className="text-sm text-muted-foreground">Personalizado</span>
                            </label>
                            <div className="flex items-center gap-1">
                                <span className="text-muted-foreground">#</span>
                                <input
                                    type="text"
                                    value={primaryColor.replace('#', '').toUpperCase()}
                                    onChange={(e) => {
                                        const val = e.target.value.replace(/[^0-9A-Fa-f]/g, '').slice(0, 6)
                                        if (val.length === 6 || val.length === 3) {
                                            setPrimaryColor(`#${val}`)
                                        } else if (val.length > 0) {
                                            setPrimaryColor(`#${val}`)
                                        }
                                    }}
                                    placeholder="3B82F6"
                                    className="w-20 px-2 py-1 text-xs font-mono bg-secondary border border-border rounded text-foreground uppercase"
                                    maxLength={6}
                                />
                            </div>
                        </div>

                        <div className="mt-3 text-sm text-muted-foreground text-center">
                            {colorPresets.find((c) => c.value === primaryColor || c.dark === primaryColor)?.name || "Personalizado"}
                        </div>
                    </Card>

                    {/* Slider de Tamaño de Avatar */}
                    <Card className="p-6 border-border">
                        <div className="mb-6">
                            <Label className="text-base font-semibold">Tamaño del Avatar</Label>
                            <p className="text-xs text-muted-foreground mt-1">
                                Ajusta el tamaño del avatar del bot en la página principal
                            </p>
                        </div>
                        <div className="space-y-4">
                            <Slider
                                value={[avatarScale]}
                                onValueChange={(value) => setAvatarScale(value[0])}
                                min={0.6}
                                max={1.4}
                                step={0.1}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Pequeño (60%)</span>
                                <span className="font-semibold text-foreground">
                                    {Math.round(avatarScale * 100)}%
                                </span>
                                <span>Grande (140%)</span>
                            </div>
                            {/* Avatar preview */}
                            <div className="flex justify-center mt-4">
                                <Avatar
                                    className="border-2 border-primary shadow-lg transition-all"
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
                            </div>
                        </div>
                    </Card>

                    {/* Slider de Escala de UI */}
                    <Card className="p-6 border-border">
                        <div className="mb-6">
                            <Label className="text-base font-semibold">Tamaño de Interfaz</Label>
                            <p className="text-xs text-muted-foreground mt-1">
                                Ajusta el tamaño general de texto y elementos
                            </p>
                        </div>
                        <div className="space-y-4">
                            <Slider
                                value={[uiScale]}
                                onValueChange={(value) => setUiScale(value[0])}
                                min={0.8}
                                max={1.2}
                                step={0.05}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Pequeño (80%)</span>
                                <span className="font-semibold text-foreground">
                                    {Math.round(uiScale * 100)}%
                                </span>
                                <span>Grande (120%)</span>
                            </div>
                            <div className="mt-4 p-4 bg-secondary/20 rounded-lg border border-border">
                                <p
                                    className="text-sm"
                                    style={{
                                        fontSize: `calc(0.875rem * ${uiScale})`,
                                        lineHeight: `calc(1.25rem * ${uiScale})`,
                                    }}
                                >
                                    Vista previa del tamaño de texto actual
                                </p>
                            </div>
                        </div>
                    </Card>

                    {/* Configuración de Búsqueda */}
                    <Card className="p-6 border-border">
                        <div className="flex items-center gap-3 mb-6">
                            <BookOpen className="w-5 h-5 text-primary" />
                            <div>
                                <Label className="text-base font-semibold">Configuración de Búsqueda</Label>
                                <p className="text-xs text-muted-foreground">
                                    Personaliza cómo aparece la búsqueda en el inicio
                                </p>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label className="text-sm font-medium">Mostrar Tarjeta de Búsqueda</Label>
                                    <p className="text-xs text-muted-foreground">Muestra el acceso directo en "Funciones"</p>
                                </div>
                                <Switch
                                    checked={showSearchCard}
                                    onCheckedChange={setShowSearchCard}
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label className="text-sm font-medium">Mostrar Barra de Búsqueda</Label>
                                    <p className="text-xs text-muted-foreground">Muestra una barra directamente en el inicio</p>
                                </div>
                                <Switch id="show-search-bar" checked={showSearchBar} onCheckedChange={setShowSearchBar} />
                            </div>
                        </div>
                    </Card>

                    <Separator className="bg-primary/10" />

                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Palette className="w-5 h-5 text-primary" />
                            <h3 className="text-lg font-semibold">Visibilidad de Tarjetas</h3>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                <div className="flex items-center gap-3">
                                    <Heart className="w-5 h-5 text-primary" />
                                    <Label htmlFor="show-donate-card" className="font-medium">Mostrar Tarjeta de Donar</Label>
                                </div>
                                <Switch id="show-donate-card" checked={showDonateCard} onCheckedChange={setShowDonateCard} />
                            </div>

                            <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                <div className="flex items-center gap-3">
                                    <HelpCircle className="w-5 h-5 text-primary" />
                                    <Label htmlFor="show-help-card" className="font-medium">Mostrar Tarjeta de Ayuda</Label>
                                </div>
                                <Switch id="show-help-card" checked={showHelpCard} onCheckedChange={setShowHelpCard} />
                            </div>

                            <div className="flex items-center justify-between p-3 bg-card border border-border rounded-xl">
                                <div className="flex items-center gap-3">
                                    <Palette className="w-5 h-5 text-primary" />
                                    <Label htmlFor="show-settings-in-menu" className="font-medium">Shortcut de Apariencia en Menú</Label>
                                </div>
                                <Switch id="show-settings-in-menu" checked={showSettingsInMenu} onCheckedChange={setShowSettingsInMenu} />
                            </div>
                        </div>
                    </div>

                    {editTarget !== "personal" && (
                        <div className="sticky bottom-6 z-50 px-2 pb-2">
                            <Button
                                className="w-full h-14 rounded-2xl text-lg font-bold shadow-2xl shadow-primary/40 border-2 border-primary/50 relative overflow-hidden group"
                                onClick={handleSaveLevel}
                                disabled={isSaving}
                            >
                                <div className="absolute inset-0 bg-primary/20 group-hover:bg-primary/30 transition-colors" />
                                <span className="relative flex items-center justify-center gap-2">
                                    {isSaving ? "Guardando..." : `Guardar para ${editTarget === 'global' ? 'Todos' : editTarget.toUpperCase()}`}
                                    <Save className="w-6 h-6" />
                                </span>
                            </Button>
                        </div>
                    )}

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
