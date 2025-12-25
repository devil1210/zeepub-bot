"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

interface ThemeContextType {
  isDarkMode: boolean
  setIsDarkMode: (val: boolean) => void
  primaryColor: string
  setPrimaryColor: (val: string) => void
  uiScale: number
  setUiScale: (val: number) => void
}

const ThemeContext = createContext<ThemeContextType>({
  isDarkMode: true,
  setIsDarkMode: () => { },
  primaryColor: "#3b82f6",
  setPrimaryColor: () => { },
  uiScale: 1,
  setUiScale: () => { },
})

export function useTheme() {
  return useContext(ThemeContext)
}

// Color presets matching interface-config
const colorPresets = [
  { name: "Azul", value: "#3b82f6", dark: "#60a5fa" },
  { name: "Verde", value: "#22c55e", dark: "#4ade80" },
  { name: "Morado", value: "#a855f7", dark: "#c084fc" },
  { name: "Rosa", value: "#ec4899", dark: "#f472b6" },
  { name: "Naranja", value: "#f97316", dark: "#fb923c" },
  { name: "Rojo", value: "#ef4444", dark: "#f87171" },
  { name: "Cyan", value: "#06b6d4", dark: "#22d3ee" },
]

// Convert hex to OKLCH for Tailwind compatibility
function hexToOklch(hex: string): string {
  hex = hex.replace('#', '')

  const r = parseInt(hex.substring(0, 2), 16) / 255
  const g = parseInt(hex.substring(2, 4), 16) / 255
  const b = parseInt(hex.substring(4, 6), 16) / 255

  const toLinear = (c: number) => {
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  }

  const rL = toLinear(r)
  const gL = toLinear(g)
  const bL = toLinear(b)

  const x = 0.4124564 * rL + 0.3575761 * gL + 0.1804375 * bL
  const y = 0.2126729 * rL + 0.7151522 * gL + 0.0721750 * bL
  const z = 0.0193339 * rL + 0.1191920 * gL + 0.9503041 * bL

  const xn = 0.95047
  const yn = 1.00000
  const zn = 1.08883

  const fx = x / xn > 0.008856 ? Math.pow(x / xn, 1 / 3) : (903.3 * x / xn + 16) / 116
  const fy = y / yn > 0.008856 ? Math.pow(y / yn, 1 / 3) : (903.3 * y / yn + 16) / 116
  const fz = z / zn > 0.008856 ? Math.pow(z / zn, 1 / 3) : (903.3 * z / zn + 16) / 116

  const L = 116 * fy - 16
  const a = 500 * (fx - fy)
  const bVal = 200 * (fy - fz)

  const C = Math.sqrt(a * a + bVal * bVal)
  let H = Math.atan2(bVal, a) * 180 / Math.PI
  if (H < 0) H += 360

  const l = L / 100
  const c = C / 150

  return `${l.toFixed(3)} ${c.toFixed(3)} ${H.toFixed(1)}`
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [primaryColor, setPrimaryColor] = useState("#3b82f6")
  const [uiScale, setUiScale] = useState(1)
  const [isLoaded, setIsLoaded] = useState(false)

  // Load saved settings from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    const savedTheme = localStorage.getItem("ui-theme")
    const savedColor = localStorage.getItem("ui-primary-color")
    const savedScale = localStorage.getItem("ui-scale")

    if (savedTheme) {
      setIsDarkMode(savedTheme === "dark")
    }
    if (savedColor) {
      setPrimaryColor(savedColor)
    }
    if (savedScale) {
      setUiScale(parseFloat(savedScale))
    }

    setIsLoaded(true)
  }, [])

  // Apply dark mode class to html element
  useEffect(() => {
    if (!isLoaded) return

    const html = document.documentElement
    if (isDarkMode) {
      html.classList.add("dark")
    } else {
      html.classList.remove("dark")
    }
    localStorage.setItem("ui-theme", isDarkMode ? "dark" : "light")
  }, [isDarkMode, isLoaded])

  // Apply primary color as CSS variables
  useEffect(() => {
    if (!isLoaded) return

    // Find the correct color variant based on mode
    const selectedPreset = colorPresets.find(
      (c) => c.value === primaryColor || c.dark === primaryColor
    )
    const colorToUse = isDarkMode
      ? (selectedPreset?.dark || primaryColor)
      : (selectedPreset?.value || primaryColor)

    // Create or update dynamic style tag
    let styleTag = document.getElementById("dynamic-theme-colors")
    if (!styleTag) {
      styleTag = document.createElement("style")
      styleTag.id = "dynamic-theme-colors"
      document.head.appendChild(styleTag)
    }

    const oklchValue = hexToOklch(colorToUse)

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
  }, [primaryColor, isDarkMode, isLoaded])

  // Apply UI scale
  useEffect(() => {
    if (!isLoaded) return

    document.documentElement.style.setProperty("--font-scale", uiScale.toString())
    document.documentElement.style.fontSize = `${uiScale * 100}%`
    localStorage.setItem("ui-scale", uiScale.toString())
  }, [uiScale, isLoaded])

  return (
    <ThemeContext.Provider
      value={{
        isDarkMode,
        setIsDarkMode,
        primaryColor,
        setPrimaryColor,
        uiScale,
        setUiScale,
      }}
    >
      {children}
    </ThemeContext.Provider>
  )
}
