"use client"

import { useEffect, useState } from "react"
import { getTelegramUser, initTelegramWebApp } from "@/lib/telegram"

export function useTelegram() {
  const [webApp, setWebApp] = useState<any>(null)
  const [user, setUser] = useState<any>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const app = initTelegramWebApp()
    if (app) {
      setWebApp(app)
      setUser(getTelegramUser())
      setIsReady(true)

      // Set ready when the app is loaded
      app.ready()
    }
  }, [])

  return { webApp, user, isReady }
}
