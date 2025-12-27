"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useTelegram } from "@/hooks/use-telegram"
import { checkAccess } from "@/lib/api"
import { useRouter, usePathname } from "next/navigation"

interface TelegramContextType {
  webApp: any
  user: any
  isReady: boolean
  hasAccess: boolean | null
  isAdmin: boolean | null
  isAdminMode: boolean
  setIsAdminMode: (val: boolean) => void
  publishTarget: string
  setPublishTarget: (val: string) => void
}

const TelegramContext = createContext<TelegramContextType>({
  webApp: null,
  user: null,
  isReady: false,
  hasAccess: null,
  isAdmin: null,
  isAdminMode: false,
  setIsAdminMode: () => { },
  publishTarget: "private",
  setPublishTarget: () => { },
})

export function TelegramProvider({ children }: { children: ReactNode }) {
  const telegram = useTelegram()

  // Cache expiration time: 5 minutes
  const CACHE_TTL = 5 * 60 * 1000 // 5 minutes in milliseconds

  const [hasAccess, setHasAccess] = useState<boolean | null>(() => {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('access_status')
      if (cached) {
        const data = JSON.parse(cached)
        const now = Date.now()
        // Check if cache has expired
        if (data.timestamp && (now - data.timestamp) < CACHE_TTL) {
          return data.hasAccess
        }
      }
    }
    return null
  })

  const [isAdmin, setIsAdmin] = useState<boolean | null>(() => {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('access_status')
      if (cached) {
        const data = JSON.parse(cached)
        const now = Date.now()
        // Check if cache has expired
        if (data.timestamp && (now - data.timestamp) < CACHE_TTL) {
          return data.isAdmin
        }
      }
    }
    return null
  })

  const [isAdminMode, setIsAdminMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('admin_mode') === 'true'
    }
    return false
  })

  const [publishTarget, setPublishTarget] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('publish_target') || 'private'
    }
    return 'private'
  })

  const router = useRouter()
  const pathname = usePathname()

  const toggleAdminMode = (val: boolean) => {
    setIsAdminMode(val)
    localStorage.setItem('admin_mode', val.toString())
  }

  const togglePublishTarget = (val: string) => {
    setPublishTarget(val)
    localStorage.setItem('publish_target', val)
  }

  // Configurar botón de retroceso nativo de Telegram
  useEffect(() => {
    if (telegram.webApp && telegram.isReady) {
      const webApp = telegram.webApp

      // Configurar el handler del botón de retroceso
      const handleBackButton = () => {
        router.back()
      }

      // Mostrar u ocultar el botón según la ruta
      if (pathname === '/') {
        // Ocultar en la página principal
        webApp.BackButton.hide()
      } else {
        // Mostrar en páginas secundarias
        webApp.BackButton.show()
      }

      // Configurar el evento click
      webApp.BackButton.onClick(handleBackButton)

      // Cleanup: remover el listener al desmontar
      return () => {
        webApp.BackButton.offClick(handleBackButton)
      }
    }
  }, [telegram.webApp, telegram.isReady, pathname, router])

  useEffect(() => {
    async function verify() {
      if (telegram.isReady && telegram.user) {
        // Check if we should use cached data or fetch fresh
        let shouldFetch = true

        if (typeof window !== 'undefined') {
          const cached = localStorage.getItem('access_status')
          if (cached) {
            const data = JSON.parse(cached)
            const now = Date.now()
            // If cache is still valid, don't fetch
            if (data.timestamp && (now - data.timestamp) < CACHE_TTL) {
              shouldFetch = false
            }
          }
        }

        if (shouldFetch) {
          try {
            const result = await checkAccess(telegram.user.id)
            const accessValue = result.hasAccess || result.isAdmin

            setHasAccess(accessValue)
            setIsAdmin(result.isAdmin)

            localStorage.setItem('access_status', JSON.stringify({
              hasAccess: accessValue,
              isAdmin: result.isAdmin,
              timestamp: Date.now()
            }))

            if (!accessValue && pathname !== "/no-access") {
              router.push("/no-access")
            }
          } catch (error) {
            console.error("Failed to check access:", error)
            if (pathname !== "/no-access" && hasAccess === null) {
              router.push("/no-access")
            }
          }
        }
      }
    }

    verify()
  }, [telegram.isReady, telegram.user, pathname, router])

  // Security: If user is strictly NOT admin, force admin mode off
  useEffect(() => {
    if (isAdmin === false && isAdminMode) {
      setIsAdminMode(false)
      if (typeof window !== 'undefined') {
        localStorage.setItem('admin_mode', 'false')
      }
    }
  }, [isAdmin, isAdminMode])

  const value = {
    ...telegram,
    hasAccess,
    isAdmin,
    isAdminMode,
    setIsAdminMode: toggleAdminMode,
    publishTarget,
    setPublishTarget: togglePublishTarget
  }

  return <TelegramContext.Provider value={value}>{children}</TelegramContext.Provider>
}

export function useTelegramContext() {
  return useContext(TelegramContext)
}
