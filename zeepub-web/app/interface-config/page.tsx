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
import { useState } from "react"

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
    } = useTheme()
    const { t } = useStrings()
    const { isAdmin } = useTelegramContext()
    const [targetRole, setTargetRole] = useState("global")
    const [isSaving, setIsSaving] = useState(false)

    const handleSaveGlobal = async () => {
        setIsSaving(true)
        try {
            await saveGlobalSettings(targetRole)
            toast.success(`Configuración guardada para: ${targetRole} `)
        } catch (error) {
            toast.error("Error al guardar la configuración global")
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <AccessGuard>
            <div className="min-h-screen bg-background pt-safe">
                <TransparentHeader />

                <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
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
                                            // Allow partial input while typing
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
                                <div
                                    className="rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center transition-all"
                                    style={{
                                        width: `${80 * avatarScale}px`,
                                        height: `${80 * avatarScale}px`
                                    }}
                                >
                                    <span className="text-primary font-bold" style={{ fontSize: `${24 * avatarScale}px` }}>
                                        Z
                                    </span>
                                </div>
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

                    {isAdmin && (
                        <>
                            <Separator className="bg-primary/10" />
                            <div className="space-y-4 p-4 border-2 border-primary/20 rounded-2xl bg-primary/5">
                                <div className="flex items-center gap-2 mb-2">
                                    <Globe className="w-5 h-5 text-primary" />
                                    <h3 className="text-lg font-bold">Configuración Global (Admin)</h3>
                                </div>

                                <p className="text-xs text-muted-foreground mb-4">
                                    Como administrador, puedes guardar la configuración actual como predeterminada para todos los usuarios o para roles específicos.
                                </p>

                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-medium">Aplicar a:</Label>
                                        <Select value={targetRole} onValueChange={setTargetRole}>
                                            <SelectTrigger className="w-full bg-card">
                                                <SelectValue placeholder="Selecciona un rol" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="global">Todos (Global)</SelectItem>
                                                <SelectItem value="admin">Administradores</SelectItem>
                                                <SelectItem value="staff">Staff</SelectItem>
                                                <SelectItem value="premium">Premium</SelectItem>
                                                <SelectItem value="vip">VIP</SelectItem>
                                                <SelectItem value="free">Lector (Free)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <Button
                                        className="w-full h-12 rounded-xl text-md font-bold"
                                        onClick={handleSaveGlobal}
                                        disabled={isSaving}
                                    >
                                        {isSaving ? "Guardando..." : "Guardar como Prefijado"}
                                        <Save className="ml-2 w-5 h-5" />
                                    </Button>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Información */}
                    <Card className="p-4 border-border bg-primary/5">
                        <p className="text-xs text-muted-foreground text-center">
                            Las configuraciones se guardan automáticamente y se aplicarán en toda la aplicación
                        </p>
                    </Card>
                </div>
            </div>
        </AccessGuard>
    )
}
