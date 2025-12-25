"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Sun, Moon, Palette } from "lucide-react"
import { AccessGuard } from "@/components/access-guard"
import { TransparentHeader } from "@/components/transparent-header"

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

    // Aplicar tema - forzar recarga de estilos
    useEffect(() => {
        const html = document.documentElement

        // Remover y agregar la clase para forzar actualización
        html.classList.remove("dark", "light")

        if (isDarkMode) {
            html.classList.add("dark")
            html.setAttribute("data-theme", "dark")
        } else {
            html.classList.add("light")
            html.setAttribute("data-theme", "light")
        }

        localStorage.setItem("ui-theme", isDarkMode ? "dark" : "light")
    }, [isDarkMode])

    // Aplicar escala de UI
    useEffect(() => {
        const html = document.documentElement
        html.style.setProperty("--font-scale", uiScale.toString())
        html.style.setProperty("--spacing-scale", uiScale.toString())
        localStorage.setItem("ui-scale", uiScale.toString())
    }, [uiScale])

    // Aplicar color principal - convertir hex a OKLCH
    useEffect(() => {
        const html = document.documentElement
        const selectedPreset = colorPresets.find(
            (c) => c.value === primaryColor || c.dark === primaryColor
        )
        const lightColor = selectedPreset?.value || primaryColor
        const darkColor = selectedPreset?.dark || primaryColor

        // Aplicar color según el modo
        const colorToUse = isDarkMode ? darkColor : lightColor

        // Convertir hex a OKLCH
        const hexToOklch = (hex: string): string => {
            // Remove # if present
            hex = hex.replace('#', '')

            // Parse RGB
            const r = parseInt(hex.substring(0, 2), 16) / 255
            const g = parseInt(hex.substring(2, 4), 16) / 255
            const b = parseInt(hex.substring(4, 6), 16) / 255

            // Convert RGB to linear RGB
            const toLinear = (c: number) => {
                return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
            }

            const rL = toLinear(r)
            const gL = toLinear(g)
            const bL = toLinear(b)

            // Convert to XYZ (D65 illuminant)
            const x = 0.4124564 * rL + 0.3575761 * gL + 0.1804375 * bL
            const y = 0.2126729 * rL + 0.7151522 * gL + 0.0721750 * bL
            const z = 0.0193339 * rL + 0.1191920 * gL + 0.9503041 * bL

            // Convert to Lab
            const xn = 0.95047
            const yn = 1.00000
            const zn = 1.08883

            const fx = x / xn > 0.008856 ? Math.pow(x / xn, 1 / 3) : (903.3 * x / xn + 16) / 116
            const fy = y / yn > 0.008856 ? Math.pow(y / yn, 1 / 3) : (903.3 * y / yn + 16) / 116
            const fz = z / zn > 0.008856 ? Math.pow(z / zn, 1 / 3) : (903.3 * z / zn + 16) / 116

            const L = 116 * fy - 16
            const a = 500 * (fx - fy)
            const bVal = 200 * (fy - fz)

            // Convert Lab to LCH
            const C = Math.sqrt(a * a + bVal * bVal)
            let H = Math.atan2(bVal, a) * 180 / Math.PI
            if (H < 0) H += 360

            // Approximate OKLCH (simplified conversion)
            const l = L / 100
            const c = C / 150
            const h = H

            return `${l.toFixed(3)} ${c.toFixed(3)} ${h.toFixed(1)}`
        }

        // Crear un style tag dinámico para inyectar los colores
        let styleTag = document.getElementById("dynamic-theme-colors")
        if (!styleTag) {
            styleTag = document.createElement("style")
            styleTag.id = "dynamic-theme-colors"
            document.head.appendChild(styleTag)
        }

        const oklchValue = hexToOklch(colorToUse)

        // Inyectar CSS con valores OKLCH
        styleTag.textContent = `
      :root {
        --primary: oklch(${oklchValue}) !important;
        --ring: oklch(${oklchValue}) !important;
        --accent: oklch(${oklchValue}) !important;
      }
      .dark {
        --primary: oklch(${oklchValue}) !important;
        --ring: oklch(${oklchValue}) !important;
        --accent: oklch(${oklchValue}) !important;
      }
    `

        localStorage.setItem("ui-primary-color", colorToUse)
    }, [primaryColor, isDarkMode])

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
