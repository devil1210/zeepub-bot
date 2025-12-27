// Telegram Web App utilities
export function getTelegramWebApp() {
  if (typeof window === "undefined") return null
  return (window as any).Telegram?.WebApp
}

export function initTelegramWebApp() {
  const webApp = getTelegramWebApp()
  if (!webApp) return null

  // Expand to full height (occupy all vertical space in standard view)
  webApp.expand()

  // New Fullscreen API (if available) - standardizes the experience across platforms
  try {
    if (typeof webApp.requestFullscreen === 'function') {
      webApp.requestFullscreen()
    }
  } catch (e) {
    console.warn("Fullscreen request failed", e)
  }

  // Optimize for full-screen experience
  if (typeof webApp.disableVerticalSwipes === 'function') {
    webApp.disableVerticalSwipes() // Prevent accidental closing when swiping down
  }

  // Set header color to match theme
  webApp.setHeaderColor("#1a1a1a") // Match your dark theme
  webApp.setBackgroundColor("#000000")

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
