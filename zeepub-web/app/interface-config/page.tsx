"use client"

import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Sun, Moon, Palette } from "lucide-react"
import { AccessGuard } from "@/components/access-guard"
import { TransparentHeader } from "@/components/transparent-header"
import { useTheme } from "@/components/theme-provider"

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
    const { isDarkMode, setIsDarkMode, primaryColor, setPrimaryColor, uiScale, setUiScale, avatarScale, setAvatarScale } = useTheme()

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
                        <div className="mt-4 flex items-center gap-3">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="color"
                                    value={primaryColor}
                                    onChange={(e) => setPrimaryColor(e.target.value)}
                                    className="w-12 h-12 rounded-lg border-2 border-border cursor-pointer bg-transparent"
                                    style={{ padding: 0 }}
                                />
                                <span className="text-sm text-muted-foreground">Color personalizado</span>
                            </label>
                            <span className="text-xs font-mono text-muted-foreground bg-secondary px-2 py-1 rounded">
                                {primaryColor.toUpperCase()}
                            </span>
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
