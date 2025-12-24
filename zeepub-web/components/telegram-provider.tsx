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
}

const TelegramContext = createContext<TelegramContextType>({
  webApp: null,
  user: null,
  isReady: false,
  hasAccess: null,
  isAdmin: null,
})

export function TelegramProvider({ children }: { children: ReactNode }) {
  const telegram = useTelegram()
  const [hasAccess, setHasAccess] = useState<boolean | null>(null)
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    async function verify() {
      if (telegram.isReady && telegram.user) {
        try {
          const result = await checkAccess(telegram.user.id)
          const accessValue = result.hasAccess || result.isAdmin
          setHasAccess(accessValue)
          setIsAdmin(result.isAdmin)

          if (!accessValue && pathname !== "/no-access") {
            console.log("[AccessControl] Denied, redirecting to /no-access")
            router.push("/no-access")
          } else if (accessValue && pathname === "/no-access") {
            router.push("/")
          }
        } catch (error) {
          console.error("Failed to check access:", error)
          // Si falla la API de acceso, por seguridad denegamos si no estamos ya en la página de error
          if (pathname !== "/no-access") {
            router.push("/no-access")
          }
        }
      }
    }

    verify()
  }, [telegram.isReady, telegram.user, pathname, router])

  const value = {
    ...telegram,
    hasAccess,
    isAdmin
  }

  return <TelegramContext.Provider value={value}>{children}</TelegramContext.Provider>
}

export function useTelegramContext() {
  return useContext(TelegramContext)
}
