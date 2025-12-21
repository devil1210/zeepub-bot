// Telegram Web App utilities
export function getTelegramWebApp() {
  if (typeof window === "undefined") return null
  return (window as any).Telegram?.WebApp
}

export function initTelegramWebApp() {
  const webApp = getTelegramWebApp()
  if (!webApp) return null

  // Expand to full height
  webApp.expand()

  // requestFullscreen is available in newer versions of Telegram API
  if (webApp.requestFullscreen) {
    try {
      webApp.requestFullscreen()
    } catch (e) {
      console.log("requestFullscreen not supported or failed", e)
    }
  }

  // Disable vertical swipes to prevent accidental dismissal
  if (webApp.isVerticalSwipesEnabled) {
    webApp.disableVerticalSwipes()
  }

  // Set header color to match theme
  webApp.setHeaderColor("#1C2733")

  return webApp
}

export function getTelegramUser() {
  const webApp = getTelegramWebApp()
  return webApp?.initDataUnsafe?.user || null
}

export function closeTelegramWebApp() {
  const webApp = getTelegramWebApp()
  webApp?.close()
}

export function getTelegramInitData() {
  const webApp = getTelegramWebApp()
  return webApp?.initData || ""
}
