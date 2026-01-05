"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

interface ThemeContextType {
  isDarkMode: boolean
  setIsDarkMode: (val: boolean) => void
  primaryColor: string
  setPrimaryColor: (val: string) => void
  uiScale: number
  setUiScale: (val: number) => void
  avatarScale: number
  setAvatarScale: (val: number) => void
  showSearchCard: boolean
  setShowSearchCard: (show: boolean) => void
  showSearchBar: boolean
  setShowSearchBar: (show: boolean) => void
  showDonateCard: boolean
  setShowDonateCard: (show: boolean) => void
  showHelpCard: boolean
  setShowHelpCard: (show: boolean) => void
  showSettingsInMenu: boolean
  setShowSettingsInMenu: (show: boolean) => void
  saveGlobalSettings: (role: string) => Promise<void>
  applySettings: (settings: any, persistToLocal?: boolean) => void
}

const ThemeContext = createContext<ThemeContextType>({
  isDarkMode: true,
  setIsDarkMode: () => { },
  primaryColor: "#3b82f6",
  setPrimaryColor: () => { },
  uiScale: 1,
  setUiScale: () => { },
  avatarScale: 1,
  setAvatarScale: () => { },
  showSearchCard: true,
  setShowSearchCard: () => { },
  showSearchBar: false,
  setShowSearchBar: () => { },
  showDonateCard: true,
  setShowDonateCard: () => { },
  showHelpCard: true,
  setShowHelpCard: () => { },
  showSettingsInMenu: false,
  setShowSettingsInMenu: () => { },
  saveGlobalSettings: async () => { },
  applySettings: () => { },
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
  const [avatarScale, setAvatarScale] = useState(1)
  const [showSearchCard, setShowSearchCard] = useState(true)
  const [showSearchBar, setShowSearchBar] = useState(false)
  const [showDonateCard, setShowDonateCard] = useState(true)
  const [showHelpCard, setShowHelpCard] = useState(true)
  const [showSettingsInMenu, setShowSettingsInMenu] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const [shouldPersist, setShouldPersist] = useState(true)
  const [isResetting, setIsResetting] = useState(false)

  // Load saved settings from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    const savedTheme = localStorage.getItem("theme")
    const savedColor = localStorage.getItem("primaryColor")
    const savedScale = localStorage.getItem("uiScale")
    const savedAvatarScale = localStorage.getItem("avatarScale")
    const savedShowSearchCard = localStorage.getItem("showSearchCard")
    const savedShowSearchBar = localStorage.getItem("showSearchBar")
    const savedShowDonateCard = localStorage.getItem("showDonateCard")
    const savedShowHelpCard = localStorage.getItem("showHelpCard")
    const savedShowSettingsInMenu = localStorage.getItem("showSettingsInMenu")

    // Sync with Backend (Role Defaults)
    const fetchRemoteDefaults = async () => {
      try {
        const { callBotAPI } = await import("@/lib/api")
        const data = await callBotAPI("ui_settings", { subAction: "get", role: "auto" })
        if (data) {
          // Only apply remote defaults for keys NOT present in localStorage
          if (data.primaryColor && !savedColor) setPrimaryColor(data.primaryColor)
          if (data.uiScale !== undefined && !savedScale) setUiScale(data.uiScale)
          if (data.avatarScale !== undefined && !savedAvatarScale) setAvatarScale(data.avatarScale)
          if (data.isDarkMode !== undefined && !savedTheme) setIsDarkMode(data.isDarkMode)
          if (data.showSearchCard !== undefined && !savedShowSearchCard) setShowSearchCard(data.showSearchCard)
          if (data.showSearchBar !== undefined && !savedShowSearchBar) setShowSearchBar(data.showSearchBar)
          if (data.showDonateCard !== undefined && !savedShowDonateCard) setShowDonateCard(data.showDonateCard)
          if (data.showHelpCard !== undefined && !savedShowHelpCard) setShowHelpCard(data.showHelpCard)
          if (data.showSettingsInMenu !== undefined && !savedShowSettingsInMenu) setShowSettingsInMenu(data.showSettingsInMenu)
        }
      } catch (error) {
        console.error("Error fetching UI defaults:", error)
      } finally {
        // ALWAYS mark as loaded even if fetch fails
        setIsLoaded(true)
      }
    }

    // Apply local settings if they exist
    if (savedTheme) setIsDarkMode(savedTheme === "dark")
    if (savedColor) setPrimaryColor(savedColor)
    if (savedScale) setUiScale(parseFloat(savedScale))
    if (savedAvatarScale) setAvatarScale(parseFloat(savedAvatarScale))
    if (savedShowSearchCard !== null) setShowSearchCard(savedShowSearchCard === "true")
    if (savedShowSearchBar !== null) setShowSearchBar(savedShowSearchBar === "true")
    if (savedShowDonateCard !== null) setShowDonateCard(savedShowDonateCard === "true")
    if (savedShowHelpCard !== null) setShowHelpCard(savedShowHelpCard === "true")
    if (savedShowSettingsInMenu !== null) setShowSettingsInMenu(savedShowSettingsInMenu === "true")

    // Then fetch remote defaults for missing ones
    fetchRemoteDefaults()
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
    if (shouldPersist) {
      localStorage.setItem("theme", isDarkMode ? "dark" : "light")
    }
  }, [isDarkMode, isLoaded, shouldPersist])

  // Apply primary color as CSS variables - use hex directly for accuracy
  useEffect(() => {
    if (!isLoaded) return

    // Find the correct color variant based on mode
    const selectedPreset = colorPresets.find(
      (c) => c.value === primaryColor || c.dark === primaryColor
    )
    const colorToUse = isDarkMode
      ? (selectedPreset?.dark || primaryColor)
      : (selectedPreset?.value || primaryColor)

    // Calculate if color is light or dark to set contrasting text
    const getContrastColor = (hex: string): string => {
      const cleanHex = hex.replace('#', '')
      const r = parseInt(cleanHex.substring(0, 2), 16)
      const g = parseInt(cleanHex.substring(2, 4), 16)
      const b = parseInt(cleanHex.substring(4, 6), 16)
      // Calculate relative luminance
      const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
      return luminance > 0.5 ? '#000000' : '#ffffff'
    }

    const contrastColor = getContrastColor(colorToUse)

    // Create or update dynamic style tag - use hex directly for accurate colors
    let styleTag = document.getElementById("dynamic-theme-colors")
    if (!styleTag) {
      styleTag = document.createElement("style")
      styleTag.id = "dynamic-theme-colors"
      document.head.appendChild(styleTag)
    }

    // Apply primary color and contrasting text color
    styleTag.textContent = `
      :root {
        --primary: ${colorToUse} !important;
        --primary-foreground: ${contrastColor} !important;
        --ring: ${colorToUse} !important;
        --accent: ${colorToUse} !important;
        --accent-foreground: ${contrastColor} !important;
      }
      .dark {
        --primary: ${colorToUse} !important;
        --primary-foreground: ${contrastColor} !important;
        --ring: ${colorToUse} !important;
        --accent: ${colorToUse} !important;
        --accent-foreground: ${contrastColor} !important;
      }
      /* Ensure button and link colors use the primary with contrast text */
      .bg-primary { background-color: ${colorToUse} !important; color: ${contrastColor} !important; }
      .text-primary { color: ${colorToUse} !important; }
      .border-primary { border-color: ${colorToUse} !important; }
    `

    if (shouldPersist) {
      localStorage.setItem("primaryColor", primaryColor)
    }
  }, [primaryColor, isDarkMode, isLoaded, shouldPersist])

  // Apply UI scale
  useEffect(() => {
    if (!isLoaded) return

    document.documentElement.style.setProperty("--font-scale", uiScale.toString())
    document.documentElement.style.fontSize = `${uiScale * 100}%`
    if (shouldPersist) {
      localStorage.setItem("uiScale", uiScale.toString())
    }
  }, [uiScale, isLoaded, shouldPersist])

  // Save avatar scale
  useEffect(() => {
    if (!isLoaded) return
    if (shouldPersist) {
      localStorage.setItem("avatarScale", avatarScale.toString())
    }
  }, [avatarScale, isLoaded, shouldPersist])

  // Save visibility preferences
  useEffect(() => {
    if (!isLoaded) return
    if (shouldPersist) {
      localStorage.setItem("showSearchCard", String(showSearchCard))
    }
  }, [showSearchCard, isLoaded, shouldPersist])

  useEffect(() => {
    if (!isLoaded) return
    if (shouldPersist) {
      localStorage.setItem("showSearchBar", String(showSearchBar))
    }
  }, [showSearchBar, isLoaded, shouldPersist])

  useEffect(() => {
    if (!isLoaded) return
    if (shouldPersist) {
      localStorage.setItem("showDonateCard", String(showDonateCard))
    }
  }, [showDonateCard, isLoaded, shouldPersist])

  useEffect(() => {
    if (!isLoaded) return
    if (shouldPersist) {
      localStorage.setItem("showHelpCard", String(showHelpCard))
    }
  }, [showHelpCard, isLoaded, shouldPersist])

  useEffect(() => {
    if (!isLoaded) return
    if (shouldPersist) {
      localStorage.setItem("showSettingsInMenu", String(showSettingsInMenu))
    }
  }, [showSettingsInMenu, isLoaded, shouldPersist])

  const saveGlobalSettings = async (role: string) => {
    try {
      const { callBotAPI } = await import("@/lib/api")
      const settings = {
        primaryColor,
        uiScale,
        avatarScale,
        isDarkMode,
        showSearchCard,
        showSearchBar,
        showDonateCard,
        showHelpCard,
        showSettingsInMenu
      }
      await callBotAPI("ui_settings", { subAction: "set", role, settings })
    } catch (error) {
      console.error("Error saving global settings:", error)
      throw error
    }
  }

  const applySettings = (settings: any, persistToLocal: boolean = true) => {
    // Disable persistence temporarily if requested (e.g. previewing level settings)
    setShouldPersist(persistToLocal)

    if (settings.isDarkMode !== undefined) setIsDarkMode(settings.isDarkMode)
    if (settings.primaryColor !== undefined) setPrimaryColor(settings.primaryColor)
    if (settings.uiScale !== undefined) setUiScale(settings.uiScale)
    if (settings.avatarScale !== undefined) setAvatarScale(settings.avatarScale)
    if (settings.showSearchCard !== undefined) setShowSearchCard(settings.showSearchCard)
    if (settings.showSearchBar !== undefined) setShowSearchBar(settings.showSearchBar)
    if (settings.showDonateCard !== undefined) setShowDonateCard(settings.showDonateCard)
    if (settings.showHelpCard !== undefined) setShowHelpCard(settings.showHelpCard)
    if (settings.showSettingsInMenu !== undefined) setShowSettingsInMenu(settings.showSettingsInMenu)

    // If we are restoring personal settings, ensure we force a save to localStorage of what we just applied
    if (persistToLocal) {
      localStorage.setItem("theme", settings.isDarkMode ? "dark" : "light")
      localStorage.setItem("primaryColor", settings.primaryColor || "#3b82f6")
      localStorage.setItem("uiScale", (settings.uiScale || 1).toString())
      localStorage.setItem("avatarScale", (settings.avatarScale || 1).toString())
      localStorage.setItem("showSearchCard", String(settings.showSearchCard ?? true))
      localStorage.setItem("showSearchBar", String(settings.showSearchBar ?? false))
      localStorage.setItem("showDonateCard", String(settings.showDonateCard ?? true))
      localStorage.setItem("showHelpCard", String(settings.showHelpCard ?? true))
      localStorage.setItem("showSettingsInMenu", String(settings.showSettingsInMenu ?? false))
    }
  }

  return (
    <ThemeContext.Provider
      value={{
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
      }}
    >
      {children}
    </ThemeContext.Provider>
  )
}
