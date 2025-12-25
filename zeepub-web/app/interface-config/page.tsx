"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Sun, Moon, Palette } from "lucide-react"
import { AccessGuard } from "@/components/access-guard"

// Paleta de colores predefinidos
const colorPresets = [
    { name: "Azul", value: "#3b82f6", dark: "#60a5fa" },
    { name: "Verde", value: "#10b981", dark: "#34d399" },
    { name: "Púrpura", value: "#8b5cf6", dark: "#a78bfa" },
    { name: "Rosa", value: "#ec4899", dark: "#f472b6" },
    { name: "Naranja", value: "#f59e0b", dark: "#fbbf24" },
    { name: "Rojo", value: "#ef4444", dark: "#f87171" },
]

export default function InterfaceConfigPage() {
    const [isDarkMode, setIsDarkMode] = useState(true)
    const [uiScale, setUiScale] = useState(1.0)
    const [primaryColor, setPrimaryColor] = useState("#3b82f6")

    // Cargar configuración guardada
    useEffect(() => {
        const savedTheme = localStorage.getItem("ui-theme")
        const savedScale = localStorage.getItem("ui-scale")
        const savedColor = localStorage.getItem("ui-primary-color")

        if (savedTheme) setIsDarkMode(savedTheme === "dark")
        if (savedScale) setUiScale(parseFloat(savedScale))
        if (savedColor) setPrimaryColor(savedColor)
    }, [])

    // Aplicar tema
    useEffect(() => {
        const root = document.documentElement
        if (isDarkMode) {
            root.classList.add("dark")
        } else {
            root.classList.remove("dark")
        }
        localStorage.setItem("ui-theme", isDarkMode ? "dark" : "light")
    }, [isDarkMode])

    // Aplicar escala de UI
    useEffect(() => {
        const root = document.documentElement
        root.style.setProperty("--font-scale", uiScale.toString())
        root.style.setProperty("--spacing-scale", uiScale.toString())
        localStorage.setItem("ui-scale", uiScale.toString())
    }, [uiScale])

    // Aplicar color principal
    useEffect(() => {
        const root = document.documentElement
        const selectedPreset = colorPresets.find(
            (c) => c.value === primaryColor || c.dark === primaryColor
        )
        const lightColor = selectedPreset?.value || primaryColor
        const darkColor = selectedPreset?.dark || primaryColor

        // Aplicar color según el modo
        const colorToUse = isDarkMode ? darkColor : lightColor
        root.style.setProperty("--primary", colorToUse)
        localStorage.setItem("ui-primary-color", colorToUse)
    }, [primaryColor, isDarkMode])

    return (
        <AccessGuard>
            <div className="min-h-screen bg-background">
                <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
                    <div className="max-w-2xl mx-auto px-4 py-3">
                        <h1 className="text-lg font-semibold text-center">Apariencia</h1>
                    </div>
                </header>

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
                        <div className="mt-3 text-sm text-muted-foreground text-center">
                            {colorPresets.find((c) => c.value === primaryColor || c.dark === primaryColor)?.name || "Personalizado"}
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
